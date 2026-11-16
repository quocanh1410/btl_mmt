"""TODO(P3): server TCP đọc chậm để tạo zero window.
Gợi ý: sock.setsockopt(SOL_SOCKET, SO_RCVBUF, 4096) TRƯỚC listen(); vòng lặp recv(1024) + time.sleep(...).
Tham số dòng lệnh: --port, --rcvbuf, --read-size, --read-interval. Ghi log thời điểm & số byte đọc ra CSV.
"""
