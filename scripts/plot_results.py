"""Vẽ biểu đồ từ results/. Chủ sở hữu: P3.

Biểu đồ tối thiểu cần có (mỗi hình: tiêu đề, nhãn trục có ĐƠN VỊ, chú giải, error bar = std qua 5 seed):
 1. Goodput (Mbit/s) theo buffer_size (KB) – S1 vs S3, kèm đường lý thuyết min(B/RTT, R_app)
 2. Goodput theo RTT (ms)
 3. Goodput & trễ hoàn tất theo app_read_rate  -> chỉ ra điểm receiver trở thành nút cổ chai
 4. Goodput / số lần timeout theo loss_rate
 5. Chuỗi thời gian 1 lần chạy S3: in-flight, rwnd, buffer occupancy theo thời gian (minh họa zero window)
Lưu PNG (dpi 200) và PDF vào plots/.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    # TODO(P3)
    raise NotImplementedError


if __name__ == "__main__":
    main()
