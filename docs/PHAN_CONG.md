# Bảng phân công – Đề 09

Nguyên tắc: **3 người code + thử nghiệm (P1–P3), 1 người chuyên báo cáo (P4)**.
Mỗi người code sở hữu một khối code + một nhóm thí nghiệm, và viết **ghi chú kỹ thuật** (`docs/ghi_chu/pX.md`)
để P4 viết báo cáo. P4 viết toàn bộ báo cáo, slide, quản lý hồ sơ nộp.

> Lưu ý:
> - Đề quy định nhóm 05 người. Nhóm 4 người cần báo giảng viên và xin duyệt phân công này ở Bước 1 (Đề xuất).
> - Bảo vệ cá nhân (30%) có tiêu chí "thao tác demo/đọc mã và dữ liệu". P4 vẫn nên đọc hiểu code,
>   tự chạy được `run_once.py` và giải thích được các biểu đồ; P1–P3 phải trình bày được phần lý thuyết của module mình.

---

## P1 – Bên gửi · Tích hợp

**Code**
- `src/tcpfc/sender.py`
  - Biến trạng thái: `snd_una`, `snd_nxt`, `MSS`, `rwnd` nhận được, tổng số byte cần gửi.
  - Sliding window: chỉ gửi khi `snd_nxt - snd_una + MSS <= min(rwnd, max_wnd)`.
  - Xử lý ACK tích lũy: trượt `snd_una`, cập nhật `rwnd`, gửi tiếp.
  - Retransmission timeout (RTO cố định hoặc RFC 6298 – ghi rõ) → gửi lại từ `snd_una` (Go-Back-N).
  - **Zero window**: persist timer, window probe, backoff thời gian probe.
- `src/tcpfc/simulation.py`: ghép engine + channel + sender + receiver + metrics, `run(config, seed) -> dict`.
- `tests/test_sender.py`, `tests/test_end_to_end.py`.

**Thử nghiệm**: kịch bản quét **RTT** và **tỷ lệ mất gói** (`sweep_rtt`, `sweep_loss`); kiểm tra kết quả hợp lý, giải thích hiện tượng timeout/probe.

**Ghi chú cho báo cáo** (`docs/ghi_chu/p1.md`): thuật toán bên gửi, giả định, nhận xét kết quả RTT/mất gói → P4 dùng cho mục 4, 7.2, 7.4.

**Quản lý kỹ thuật**: review & merge PR vào `main`, giữ CI xanh.

---

## P2 – Bên nhận · Bộ đệm · Chỉ tiêu đo

**Code**
- `src/tcpfc/receiver.py`
  - Bộ đệm nhận `buffer_size`; `rcv_nxt`; segment ngoài thứ tự (lưu hoặc bỏ – ghi rõ).
  - `rwnd = buffer_size - buffered_bytes` gửi trong mỗi ACK.
  - Ứng dụng đọc với tốc độ `app_read_rate`, chu kỳ `app_read_interval`.
  - **Window update** khi rwnd tăng từ < MSS lên ≥ MSS.
  - (Tùy chọn) tránh Silly Window Syndrome phía nhận.
- `src/tcpfc/metrics.py`: goodput, dữ liệu đang bay, buffer occupancy, trễ hoàn tất, số lần zero window/timeout/probe (trung bình theo thời gian).
- `tests/test_receiver.py`, `tests/test_metrics.py`.

**Thử nghiệm**: 3 kịch bản tải S1/S2/S3, quét **buffer_size** và **app_read_rate** (`sweep_buffer`, `sweep_app_rate`) → chứng minh **phía nhận trở thành nút cổ chai**, so sánh với lý thuyết `min(B/RTT, R_app)`.

**Ghi chú cho báo cáo** (`docs/ghi_chu/p2.md`): mô hình bên nhận, định nghĩa & công thức chỉ tiêu, nhận xét kết quả → P4 dùng cho mục 5, 6.3, 7.1, 7.3, 7.6.

---

## P3 – Kênh truyền · Engine · Hạ tầng thí nghiệm · Demo TCP thật

