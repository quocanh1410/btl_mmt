"""In từng bước mô phỏng bằng lời (để hiểu code chạy thế nào).

Dùng:  python scripts/trace.py              # ví dụ nhỏ mặc định
       python scripts/trace.py --pause      # thêm: ứng dụng ngừng đọc -> thấy zero window + probe
Mỗi dòng: thời điểm, [hàm trong code đang chạy], việc xảy ra.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tcpfc import simulation  # noqa: E402
from tcpfc.channel import Channel  # noqa: E402
from tcpfc.receiver import Receiver  # noqa: E402
from tcpfc.sender import Sender  # noqa: E402

MSS = 1000


def seg_no(byte: int) -> int:
    return byte // MSS + 1


def say(sim, where: str, text: str) -> None:
    print(f"t={sim.now:6.3f}s  {where:<26} {text}")


def install_tracing() -> None:
    # ---------------- bên gửi
    orig_try_send = Sender._try_send
    orig_send_to_receiver = Channel.send_to_receiver

    def send_to_receiver(self, seg):
        s = self.sender
        if seg.is_probe:
            say(self.sim, "[sender._on_persist]", "GỬI PROBE 1 byte: \"còn chỗ chưa?\"")
        else:
            kind = "GỬI LẠI" if seg.is_retx else "Gửi"
            say(self.sim, "[sender._try_send]",
                f"{kind} segment #{seg_no(seg.seq)} (byte {seg.seq}–{seg.end - 1}). "
                f"Đang bay: {s.in_flight} / cửa sổ {s.window} byte")
        return orig_send_to_receiver(self, seg)

    def try_send(self):
        before = self.snd_nxt
        orig_try_send(self)
        if self.snd_nxt == before and self.snd_nxt < self.total_bytes:
            say(self.sim, "[sender._try_send]",
                f"Không gửi được: đang bay {self.in_flight} + {MSS} > cửa sổ {self.window}")

    orig_on_ack = Sender.on_ack

    def on_ack(self, ack):
        tag = "WINDOW UPDATE" if ack.is_window_update else "ACK"
        say(self.sim, "[sender.on_ack]",
            f"Nhận {tag}: ack={ack.ack} (đã nhận đến hết segment #{ack.ack // MSS}), rwnd={ack.rwnd}")
        was_done = self.done
        orig_on_ack(self, ack)
        if self.done and not was_done:
            say(self.sim, "[sender.on_ack]", "Tất cả dữ liệu đã được ACK -> bên gửi xong")

    orig_on_rto = Sender._on_rto

    def on_rto(self):
        if self.in_flight > 0 and not self.done:
            say(self.sim, "[sender._on_rto]", f"HẾT RTO, chưa có ACK -> lùi về byte {self.snd_una} gửi lại")
        orig_on_rto(self)

    # ---------------- bên nhận
    orig_on_segment = Receiver.on_segment

    def on_segment(self, seg):
        if seg.is_probe:
            say(self.sim, "[receiver.on_segment]", "Nhận PROBE -> trả lời rwnd hiện tại")
        else:
            say(self.sim, "[receiver.on_segment]", f"Nhận segment #{seg_no(seg.seq)}")
        orig_on_segment(self, seg)
        say(self.sim, "", f"   bộ đệm: {self.buffered_bytes}/{self.buffer_size} byte, "
                          f"trống {self.free_space} -> gửi ACK(ack={self.rcv_nxt}, rwnd={self.rwnd})")

    orig_read = Receiver._app_read

    pending: list[str] = []

    def app_read(self):
        before = self.delivered_bytes
        paused = self._app_paused(self.sim.now)
        pending.clear()
        orig_read(self)
        n = self.delivered_bytes - before
        if paused:
            if not getattr(self, "_told_pause", False):
                say(self.sim, "[receiver._app_read]", "Ứng dụng TẠM DỪNG, không đọc nữa")
                self._told_pause = True
        elif n:
            say(self.sim, "[receiver._app_read]",
                f"Ứng dụng đọc {n} byte. Bộ đệm còn {self.buffered_bytes} byte, rwnd={self.rwnd}")
        for m in pending:
            say(self.sim, "[receiver._app_read]", m)

    orig_ack = Receiver._send_ack

    def send_ack(self, is_window_update=False):
        if is_window_update:
            pending.append(f"   rwnd tăng nhiều -> chủ động gửi WINDOW UPDATE rwnd={self.rwnd}")
        orig_ack(self, is_window_update)

    Sender._try_send = try_send
    Channel.send_to_receiver = send_to_receiver
    Sender.on_ack = on_ack
    Sender._on_rto = on_rto
    Receiver.on_segment = on_segment
    Receiver._app_read = app_read
    Receiver._send_ack = send_ack


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pause", action="store_true", help="ứng dụng ngừng đọc từ 0.3 s đến 2.5 s")
    a = ap.parse_args()
    cfg = dict(total_bytes=5 * MSS, mss=MSS, buffer_size=2 * MSS, rtt=0.1, bandwidth=None, rto=1.0,
               loss_rate=0.0, app_read_rate=10_000, app_read_interval=0.1, max_sim_time=60)
    if a.pause:
        cfg.update(app_pause_at=0.3, app_pause_duration=2.2)
    print("Ví dụ: gửi 5 segment x 1000 byte | bộ đệm nhận = 2000 byte (2 segment) | RTT = 100 ms\n"
          "Ứng dụng nhận đọc 1000 byte mỗi 0.1 s" + (" | NGỪNG ĐỌC từ 0.3 s đến 2.5 s" if a.pause else "") +
          "\n" + "-" * 100)
    install_tracing()
    out = simulation.run(cfg, seed=1)
    print("-" * 100)
    print(f"Xong: ứng dụng đọc hết lúc t = {out['completion_time']:.3f} s, goodput = {out['goodput']:.0f} byte/s, "
          f"số probe = {out['probe_count']}, số window update = {out['window_update_count']}")


if __name__ == "__main__":
    main()
