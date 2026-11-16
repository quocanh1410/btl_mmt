"""Bên nhận TCP: bộ đệm, rwnd, ứng dụng đọc. Chủ sở hữu: P2.

Giả định cần ghi vào báo cáo:
- Bộ đệm nhận cố định buffer_size byte.
- Segment ngoài thứ tự: (chọn) lưu tạm trong buffer HOẶC bỏ. Ghi rõ lựa chọn.
- Ứng dụng đọc định kỳ mỗi app_read_interval giây, mỗi lần tối đa app_read_rate*interval byte.
- ACK ngay cho mỗi segment (không delayed ACK) – có thể mở rộng.
- Window update chủ động khi rwnd tăng từ < MSS lên >= MSS sau khi ứng dụng đọc.
"""

from __future__ import annotations

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

        self.rcv_nxt = 0               # byte tiếp theo mong đợi
        self.in_order_bytes = 0        # byte đúng thứ tự đang nằm trong buffer chờ ứng dụng đọc
        self.ooo: dict[int, int] = {}  # seq -> length, segment ngoài thứ tự
        self.delivered_bytes = 0       # byte ứng dụng đã đọc

    # ------------------------------------------------------------------ API
    @property
    def buffered_bytes(self) -> int:
        return self.in_order_bytes + sum(self.ooo.values())

    @property
    def rwnd(self) -> int:
        return max(0, self.buffer_size - self.buffered_bytes)

    def start(self) -> None:
        self.sim.schedule(self.app_read_interval, self._app_read)

    def on_segment(self, seg: Segment) -> None:
        # TODO(P2):
        # 1. Probe / segment vượt quá rwnd -> không nhận dữ liệu (hoặc nhận nếu vừa), vẫn trả ACK với rwnd hiện tại.
        # 2. seg.seq == rcv_nxt -> thêm vào buffer, tăng rcv_nxt, ghép các segment ooo liền kề.
        # 3. seg.seq > rcv_nxt -> lưu ooo nếu store_out_of_order và còn chỗ.
        # 4. seg.end <= rcv_nxt -> trùng lặp, bỏ.
        # 5. metrics.on_buffer_change(...); nếu rwnd == 0 -> metrics.on_event(t, "zero_window").
        # 6. self._send_ack()
        raise NotImplementedError

    # ------------------------------------------------------------ nội bộ
    def _send_ack(self, is_window_update: bool = False) -> None:
        # TODO(P2): self.channel.send_to_sender(Ack(self.rcv_nxt, self.rwnd, self.sim.now, is_window_update))
        raise NotImplementedError

    def _app_read(self) -> None:
        # TODO(P2):
        # - đọc n = min(in_order_bytes, app_read_rate * app_read_interval); giảm in_order_bytes; tăng delivered_bytes
        # - metrics.on_app_read, metrics.on_buffer_change
        # - nếu rwnd trước < mss và rwnd sau >= mss -> _send_ack(is_window_update=True)
        # - nếu delivered_bytes < total_bytes -> lên lịch lần đọc tiếp
        raise NotImplementedError