**Code**
- `src/tcpfc/engine.py` (đã có bản khởi đầu – kiểm thử, mở rộng), `src/tcpfc/channel.py` (trễ RTT/2, jitter, mất gói Bernoulli, seed).
- `scripts/run_experiments.py`: chạy mọi kịch bản × 5 seed → `results/raw/*.csv`, `results/summary.csv` (mean/std).
- `scripts/plot_results.py`: các biểu đồ có tiêu đề, đơn vị, chú giải, error bar; biểu đồ chuỗi thời gian in-flight/rwnd/buffer.
- `scripts/make_submission.sh`, `results/ENVIRONMENT.md`.
- `tests/test_engine.py`, `tests/test_channel.py`.
- `demo/real_tcp/`: TCP thật trên 2 máy/VM (SO_RCVBUF nhỏ + đọc chậm, `tc netem`), Wireshark: ZeroWindow / ZeroWindowProbe / Window Update. Quay **video demo 3–5 phút**.

**Thử nghiệm**: chạy bản cuối toàn bộ thí nghiệm, xuất biểu đồ cho báo cáo; thí nghiệm TCP thật.

**Ghi chú cho báo cáo** (`docs/ghi_chu/p3.md`): kiến trúc mô phỏng, mô hình kênh, giới hạn mô hình, kết quả Wireshark → P4 dùng cho mục 3, 8.

---

## P4 – Báo cáo · Slide · Hồ sơ nộp (không code)

- Viết **toàn bộ báo cáo** `report/sections/*.md` (15–25 trang) dựa trên ghi chú kỹ thuật, biểu đồ và CSV của P1–P3:
  - Tự nghiên cứu & viết ngay từ tuần 1: mục 1 (mục tiêu), 2 (lý thuyết: sliding window, rwnd, zero window, persist timer, SWS, flow vs congestion control), 10 (tài liệu tham khảo – RFC 9293, 6298, 1122).
  - Từ GĐ 3: mục 3–6 theo ghi chú kỹ thuật.
  - Từ GĐ 4: mục 7–9 (phân tích: tách rõ Quan sát – Nhận định – Giới hạn; mọi hình ghi tham số, số seed, đơn vị).
- Vẽ **sơ đồ khối, sơ đồ trình tự** (sequence diagram) gửi/nhận/zero window cho báo cáo và slide.
- Ghép báo cáo → PDF; làm **slide bảo vệ** (mỗi người code góp 2–4 slide nội dung phần mình, P4 thống nhất hình thức).
- Hồ sơ: đề xuất gửi giảng viên (Bước 1), `docs/NHAT_KY_DONG_GOP.md` (nhắc mọi người ghi hàng tuần), `docs/KHAI_BAO_AI.md`, rà checklist mục VII của đề, biên bản họp.
- Review PR ở góc độ "đọc có hiểu không": docstring, giả định, tên biến khớp với báo cáo.

---

## Luồng phối hợp code → báo cáo

```
P1/P2/P3: code + test ──► chạy thí nghiệm ──► CSV + biểu đồ (P3) ──┐
         └─► ghi chú kỹ thuật docs/ghi_chu/pX.md ──────────────────┼──► P4 viết báo cáo + slide
P4: lý thuyết (tuần 1–2) ──────────────────────────────────────────┘
```
P4 hỏi lại trực tiếp trong issue/PR khi ghi chú chưa rõ; người code trả lời trong 24h.

## Mốc thời gian (điều chỉnh theo hạn nộp thực tế)

| Giai đoạn | P1–P3 (code & thử nghiệm) | P4 (báo cáo) |
|---|---|---|
| GĐ1 | Chốt `GIAO_DIEN.md` | Gửi đề xuất + phân công cho GV; khung báo cáo |
| GĐ2 | Mỗi module qua test đơn vị; ghép end-to-end không mất gói | Viết mục 1, 2, 10 |
| GĐ3 | Đủ chức năng (mất gói, zero window, window update); demo TCP thật lần 1; ghi chú kỹ thuật bản 1 | Viết mục 3, 4, 5, 6; sơ đồ |
| GĐ4 | Chạy đủ kịch bản × 5 seed, CSV + biểu đồ | Viết mục 7, 8 |
| GĐ5 | Sửa lỗi, video demo, góp slide | Mục 9, ghép PDF, slide |
| GĐ6 | Chạy lại trên máy sạch | Rà checklist, nén & nộp |
