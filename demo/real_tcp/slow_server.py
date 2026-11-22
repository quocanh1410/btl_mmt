"""Server TCP đọc chậm – tạo hiện tượng zero window (chạy trên MÁY NHẬN).

Ví dụ:
    python slow_server.py --port 5000 --rcvbuf 8192 --read-size 1024 --read-interval 0.05 --pause 10

Ý nghĩa tham số:
    --rcvbuf         kích thước bộ đệm nhận (byte) – nhỏ thì dễ đầy (Linux tự nhân đôi giá trị này)
    --read-size      mỗi lần ứng dụng đọc bao nhiêu byte
    --read-interval  nghỉ bao lâu giữa hai lần đọc (giây)  -> tốc độ đọc ≈ read-size / read-interval
    --pause          không đọc gì trong N giây đầu (để bộ đệm chắc chắn đầy -> thấy rõ probe)
    --log            file CSV ghi (thời gian, số byte đã đọc)
"""
import argparse
import csv
import socket
import time


def main() -> None:
    ap = argparse.ArgumentParser(description="Server TCP đọc chậm")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--rcvbuf", type=int, default=8192)
    ap.add_argument("--read-size", type=int, default=1024)
    ap.add_argument("--read-interval", type=float, default=0.05)
    ap.add_argument("--pause", type=float, default=0.0)
    ap.add_argument("--log", default="server_log.csv")
    a = ap.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Phải đặt SO_RCVBUF TRƯỚC listen() để socket được accept kế thừa (và cửa sổ ban đầu nhỏ)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, a.rcvbuf)
    srv.bind((a.host, a.port))
    srv.listen(1)
    real = srv.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    rate = a.read_size / a.read_interval if a.read_interval > 0 else float("inf")
    print(f"[server] lắng nghe {a.host}:{a.port} | SO_RCVBUF yêu cầu={a.rcvbuf} B, thực tế={real} B")
    print(f"[server] ứng dụng đọc {a.read_size} B mỗi {a.read_interval}s ≈ {rate/1024:.1f} KB/s, "
          f"tạm dừng đọc {a.pause}s đầu")

    conn, addr = srv.accept()
    print(f"[server] kết nối từ {addr[0]}:{addr[1]}")
    t0 = time.time()
    total = 0
    with open(a.log, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time_s", "bytes_read_total"])
        if a.pause > 0:
            print(f"[server] KHÔNG đọc trong {a.pause}s -> bộ đệm sẽ đầy, quan sát ZeroWindow / probe")
            time.sleep(a.pause)
        last_print = 0.0
        while True:
            data = conn.recv(a.read_size)
            if not data:
                break
            total += len(data)
            t = time.time() - t0
            w.writerow([f"{t:.4f}", total])
            if t - last_print >= 1.0:
                print(f"[server] t={t:6.1f}s  đã đọc {total/1024:9.1f} KB")
                last_print = t
            if a.read_interval > 0:
                time.sleep(a.read_interval)
    dt = time.time() - t0
    print(f"[server] xong: {total} B trong {dt:.2f}s -> tốc độ đọc trung bình {total/dt/1024:.1f} KB/s")
    print(f"[server] log: {a.log}")
    conn.close()
    srv.close()


if __name__ == "__main__":
    main()
