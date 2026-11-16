# Minh chứng & demo (P3)

- `real_tcp/` : chương trình socket TCP thật để quan sát zero window
  - `slow_server.py` : SO_RCVBUF nhỏ, đọc chậm (ví dụ 4 KB mỗi 100 ms)
  - `fast_client.py` : gửi liên tục
  - Chạy trên 2 máy/VM khác nhau; (tùy chọn) `sudo tc qdisc add dev eth0 root netem delay 50ms loss 1%`
- `pcap/` : file .pcapng (lọc Wireshark: `tcp.analysis.zero_window || tcp.analysis.zero_window_probe || tcp.analysis.window_update`)
- `screenshots/` : ảnh chụp Wireshark, log mô phỏng
- Video demo 3–5 phút: file lớn để trên Google Drive, dán link ở đây: ...
