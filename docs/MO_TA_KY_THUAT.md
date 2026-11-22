# Mô tả kỹ thuật mô hình mô phỏng – Đề 09

Tài liệu tổng hợp để viết báo cáo (mục 3–7) và chuẩn bị bảo vệ. Mọi con số dưới đây lấy từ
`results/summary.csv` (chạy bằng `python scripts/run_all.py`; chạy lại sẽ cho đúng các số này vì
mô phỏng tất định khi cùng seed).

## 1. Kiến trúc

```
Ứng dụng gửi → Sender ──Segment──► Channel ──► Receiver → Ứng dụng nhận (đọc R_app)
                  ▲                                │
                  └──────── Ack(ack, rwnd) ◄───────┘
Engine (hàng đợi sự kiện) điều khiển thời gian; Metrics ghi chuỗi thời gian và sự kiện.
```

| File | Nội dung |
|---|---|
| `engine.py` | Mô phỏng sự kiện rời rạc: heap theo thời gian, cùng thời điểm thì FIFO, hủy được timer |
| `channel.py` | Trễ lan truyền RTT/2 mỗi chiều, băng thông hữu hạn (thời gian phát), mất gói Bernoulli theo seed |
| `sender.py` | Sliding window theo rwnd, RTO + Go-Back-N, persist timer + window probe |
| `receiver.py` | Bộ đệm B, ACK tích lũy, rwnd, ứng dụng đọc định kỳ, window update, segment sai thứ tự |
| `metrics.py` | Chuỗi thời gian (in-flight, rwnd, bộ đệm, byte đã đọc), đếm sự kiện, tính chỉ tiêu |
| `simulation.py` | Ghép các khối, `run(config, seed)`, giới hạn lý thuyết |

## 2. Giả định và giản lược (đưa vào báo cáo)

| Khía cạnh | Mô hình | TCP thật |
|---|---|---|
| Kiểm soát tắc nghẽn | **Không có cwnd** – cửa sổ gửi = min(rwnd, max_wnd) | min(rwnd, cwnd) |
| Thiết lập/đóng kết nối | Không mô hình (bắt đầu ở trạng thái ESTABLISHED) | 3-way handshake, FIN |
| Kích thước segment | Luôn MSS (trừ segment cuối) | MSS, Nagle |
| ACK | Mỗi segment 1 ACK, ACK tích lũy | Có delayed ACK, SACK |
| Gửi lại | Hết RTO → Go-Back-N từ snd_una; RTO cố định 1 s, nhân đôi khi timeout liên tiếp | RTO theo RFC 6298 + fast retransmit |
| Kênh | Trễ cố định RTT/2, băng thông 10 Mbit/s, hàng đợi không giới hạn, mất gói độc lập | Hàng đợi hữu hạn, mất gói do nghẽn |
| Ứng dụng nhận | Đọc mỗi 1 ms tối đa R_app·Δt byte; có thể tạm dừng | Đọc khi có dữ liệu |
| Trường Window | Không giới hạn 65 535 (coi như có window scaling) | 16 bit + window scale |

## 3. Thuật toán

### Bên gửi (Hình 2)
- Gửi khi `in_flight + len ≤ min(rwnd, max_wnd)`, với `in_flight = snd_nxt − snd_una`.
- ACK mới (`ack > snd_una`): trượt `snd_una`, khởi động lại RTO, đặt lại RTO về giá trị gốc. ACK cũ bị bỏ qua.
- ACK tích lũy có thể vượt `snd_nxt` sau Go-Back-N (bên nhận đã giữ phần sau) → `snd_nxt = max(snd_nxt, ack)`.
- **Persist timer**: bật khi còn dữ liệu, không có gì đang bay và cửa sổ không đủ cho 1 segment.
  Mỗi lần hết hạn gửi **window probe** (1 byte cũ, seq = snd_una − 1, giống Linux: chỉ để bên nhận trả lời
  ACK kèm rwnd) rồi **nhân đôi** khoảng chờ (khởi đầu = RTO = 1 s, trần 60 s).

