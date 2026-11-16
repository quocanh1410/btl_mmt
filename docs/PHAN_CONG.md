# Bảng phân công – Đề 09

Nguyên tắc: **mỗi người sở hữu một khối code + một phần báo cáo + một phần slide**, để khi bảo vệ cá nhân
(30% điểm, chấm riêng) ai cũng giải thích và demo được phần của mình. Mọi người đều review PR của người khác
nên cần hiểu tổng thể.

> Lưu ý: đề quy định nhóm 05 người. Nhóm 4 người cần báo giảng viên và xin duyệt phân công này ở Bước 1 (Đề xuất).

---

## P1 – Trưởng nhóm · Bên gửi (Sender) · Tích hợp

**Code**
- `src/tcpfc/sender.py`
  - Biến trạng thái: `snd_una`, `snd_nxt`, `MSS`, `rwnd` nhận được, tổng số byte cần gửi.
  - Sliding window: chỉ gửi khi `snd_nxt - snd_una + MSS <= min(rwnd, max_wnd)`.
  - Xử lý ACK tích lũy: trượt `snd_una`, cập nhật `rwnd`, gửi tiếp.
  - Retransmission timeout (RTO cố định hoặc tính theo SRTT/RTTVAR – RFC 6298, ghi rõ chọn gì) → gửi lại từ `snd_una` (Go-Back-N).
  - **Zero window**: khi `rwnd = 0` bật **persist timer**, gửi window probe (1 byte hoặc segment rỗng — ghi rõ), backoff thời gian probe.
- `src/tcpfc/simulation.py`: ghép engine + channel + sender + receiver + metrics, hàm `run(config) -> dict`.
- `tests/test_sender.py`, `tests/test_end_to_end.py`.

**Báo cáo**: `report/sections/02_ly_thuyet.md` (sliding window, advertised window, phân biệt flow control vs congestion control, persist timer – RFC 9293), `04_mo_hinh_ben_gui.md`.

**Quản lý**: tạo issue, chia milestone, chủ trì họp tuần, merge PR vào `main`, nộp bài.

---

## P2 – Bên nhận (Receiver) · Bộ đệm · Ứng dụng đọc

**Code**
- `src/tcpfc/receiver.py`
  - Bộ đệm nhận dung lượng `buffer_size` (byte); `rcv_nxt`; dữ liệu đúng thứ tự vào buffer.
  - Segment ngoài thứ tự: lưu (chiếm buffer) hoặc bỏ — chọn 1 và ghi rõ giả định.
  - Tính `rwnd = buffer_size - buffered_bytes` và gửi trong mỗi ACK.
  - Ứng dụng đọc với tốc độ `app_read_rate` (byte/s), mô hình sự kiện đọc định kỳ (chu kỳ `app_read_interval`).
  - **Window update**: khi ứng dụng đọc làm rwnd tăng từ 0 (hoặc < MSS) lên ≥ MSS → chủ động gửi ACK cập nhật cửa sổ.
  - (Mở rộng tùy chọn) Silly Window Syndrome: so sánh có/không có tránh SWS phía nhận (Clark).
- `tests/test_receiver.py`.

**Báo cáo**: `report/sections/05_mo_hinh_ben_nhan.md`; phân tích hiện tượng **receiver bottleneck** trong `07_phan_tich.md` (phối hợp P4).

---

## P3 – Kênh truyền · Engine sự kiện · Kiểm chứng TCP thật

**Code**
- `src/tcpfc/engine.py`: bộ lập lịch sự kiện (đã có bản khởi đầu, P3 chịu trách nhiệm mở rộng/sửa lỗi, thêm hủy timer).
- `src/tcpfc/channel.py`: trễ một chiều = RTT/2 (+ jitter tùy chọn), mất gói Bernoulli với xác suất `loss_rate`, RNG có `seed`; áp dụng mất gói cho cả data và ACK (cấu hình được). Băng thông liên kết tùy chọn (thời gian phát = size/bandwidth).
- `tests/test_engine.py`, `tests/test_channel.py`.
- `demo/real_tcp/`: thí nghiệm **TCP thật** để đối chiếu định tính: server đọc chậm + `SO_RCVBUF` nhỏ, client gửi liên tục, chạy trên 2 máy/VM (hoặc dùng `tc netem` tạo RTT/mất gói), bắt gói bằng Wireshark → chụp **TCP ZeroWindow / Window Update / ZeroWindowProbe**.
- Quay video demo 3–5 phút.

**Báo cáo**: `report/sections/03_kien_truc_mo_phong.md` (engine, kênh, giả định, giới hạn mô hình), `08_doi_chieu_tcp_that.md`.

---

## P4 – Thí nghiệm · Chỉ tiêu · Biểu đồ · Tổng hợp báo cáo

**Code**
- `src/tcpfc/metrics.py`: ghi chuỗi thời gian (in-flight, buffer occupancy, rwnd), tính chỉ tiêu:
  - **Goodput** = byte ứng dụng nhận đúng / thời gian hoàn tất (Mbit/s hoặc KB/s – thống nhất đơn vị).
  - **Dữ liệu đang bay** = `snd_nxt - snd_una` (byte), lấy trung bình theo thời gian.
  - **Buffer occupancy** (byte và % dung lượng), trung bình + max.
  - **Trễ hoàn tất** (s), số lần zero window, số lần truyền lại, số probe.
- `configs/*.yaml`, `scripts/run_experiments.py` (≥ 3 kịch bản, ≥ 2 tham số quét, 5 seed, xuất CSV có mean/std), `scripts/plot_results.py` (tiêu đề, chú giải, đơn vị, error bar), `scripts/make_submission.sh`.
- `tests/test_metrics.py`.

**Báo cáo**: `report/sections/06_thiet_ke_thi_nghiem.md`, `07_phan_tich.md` (chủ trì), ghép toàn bộ báo cáo → PDF, slide tổng.

---

## Phần chung (cả nhóm)

| Hạng mục | Chủ trì | Tham gia |
|---|---|---|
| `01_muc_tieu.md`, `09_han_che_ket_luan.md` | P1 | tất cả |
| Định nghĩa giao diện `segment.py` + [GIAO_DIEN.md](GIAO_DIEN.md) | P1 | tất cả duyệt ở tuần 1 |
| Slide bảo vệ | P4 | mỗi người 2–4 slide phần mình |
| Nhật ký đóng góp | mỗi người tự ghi | P1 kiểm tra hàng tuần |
| Khai báo AI | mỗi người tự khai | P1 tổng hợp |

## Mốc thời gian (điều chỉnh theo hạn nộp thực tế)

| Tuần | Mốc | Đầu ra |
|---|---|---|
| T1 | Đề xuất + chốt giao diện | Gửi GV đề xuất & phân công; `GIAO_DIEN.md` được cả nhóm approve |
| T2 | Bản chạy được tối thiểu | Mỗi module qua test đơn vị; P1 ghép end-to-end không mất gói |
| T3 | Đủ chức năng | Mất gói + RTO, zero window + probe, window update; demo TCP thật lần 1 |
| T4 | Thí nghiệm | Chạy đủ kịch bản × 5 seed, có CSV và biểu đồ nháp |
| T5 | Phân tích + báo cáo | Báo cáo bản nháp đầy đủ, slide, video |
| T6 | Hoàn thiện | Rà soát, chạy lại từ đầu trên máy sạch, nén & nộp |
