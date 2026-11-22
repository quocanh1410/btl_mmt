"""Kênh truyền giữa bên gửi và bên nhận. Chủ sở hữu: P3.

Giả định (ghi vào báo cáo):
- Trễ một chiều = RTT/2, đối xứng; jitter tùy chọn (phân bố đều [-jitter, +jitter]).
  Khi jitter = 0 kênh giữ nguyên thứ tự gói; khi jitter > 0 gói có thể đến sai thứ tự.
- Mất gói độc lập (Bernoulli) với xác suất loss_rate; có thể áp dụng cho cả ACK.
- Băng thông liên kết bandwidth (bit/s) mỗi chiều: mỗi gói chiếm thời gian phát
  (kích thước + 40 byte header) · 8 / bandwidth; gói sau chờ gói trước phát xong (hàng đợi FIFO
  không giới hạn, KHÔNG mất gói do tràn hàng đợi – đề flow control, không mô hình nghẽn).
  bandwidth = None -> băng thông vô hạn, chỉ còn trễ lan truyền.
- Mọi số ngẫu nhiên lấy từ self.rng (đã gieo seed) -> cùng seed cho cùng kết quả.
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
        bandwidth: float | None = None,
        header_bytes: int = 40,
    ) -> None:
        if rtt <= 0:
            raise ValueError("rtt phải > 0")
        if not 0.0 <= loss_rate < 1.0:
            raise ValueError("loss_rate phải trong [0, 1)")
        self.sim = sim
        self.rtt = rtt
        self.loss_rate = loss_rate
        self.rng = rng
        self.loss_on_ack = loss_on_ack
        self.jitter = jitter
        self.metrics = metrics
        self.bandwidth = bandwidth
        self.header_bytes = header_bytes
        self._free_at = {"data": 0.0, "ack": 0.0}   # thời điểm liên kết mỗi chiều rảnh
        self.sender = None
        self.receiver = None

    def connect(self, sender, receiver) -> None:
        self.sender = sender
        self.receiver = receiver

    def _one_way_delay(self) -> float:
        d = self.rtt / 2
        if self.jitter > 0:
            d += self.rng.uniform(-self.jitter, self.jitter)
        return max(d, 0.0)

    def _tx_delay(self, direction: str, payload: int) -> float:
        """Thời gian chờ phát + phát gói trên liên kết (0 nếu băng thông vô hạn)."""
        if not self.bandwidth:
            return 0.0
        start = max(self.sim.now, self._free_at[direction])
        done = start + (payload + self.header_bytes) * 8 / self.bandwidth
        self._free_at[direction] = done
        return done - self.sim.now

    def _is_lost(self, apply_loss: bool) -> bool:
        return apply_loss and self.loss_rate > 0 and self.rng.random() < self.loss_rate

    def _event(self, name: str) -> None:
        if self.metrics is not None:
            self.metrics.on_event(self.sim.now, name)

    def send_to_receiver(self, segment: Segment) -> None:
        tx = self._tx_delay("data", segment.length)   # gói vẫn chiếm liên kết dù sau đó bị mất
        if self._is_lost(True):
            self._event("data_lost")
            return
        self.sim.schedule(tx + self._one_way_delay(), self.receiver.on_segment, segment)

    def send_to_sender(self, ack: Ack) -> None:
        tx = self._tx_delay("ack", 0)
        if self._is_lost(self.loss_on_ack):
            self._event("ack_lost")
            return
        self.sim.schedule(tx + self._one_way_delay(), self.sender.on_ack, ack)
