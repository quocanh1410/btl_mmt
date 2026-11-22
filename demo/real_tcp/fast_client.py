"""Client TCP gửi liên tục (chạy trên MÁY GỬI).

Ví dụ:
    python fast_client.py --host 192.168.1.20 --port 5000 --bytes 2000000

Client gửi nhanh nhất có thể; tốc độ thực tế sẽ bị giới hạn bởi rwnd mà server quảng bá.
"""
import argparse
import socket
import time


def main() -> None:
    ap = argparse.ArgumentParser(description="Client TCP gửi liên tục")
    ap.add_argument("--host", required=True, help="IP của máy chạy slow_server.py")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--bytes", type=int, default=2_000_000, help="tổng số byte cần gửi")
    ap.add_argument("--chunk", type=int, default=16384, help="mỗi lần gọi send() bao nhiêu byte")
    a = ap.parse_args()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f"[client] kết nối {a.host}:{a.port} ...")
    s.connect((a.host, a.port))
    local = s.getsockname()
    print(f"[client] đã kết nối từ {local[0]}:{local[1]} | gửi {a.bytes} B")

    payload = bytes(range(256)) * (a.chunk // 256 + 1)
    payload = payload[: a.chunk]
    sent = 0
    t0 = time.time()
    last_print = 0.0
    while sent < a.bytes:
        n = min(a.chunk, a.bytes - sent)
        s.sendall(payload[:n])          # bị chặn khi bộ đệm gửi đầy (do rwnd = 0)
        sent += n
        t = time.time() - t0
        if t - last_print >= 1.0:
            print(f"[client] t={t:6.1f}s  đã đẩy vào socket {sent/1024:9.1f} KB")
            last_print = t
    s.shutdown(socket.SHUT_WR)          # báo hết dữ liệu (FIN)
    s.recv(1)                           # chờ server đóng -> mọi byte đã được đọc
    dt = time.time() - t0
    print(f"[client] xong: {sent} B trong {dt:.2f}s -> goodput ≈ {sent/dt/1024:.1f} KB/s")
    s.close()


if __name__ == "__main__":
    main()