### Bên nhận (Hình 3, 4)
- Chỗ trống = B − (byte trong bộ đệm, gồm cả segment sai thứ tự). Segment chỉ được nhận nếu nằm trọn trong
  chỗ trống; segment trùng, probe hay segment bị bỏ vẫn được trả ACK.
- **rwnd quảng bá = chỗ trống, nhưng = 0 nếu chỗ trống < min(MSS, B/2)** – tránh Silly Window Syndrome phía
  nhận (RFC 1122 §4.2.3.3; Linux làm tương tự). *Lưu đồ Hình 3 ghi "rwnd = B − dữ liệu trong đệm"; cần bổ sung
  chú thích quy tắc làm tròn này.*
- **Window update** sau khi ứng dụng đọc: gửi ACK chủ động nếu cửa sổ mới ≥ 2 × phần cửa sổ đã báo còn lại
  (quy tắc của Linux `tcp_cleanup_rbuf`). Trường hợp quan trọng nhất: đã báo 0, nay ≥ 1 MSS → gửi ngay.
  *Lưu đồ Hình 4 ghi "rwnd tăng từ < 1 MSS lên ≥ 1 MSS" – đó là trường hợp đặc biệt của quy tắc này.*

## 4. Chỉ tiêu đo (`metrics.py`)

| Chỉ tiêu | Công thức / định nghĩa | Đơn vị |
|---|---|---|
| Goodput | total_bytes / completion_time | B/s (biểu đồ: kB/s hoặc Mbit/s) |
| Thời gian hoàn tất | lúc ứng dụng nhận đọc xong byte cuối | s |
| Dữ liệu đang bay TB | trung bình theo thời gian của snd_nxt − snd_una | byte |
| Bộ đệm bị chiếm TB | trung bình theo thời gian của byte trong bộ đệm / B | % |
| Zero window | số lần rwnd chuyển về 0, tổng thời gian rwnd = 0 | lần, s |
| Probe, window update, timeout, byte gửi lại | đếm sự kiện | lần, byte |

Trung bình theo thời gian của hàm bậc thang: Σ vᵢ·(tᵢ₊₁ − tᵢ) / T.

## 5. Giới hạn lý thuyết (`simulation.theory_goodput`)

Khi không mất gói: **goodput ≤ min( ⌊B/MSS⌋·MSS / RTT , băng thông·MSS/(MSS+40) , R_app )**.
Cột `bottleneck` trong kết quả cho biết giới hạn nào nhỏ nhất (`window`, `link`, `receiver_app`).
Với cấu hình gốc (B = 65 535 B, MSS = 1460 B, RTT = 100 ms, 10 Mbit/s): giới hạn cửa sổ = 642,4 kB/s,
giới hạn đường truyền = 1 216,7 kB/s.

## 6. Kịch bản và kết quả chính

Tham số cố định: 1 MB dữ liệu, MSS 1460 B, B = 65 535 B, RTT 100 ms, 10 Mbit/s, RTO 1 s; 5 seed.

| Kịch bản | R_app | Goodput đo | Lý thuyết | Tỉ lệ | Bộ đệm TB | Ghi chú |
|---|---|---|---|---|---|---|
| S1 đọc nhanh | 10 MB/s | 618,4 kB/s | 642,4 | 0,96 | 0,5 % | giới hạn bởi cửa sổ B/RTT |
| S2 trung bình | 650 kB/s | 474,8 kB/s | 642,4 | 0,74 | 10,8 % | vùng chuyển tiếp R_app ≈ B/RTT |
| S3 đọc chậm | 100 kB/s | 99,5 kB/s | 100 | 0,995 | 77,1 % | **bên nhận là nút cổ chai** |
| S4 tạm dừng 5 s | 100 kB/s | 66,4 kB/s | 100 (66,7 tính cả 5 s dừng) | – | 84,1 % | rwnd = 0 trong 4,9 s, 2 probe (cách 2 s – backoff), 5 window update |

