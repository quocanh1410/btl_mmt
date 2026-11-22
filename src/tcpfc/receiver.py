"""Bên nhận TCP: bộ đệm, rwnd, ứng dụng đọc. Chủ sở hữu: P2.

Giả định (ghi vào báo cáo):
- Bộ đệm nhận cố định buffer_size = B byte, chứa cả dữ liệu đúng thứ tự chưa được ứng dụng
  đọc lẫn segment đến sai thứ tự (nếu store_out_of_order = True).
- Chỗ trống = B − (byte đang nằm trong bộ đệm). Segment chỉ được nhận nếu nằm trọn trong
  [rcv_nxt, rcv_nxt + chỗ trống); nếu không thì bị bỏ (bên gửi sẽ gửi lại).
- rwnd quảng bá = chỗ trống, NHƯNG nếu chỗ trống < min(MSS, B/2) thì báo rwnd = 0
  (tránh Silly Window Syndrome phía nhận – RFC 1122 §4.2.3.3, Linux làm tương tự).
  Tắt bằng rx_sws_avoid = False để rwnd = chỗ trống đúng nghĩa đen.
- ACK ngay cho mỗi segment đến (không delayed ACK), ACK tích lũy = rcv_nxt.
- Window probe không mang dữ liệu mới: chỉ được trả lời bằng ACK kèm rwnd hiện tại.
- Ứng dụng đọc định kỳ mỗi app_read_interval giây, mỗi lần tối đa app_read_rate·interval byte
  (phần lẻ byte được cộng dồn sang lần sau). Tùy chọn: ứng dụng ngừng đọc trong khoảng
  [app_pause_at, app_pause_at + app_pause_duration) – mô phỏng ứng dụng bận/treo.
- Window update (như Linux tcp_cleanup_rbuf): sau khi ứng dụng đọc, nếu cửa sổ mới
  ≥ 2 × phần cửa sổ còn lại đã báo cho bên gửi (và > 0) thì chủ động gửi ACK báo cửa sổ mới.
  Trường hợp quan trọng nhất: đã báo rwnd = 0, nay có ≥ 1 MSS chỗ trống -> gửi ngay.
"""

from __future__ import annotations

import math

from .engine import Simulator
from .segment import Ack, Segment


class Receiver:
    def __init__(
        self,
        sim: Simulator,
        channel,
        metrics,
        buffer_size: int,
        app_read_rate: float,
        app_read_interval: float,
        total_bytes: int,
        mss: int,
        store_out_of_order: bool = True,
        sws_avoid: bool = True,
        app_pause_at: float | None = None,
        app_pause_duration: float = 0.0,
    ) -> None:
        self.sim = sim
        self.channel = channel
        self.metrics = metrics
        self.buffer_size = buffer_size
        self.app_read_rate = app_read_rate
        self.app_read_interval = app_read_interval
        self.total_bytes = total_bytes
        self.mss = mss
        self.store_out_of_order = store_out_of_order
        self.sws_avoid = sws_avoid
        self.app_pause_at = app_pause_at
        self.app_pause_duration = app_pause_duration

        self.rcv_nxt = 0               # byte tiếp theo mong đợi
        self.in_order_bytes = 0        # byte đúng thứ tự đang nằm trong buffer chờ ứng dụng đọc
        self.ooo: dict[int, int] = {}  # seq -> length, segment ngoài thứ tự
        self.delivered_bytes = 0       # byte ứng dụng đã đọc
        self._read_credit = 0.0        # phần lẻ byte được phép đọc cộng dồn
        self._was_zero = False
        self._adv_right_edge = buffer_size   # mép phải cửa sổ đã báo gần nhất (rcv_nxt + rwnd)

    # ------------------------------------------------------------------ API
    @property
    def buffered_bytes(self) -> int:
        return self.in_order_bytes + sum(self.ooo.values())

    @property
    def free_space(self) -> int:
        return max(0, self.buffer_size - self.buffered_bytes)

    @property
    def rwnd(self) -> int:
        """Cửa sổ quảng bá trong ACK."""
        free = self.free_space
        if self.sws_avoid and free < min(self.mss, self.buffer_size // 2):
            return 0
        return free

    def start(self) -> None:
        self.sim.schedule(self.app_read_interval, self._app_read)

    def on_segment(self, seg: Segment) -> None:
        if not seg.is_probe and seg.end > self.rcv_nxt:
            self._accept(seg)
        # trùng lặp, probe hoặc bị bỏ: vẫn trả ACK với trạng thái hiện tại
        self._after_buffer_change()
        self._send_ack()

    # ------------------------------------------------------------ nội bộ
    def _accept(self, seg: Segment) -> None:
        start = max(seg.seq, self.rcv_nxt)          # cắt phần đã nhận (nếu chồng lấn)
        new_len = seg.end - start
        right_edge = self.rcv_nxt + self.free_space  # chỗ thực sự còn trống
        if seg.end > right_edge:
            self.metrics.on_event(self.sim.now, "rx_drop_full")
            return
        if start == self.rcv_nxt:
            self.in_order_bytes += new_len
            self.rcv_nxt += new_len
            # ghép các segment ngoài thứ tự đã liền mạch
            while self.rcv_nxt in self.ooo:
                ln = self.ooo.pop(self.rcv_nxt)
                self.in_order_bytes += ln
                self.rcv_nxt += ln
        elif self.store_out_of_order:
            if start not in self.ooo:
                self.ooo[start] = new_len
                self.metrics.on_event(self.sim.now, "rx_out_of_order")
        else:
            self.metrics.on_event(self.sim.now, "rx_drop_out_of_order")

    def _after_buffer_change(self) -> None:
        t = self.sim.now
        rw = self.rwnd
        self.metrics.on_buffer_change(t, self.buffered_bytes, rw)
        if rw == 0 and not self._was_zero:
            self.metrics.on_event(t, "zero_window")
        self._was_zero = rw == 0

    def _send_ack(self, is_window_update: bool = False) -> None:
        rw = self.rwnd
        self._adv_right_edge = self.rcv_nxt + rw
        self.channel.send_to_sender(Ack(self.rcv_nxt, rw, self.sim.now, is_window_update))

    def _advertised_remaining(self) -> int:
        """Phần cửa sổ bên gửi đang tin là còn dùng được (theo lần báo gần nhất)."""
        return max(0, self._adv_right_edge - self.rcv_nxt)

    def _app_paused(self, t: float) -> bool:
        return (self.app_pause_at is not None
                and self.app_pause_at <= t < self.app_pause_at + self.app_pause_duration)

    def _app_read(self) -> None:
        t = self.sim.now
        if self._app_paused(t):
            self.sim.schedule(self.app_read_interval, self._app_read)
            return
        self._read_credit += self.app_read_rate * self.app_read_interval
        n = min(self.in_order_bytes, math.floor(self._read_credit))
        if n > 0:
            self.in_order_bytes -= n
            self.delivered_bytes += n
            self._read_credit -= n
            self.metrics.on_app_read(t, n)
            self._after_buffer_change()
        # Khi đệm rỗng, ứng dụng chờ dữ liệu: không tích lũy quyền đọc quá 1 chu kỳ
        self._read_credit = min(self._read_credit, self.app_read_rate * self.app_read_interval)

        if n > 0:
            new, cur = self.rwnd, self._advertised_remaining()
            if new > 0 and new >= 2 * cur:
                self.metrics.on_event(t, "window_update")
                self._send_ack(is_window_update=True)

        if self.delivered_bytes < self.total_bytes:
            self.sim.schedule(self.app_read_interval, self._app_read)
