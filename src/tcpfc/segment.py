"""Cấu trúc dữ liệu dùng chung. Sửa file này phải qua PR và được cả nhóm approve."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    """Segment dữ liệu từ bên gửi sang bên nhận.

    seq     : số thứ tự byte đầu tiên trong segment
    length  : số byte dữ liệu (probe có thể là 1 byte hoặc 0 – ghi rõ giả định)
    sent_at : thời điểm gửi (s)
    """

    seq: int
    length: int
    sent_at: float
    is_probe: bool = False
    is_retx: bool = False

    @property
    def end(self) -> int:
        return self.seq + self.length


@dataclass(frozen=True)
class Ack:
    """ACK tích lũy từ bên nhận về bên gửi.

    ack  : byte tiếp theo bên nhận mong đợi (mọi byte < ack đã nhận đúng thứ tự)
    rwnd : advertised receive window (byte) tại thời điểm gửi ACK
    """

    ack: int
    rwnd: int
    sent_at: float
    is_window_update: bool = False
