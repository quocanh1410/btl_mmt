# Demo TCP thật trên 2 máy + Wireshark

Mục đích: quan sát **flow control của TCP thật** (không phải mô phỏng) – bên nhận đọc chậm làm
bộ đệm đầy, Wireshark hiện **TCP ZeroWindow**, **TCP ZeroWindowProbe**, **TCP Window Update**.
Dùng để đối chiếu định tính với kết quả mô phỏng (Hình 13) và quay video demo.

Chương trình chỉ dùng thư viện chuẩn Python 3 – chạy được trên Windows, Linux, macOS.

| File | Chạy trên | Vai trò |
|---|---|---|
| `real_tcp/slow_server.py` | **Máy B – máy nhận** | Bộ đệm nhận nhỏ, ứng dụng đọc chậm hoặc tạm dừng đọc |
| `real_tcp/fast_client.py` | **Máy A – máy gửi** | Gửi dữ liệu liên tục nhanh nhất có thể |

## 1. Chuẩn bị (5 phút)

1. Hai máy (laptop/VM) **cùng một mạng**. Wi-Fi trường thường chặn các máy nói chuyện với nhau –
   nếu không kết nối được, dùng **điểm phát Wi-Fi từ điện thoại** cho cả 2 máy.
2. Cài **Python 3** trên cả 2 máy và **Wireshark** trên máy A (máy gửi) – https://www.wireshark.org/download.html
3. Tải repo về cả 2 máy (hoặc chỉ cần copy thư mục `demo/real_tcp/`).
4. Xem **IP của máy B**:
   - Windows: `ipconfig` → dòng *IPv4 Address* của card Wi-Fi
   - Linux/macOS: `ip a` hoặc `ifconfig`
5. **Mở tường lửa cổng 5000 trên máy B**:
   - Windows: lần đầu chạy server, khi hộp thoại hiện ra chọn **Allow access** (mạng Private).
     Hoặc mở PowerShell (Admin):
     `netsh advfirewall firewall add rule name="tcp-demo" dir=in action=allow protocol=TCP localport=5000`
   - Linux (ufw): `sudo ufw allow 5000/tcp`

## 2. Bắt gói trên máy A

Mở Wireshark → chọn card mạng đang dùng (Wi-Fi/Ethernet) → bắt đầu bắt → ô lọc hiển thị gõ:

```
tcp.port == 5000
```

## 3. Ba thí nghiệm

Mỗi thí nghiệm: **chạy server trên máy B trước**, rồi chạy client trên máy A
(thay `192.168.1.20` bằng IP máy B). Mỗi lần chạy server phục vụ 1 kết nối rồi thoát.

### Thí nghiệm 1 – Ứng dụng đọc nhanh (đối chứng: không có zero window)
```bash
# máy B
python slow_server.py --rcvbuf 65536 --read-size 65536 --read-interval 0
# máy A
python fast_client.py --host 192.168.1.20 --bytes 5000000
```
Kỳ vọng: không có dòng ZeroWindow; goodput cao (giới hạn bởi mạng).

### Thí nghiệm 2 – Ứng dụng đọc chậm (bên nhận là nút cổ chai)
```bash
# máy B: bộ đệm 8 KB, đọc 1 KB mỗi 50 ms ≈ 20 KB/s
python slow_server.py --rcvbuf 8192 --read-size 1024 --read-interval 0.05
# máy A
python fast_client.py --host 192.168.1.20 --bytes 500000
```
Kỳ vọng: goodput client in ra ≈ tốc độ đọc của server (~20 KB/s) dù mạng nhanh hơn nhiều;
Wireshark có nhiều dòng **TCP Window Full** / **TCP ZeroWindow** và **TCP Window Update**.

### Thí nghiệm 3 – Ứng dụng tạm dừng đọc 15 s (persist timer + probe)
```bash
# máy B
python slow_server.py --rcvbuf 8192 --read-size 4096 --read-interval 0.01 --pause 15
# máy A
python fast_client.py --host 192.168.1.20 --bytes 300000
```
Kỳ vọng trong Wireshark:
1. Sau ~1 giây bộ đệm đầy → **TCP ZeroWindow** (Win=0) từ máy B.
2. Máy A gửi **TCP ZeroWindowProbe** lặp lại, **khoảng cách giữa các probe tăng dần** (backoff),
   máy B trả lời **TCP ZeroWindowProbeAck** vẫn Win=0.
3. Hết 15 s, server đọc lại → **TCP Window Update** (Win > 0) → máy A gửi tiếp.

Đây chính là Hình 5 (lưu đồ ví dụ zero window) và Hình 13 (mô phỏng S4) trong báo cáo.

## 4. Lọc và chụp ảnh cho báo cáo

Lọc chỉ các gói liên quan flow control:
```
tcp.analysis.zero_window || tcp.analysis.zero_window_probe || tcp.analysis.zero_window_probe_ack || tcp.analysis.window_update || tcp.analysis.window_full
```
- Cột **Win** (thêm bằng chuột phải tiêu đề cột → Column Preferences, hoặc xem trường `tcp.window_size`)
  cho thấy rwnd quảng bá.
- **Statistics → TCP Stream Graphs → Window Scaling** (chọn 1 gói từ A → B trước): vẽ dữ liệu
  đang bay và cửa sổ nhận theo thời gian – so sánh trực tiếp với Hình 12–13 của mô phỏng.
- **Analyze → Expert Information**: đếm số ZeroWindow / ZeroWindowProbe / Window Update.
- Lưu file bắt gói: **File → Save As** → `demo/pcap/thi_nghiem_3.pcapng`; ảnh chụp → `demo/screenshots/`.
- Server ghi `server_log.csv` (thời gian, tổng byte đã đọc) – vẽ được tốc độ đọc thực tế.

## 5. (Tùy chọn, Linux) Thêm trễ / mất gói bằng netem trên máy A
```bash
sudo tc qdisc add dev wlan0 root netem delay 50ms loss 1%   # thay wlan0 bằng tên card mạng
sudo tc qdisc del dev wlan0 root                             # gỡ bỏ sau khi xong
```

## Lưu ý khi so sánh với mô phỏng
- Linux tự **nhân đôi** giá trị `SO_RCVBUF` và còn dùng một phần bộ đệm cho overhead, nên cửa sổ
  thật nhỏ hơn con số in ra; Windows/macOS cũng có quy tắc riêng. Vì vậy chỉ so sánh **định tính**
  (có zero window không, probe có backoff không, goodput có bám tốc độ đọc không), không so con số.
- TCP thật còn có congestion control (cwnd), delayed ACK, Nagle…; mô phỏng chỉ giữ flow control.

## Video demo (3–5 phút) gợi ý kịch bản
1. Giới thiệu 2 máy, IP, sơ đồ (30 s).
2. Thí nghiệm 3 với Wireshark đang chạy – chỉ ra ZeroWindow → probe → Window Update (2 phút).
3. Chạy mô phỏng `python scripts/run_once.py --scenario S4_tam_dung --plot`, mở `plots/run_once.png`
   và so sánh với Wireshark (1 phút).
4. Kết luận: bên nhận đọc chậm → rwnd giảm → bên gửi bị chặn (30 s).

Video lớn: để trên Google Drive, dán link tại đây: …
