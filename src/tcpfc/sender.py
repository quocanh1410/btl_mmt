"""Bên gửi TCP (rút gọn, chỉ flow control). Chủ sở hữu: P1.

Giả định (ghi vào báo cáo):
- Ứng dụng gửi luôn có sẵn dữ liệu (bulk transfer total_bytes byte).
- Cửa sổ gửi hiệu dụng = min(rwnd, max_wnd); KHÔNG có cwnd (không mô hình congestion control).
- Chỉ gửi segment đủ MSS (trừ segment cuối) -> tránh "silly window" phía gửi.
- Mất gói -> hết RTO -> gửi lại từ snd_una (Go-Back-N). RTO cố định, nhân đôi sau mỗi lần
  timeout liên tiếp (có trần rto_max), trở về giá trị ban đầu khi có ACK mới.
- Persist timer bật khi còn dữ liệu, không có gì đang bay và cửa sổ không đủ cho 1 segment
  (đặc biệt khi rwnd = 0). Mỗi lần hết hạn gửi 1 window probe rồi nhân đôi khoảng chờ (trần persist_max).
- Window probe mô phỏng kiểu Linux: 1 byte cũ (seq = snd_una - 1), không mang dữ liệu mới,
  chỉ để bên nhận trả lời ACK kèm rwnd hiện tại.
"""

from __future__ import annotations

from .engine import EventHandle, Simulator
from .segment import Ack, Segment


class Sender:
    def __init__(
        self,
        sim: Simulator,
        channel,
        metrics,
        total_bytes: int,
        mss: int,
        rto: float,
        init_rwnd: int,
        max_wnd: int | None = None,
        persist_init: float | None = None,
        persist_max: float = 60.0,
        rto_backoff: bool = True,
        rto_max: float = 60.0,
    ) -> None:
        self.sim = sim
        self.channel = channel
        self.metrics = metrics
        self.total_bytes = total_bytes
        self.mss = mss
        self.rto_base = rto
        self.rto = rto
        self.rto_backoff = rto_backoff
        self.rto_max = rto_max
        self.max_wnd = max_wnd
        self.persist_init = persist_init if persist_init is not None else rto
        self.persist_max = persist_max

        self.snd_una = 0      # byte cũ nhất chưa được ACK
        self.snd_nxt = 0      # byte tiếp theo sẽ gửi
        self.snd_max = 0      # byte cao nhất từng gửi (để nhận biết gửi lại)
        self.rwnd = init_rwnd

        self._rto_timer: EventHandle | None = None
        self._persist_timer: EventHandle | None = None
        self._persist_interval = self.persist_init

    # ------------------------------------------------------------------ API
    @property
    def in_flight(self) -> int:
        return self.snd_nxt - self.snd_una

    @property
    def done(self) -> bool:
        return self.snd_una >= self.total_bytes

    @property
    def window(self) -> int:
        w = self.rwnd
        if self.max_wnd is not None:
            w = min(w, int(self.max_wnd))
        return w

    def start(self) -> None:
        self._try_send()

    def on_ack(self, ack: Ack) -> None:
        t = self.sim.now
        if ack.ack < self.snd_una:
            return  # ACK cũ đến trễ: bỏ qua (kể cả rwnd của nó, vì đã lỗi thời)

        if ack.ack > self.snd_una:
            # ACK mới: trượt cửa sổ
            self.snd_una = min(ack.ack, self.total_bytes)
            # sau Go-Back-N, ACK tích lũy có thể vượt snd_nxt (bên nhận đã giữ phần sau)
            self.snd_nxt = max(self.snd_nxt, self.snd_una)
            self.rto = self.rto_base
            self.sim.cancel(self._rto_timer)
            self._rto_timer = None
            if self.in_flight > 0:
                self._start_rto()

        self.rwnd = ack.rwnd
        self.metrics.on_ack_received(t, ack, self.in_flight)

        if self.done:
            self._stop_timers()
            return

        if self.rwnd > 0 and self._persist_timer is not None:
            self.sim.cancel(self._persist_timer)
            self._persist_timer = None
            self._persist_interval = self.persist_init
        self._try_send()

    # ------------------------------------------------------------ nội bộ
    def _seg_len(self) -> int:
        return min(self.mss, self.total_bytes - self.snd_nxt)

    def _try_send(self) -> None:
        t = self.sim.now
        while self.snd_nxt < self.total_bytes:
            length = self._seg_len()
            if self.in_flight + length > self.window:
                break
            seg = Segment(self.snd_nxt, length, t, is_retx=self.snd_nxt < self.snd_max)
            self.snd_nxt += length
            self.snd_max = max(self.snd_max, self.snd_nxt)
            self.channel.send_to_receiver(seg)
            self.metrics.on_send(t, seg, self.in_flight)
            if self._rto_timer is None:
                self._start_rto()

        # Bị chặn bởi cửa sổ bên nhận mà không còn gì đang bay -> cần persist timer,
        # nếu không sẽ kẹt khi ACK báo cửa sổ mới bị mất.
        blocked = self.snd_nxt < self.total_bytes and self.in_flight == 0
        if blocked and self._persist_timer is None:
            self.metrics.on_event(t, "sender_blocked")
            self._persist_timer = self.sim.schedule(self._persist_interval, self._on_persist)

    def _start_rto(self) -> None:
        self._rto_timer = self.sim.schedule(self.rto, self._on_rto)

    def _on_rto(self) -> None:
        self._rto_timer = None
        if self.in_flight == 0 or self.done:
            return
        self.metrics.on_event(self.sim.now, "timeout")
        self.snd_nxt = self.snd_una           # Go-Back-N
        self.metrics.on_in_flight(self.sim.now, self.in_flight)
        if self.rto_backoff:
            self.rto = min(self.rto * 2, self.rto_max)
        self._try_send()

    def _on_persist(self) -> None:
        self._persist_timer = None
        if self.done:
            return
        if self.in_flight > 0 or self._seg_len() <= self.window:
            self._try_send()          # cửa sổ đã mở trong lúc chờ
            return
        t = self.sim.now
        probe = Segment(max(self.snd_una - 1, 0), 1, t, is_probe=True)
        self.channel.send_to_receiver(probe)
        self.metrics.on_event(t, "probe")
        self._persist_interval = min(self._persist_interval * 2, self.persist_max)
        self._persist_timer = self.sim.schedule(self._persist_interval, self._on_persist)

    def _stop_timers(self) -> None:
        self.sim.cancel(self._rto_timer)
        self.sim.cancel(self._persist_timer)
        self._rto_timer = self._persist_timer = None
