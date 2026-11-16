"""Bên gửi TCP (rút gọn, chỉ flow control). Chủ sở hữu: P1.

Giả định cần ghi vào báo cáo:
- Ứng dụng gửi luôn có sẵn dữ liệu (bulk transfer total_bytes).
- Cửa sổ gửi hiệu dụng = min(rwnd, max_wnd); KHÔNG có cwnd.
- Mất gói -> RTO -> gửi lại từ snd_una (Go-Back-N). Ghi rõ RTO cố định hay RFC 6298.
- rwnd = 0 -> persist timer, gửi window probe; backoff probe (nhân đôi, có trần).
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
    ) -> None:
        self.sim = sim
        self.channel = channel
        self.metrics = metrics
        self.total_bytes = total_bytes
        self.mss = mss
        self.rto = rto
        self.max_wnd = max_wnd
        self.persist_init = persist_init if persist_init is not None else rto
        self.persist_max = persist_max

        self.snd_una = 0      # byte cũ nhất chưa được ACK
        self.snd_nxt = 0      # byte tiếp theo sẽ gửi
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
            w = min(w, self.max_wnd)
        return w

    def start(self) -> None:
        self._try_send()

    def on_ack(self, ack: Ack) -> None:
        # TODO(P1):
        # 1. Nếu ack.ack > snd_una: trượt snd_una, khởi động lại / hủy RTO timer.
        # 2. Cập nhật self.rwnd = ack.rwnd (lưu ý ACK cũ/đến trễ – ghi giả định).
        # 3. rwnd == 0 và còn dữ liệu -> bật persist timer; rwnd > 0 -> hủy persist timer, reset backoff.
        # 4. metrics.on_ack_received(...); gọi self._try_send().
        # 5. Nếu done -> hủy mọi timer.
        raise NotImplementedError

    # ------------------------------------------------------------ nội bộ
    def _try_send(self) -> None:
        # TODO(P1): while còn dữ liệu và in_flight + len <= window: tạo Segment, channel.send_to_receiver,
        #           metrics.on_send, tăng snd_nxt; bật RTO timer nếu chưa có.
        #           Quyết định: có gửi segment < MSS khi cửa sổ còn nhỏ không? (liên quan SWS – ghi rõ)
        raise NotImplementedError

    def _on_rto(self) -> None:
        # TODO(P1): metrics.on_event(t, "timeout"); snd_nxt = snd_una; gửi lại (is_retx=True).
        raise NotImplementedError

    def _on_persist(self) -> None:
        # TODO(P1): gửi probe (is_probe=True), metrics.on_event(t, "probe"),
        #           nhân đôi _persist_interval (trần persist_max), đặt lại persist timer.
        raise NotImplementedError
