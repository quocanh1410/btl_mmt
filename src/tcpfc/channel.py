"""Kênh truyền giữa bên gửi và bên nhận. Chủ sở hữu: P3.

Giả định (ghi vào báo cáo):
- Trễ một chiều = RTT/2, đối xứng; jitter tùy chọn (phân bố đều [-jitter, +jitter]).
- Mất gói độc lập (Bernoulli) với xác suất loss_rate; có thể áp dụng cho cả ACK.
- Không có hàng đợi/nghẽn tại kênh (đây là đề flow control, không phải congestion control).
- (Tùy chọn) băng thông hữu hạn: thêm thời gian phát size/bandwidth.
"""

from __future__ import annotations

import random

from .engine import Simulator
from .segment import Ack, Segment


class Channel:
    def __init__(
        self,
        sim: Simulator,
        rtt: float,
        loss_rate: float,
        rng: random.Random,
        loss_on_ack: bool = True,
        jitter: float = 0.0,
        metrics=None,
    ) -> None:
        self.sim = sim
        self.rtt = rtt
        self.loss_rate = loss_rate
        self.rng = rng
        self.loss_on_ack = loss_on_ack
        self.jitter = jitter
        self.metrics = metrics
        self.sender = None
        self.receiver = None

    def connect(self, sender, receiver) -> None:
        self.sender = sender
        self.receiver = receiver

    def _one_way_delay(self) -> float:
        # TODO(P3): thêm jitter, đảm bảo không âm và (nếu cần) giữ thứ tự gói.
        raise NotImplementedError

    def _is_lost(self, apply_loss: bool) -> bool:
        # TODO(P3): Bernoulli(loss_rate) dùng self.rng (KHÔNG dùng random toàn cục -> mất tái lập).
        raise NotImplementedError

    def send_to_receiver(self, segment: Segment) -> None:
        # TODO(P3): nếu không mất -> self.sim.schedule(delay, self.receiver.on_segment, segment)
        #           nếu mất -> ghi metrics.on_event(t, "data_lost")
        raise NotImplementedError

    def send_to_sender(self, ack: Ack) -> None:
        # TODO(P3): tương tự, gọi self.sender.on_ack(ack); mất ACK chỉ khi loss_on_ack=True
        raise NotImplementedError