### Nhận xét (gợi ý cho mục 7 của báo cáo)
1. **Bên nhận thành nút cổ chai** khi R_app < B/RTT: goodput bám đúng R_app (S3: 99,5 % R_app), dữ liệu ứ ở
   bộ đệm nhận (77 %), dữ liệu đang bay chỉ còn ≈ R_app·RTT ≈ 10 KiB thay vì 64 KiB (Hình 8, 12).
2. **Quét buffer (Hình 6)**: S1 tăng gần tuyến tính theo B (giới hạn cửa sổ) đến khi chạm băng thông
   (B ≥ 128 KiB ≈ BDP = 10 Mbit/s × 100 ms = 125 kB) thì bão hòa; S3 gần như không đổi – tăng bộ đệm
   không giúp được khi ứng dụng đọc chậm. Riêng B = 8 KiB thì S3 cũng bị giới hạn bởi cửa sổ (73 kB/s < 100 kB/s).
3. **Quét RTT (Hình 7)**: S1 giảm theo 1/RTT (RTT ≥ 100 ms), với RTT nhỏ bị chặn bởi băng thông; S3 gần như
   không phụ thuộc RTT.
4. **Vùng chuyển tiếp (S2, Hình 8)**: goodput thấp hơn cả hai giới hạn (tỉ lệ 0,74–0,87) vì dữ liệu chưa đọc
   chiếm bộ đệm làm cửa sổ hiệu dụng < B. Công thức min(·) là **cận trên**, không phải giá trị chính xác.
5. **Khi nào có zero window?** Ở trạng thái ổn định bên nhận tự cân bằng: bộ đệm ≈ B − R_app·RTT, nên rwnd
   chỉ về 0 khi (a) ứng dụng **ngừng đọc** (S4, Hình 13), (b) ứng dụng đọc **theo cục lớn** – chu kỳ đọc ≥ 200 ms
   (Hình 10), hoặc (c) **R_app·RTT < MSS** – ví dụ S3 với RTT = 10 ms: 638 lần zero window.
   Nếu chu kỳ đọc dài tới mức mỗi lần đọc chỉ lấy được tối đa B byte (1 s), goodput giảm còn ≈ B/chu kỳ (62,5 kB/s).
6. **Mất gói (Hình 9)**: goodput giảm rất mạnh (S1: 0,5 % mất gói → còn 31 %) vì mô hình không có fast
   retransmit: mỗi gói mất phải chờ RTO = 1 s = 10 RTT rồi Go-Back-N. S3 giảm ít hơn về tương đối vì vốn đã
   bị giới hạn bởi bên nhận.
7. Không mất gói thì kết quả **tất định** (độ lệch chuẩn = 0 qua 5 seed): ngẫu nhiên chỉ đến từ mất gói.

## 7. Hạn chế
- Không có congestion control, fast retransmit, SACK, delayed ACK → hiệu năng khi mất gói bi quan hơn TCP thật.
- Kênh không có hàng đợi hữu hạn nên không có mất gói do nghẽn.
- Ứng dụng đọc theo chu kỳ cố định 1 ms (xấp xỉ "đọc ngay khi có dữ liệu").
- So với TCP thật chỉ đối chiếu định tính (demo Wireshark, `demo/README.md`).

## 8. Kiểm thử (`pytest`, 26 test)
- Đơn vị: engine (thứ tự, hủy), channel (trễ, tỉ lệ mất, tái lập), sender (không vượt rwnd, trượt cửa sổ,
  probe khi rwnd = 0, Go-Back-N), receiver (rwnd, zero window, window update, sai thứ tự), metrics (trung bình theo thời gian).
- Tích hợp có đáp án lý thuyết: giới hạn cửa sổ, giới hạn bên nhận, giới hạn đường truyền, tạm dừng → probe,
  R_app·RTT < MSS → zero window, mất gói vẫn hoàn tất, cùng seed cùng kết quả, bộ đệm không bao giờ tràn.
