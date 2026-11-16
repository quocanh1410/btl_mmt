"""Ghi log và tính chỉ tiêu. Chủ sở hữu: P4.

Định nghĩa chỉ tiêu (đưa vào báo cáo, mục Thiết kế thí nghiệm):
- goodput (byte/s)          = total_bytes ứng dụng nhận / completion_time
- completion_time (s)       = thời điểm ứng dụng nhận đọc xong byte cuối cùng
- avg_in_flight (byte)      = trung bình theo thời gian của snd_nxt - snd_una
- avg/max_buffer_occupancy  = trung bình theo thời gian / cực đại của buffered_bytes (byte và %)
- zero_window_count, timeout_count, probe_count, retx_bytes
- zero_window_time (s)      = tổng thời gian rwnd == 0 (tùy chọn)
Trung bình THEO THỜI GIAN (time-weighted), không phải trung bình theo mẫu.
"""

from __future__ import annotations

from collections import Counter

from .segment import Ack, Segment


class Metrics:
    def __init__(self, total_bytes: int, buffer_size: int) -> None:
        self.total_bytes = total_bytes
        self.buffer_size = buffer_size
        self.events: Counter[str] = Counter()
        self.ts_in_flight: list[tuple[float, int]] = [(0.0, 0)]
        self.ts_buffer: list[tuple[float, int]] = [(0.0, 0)]
        self.ts_rwnd: list[tuple[float, int]] = [(0.0, buffer_size)]
        self.ts_delivered: list[tuple[float, int]] = [(0.0, 0)]
        self.bytes_sent = 0
        self.retx_bytes = 0
        self.completion_time: float | None = None

    # ----------------------------------------------------- hàm ghi (module khác gọi)
    def on_send(self, t: float, seg: Segment, in_flight: int | None = None) -> None:
        # TODO(P4): cộng bytes_sent / retx_bytes; ghi ts_in_flight nếu có in_flight
        raise NotImplementedError

    def on_ack_received(self, t: float, ack: Ack, in_flight: int) -> None:
        # TODO(P4)
        raise NotImplementedError

    def on_buffer_change(self, t: float, buffered_bytes: int, rwnd: int) -> None:
        # TODO(P4)
        raise NotImplementedError

    def on_app_read(self, t: float, nbytes: int) -> None:
        # TODO(P4): cập nhật ts_delivered; khi đủ total_bytes -> completion_time = t
        raise NotImplementedError

    def on_event(self, t: float, name: str) -> None:
        self.events[name] += 1

    # ----------------------------------------------------- tính chỉ tiêu
    @staticmethod
    def time_weighted_mean(series: list[tuple[float, int]], t_end: float) -> float:
        # TODO(P4): sum(value_i * (t_{i+1} - t_i)) / t_end  (hàm bậc thang)
        raise NotImplementedError

    def summary(self) -> dict:
        # TODO(P4): trả dict các chỉ tiêu ở docstring đầu file
        raise NotImplementedError

    def timeseries(self) -> dict[str, list[tuple[float, int]]]:
        return {
            "in_flight": self.ts_in_flight,
            "buffer": self.ts_buffer,
            "rwnd": self.ts_rwnd,
            "delivered": self.ts_delivered,
        }
