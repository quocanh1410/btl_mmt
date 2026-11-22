"""Vẽ biểu đồ từ results/. Chủ sở hữu: P3.

Mỗi hình: tiêu đề, nhãn trục có ĐƠN VỊ, chú giải, error bar = độ lệch chuẩn qua các seed.
Đường nét đứt màu xám = giới hạn lý thuyết min(B/RTT, băng thông, R_app).
Lưu PNG (dpi 200) vào plots/.   Dùng: python scripts/plot_results.py
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "plots"

# Bảng màu phân loại cố định (đã kiểm tra an toàn cho người mù màu): kịch bản luôn giữ màu của nó
COLOR = {"S1_nhe": "#2a78d6", "S3_nang": "#eb6834", "S4_tam_dung": "#1baf7a", "S2_trung_binh": "#eda100"}
MARK = {"S1_nhe": "o", "S3_nang": "s", "S4_tam_dung": "^", "S2_trung_binh": "D"}
NAME = {"S1_nhe": "S1 – ứng dụng đọc nhanh", "S2_trung_binh": "S2 – trung bình",
        "S3_nang": "S3 – ứng dụng đọc chậm (100 kB/s)", "S4_tam_dung": "S4 – tạm dừng đọc 5 s"}
THEORY = "#8a8984"
TS_COLOR = {"in_flight": "#2a78d6", "rwnd": "#eb6834", "buffer": "#1baf7a"}
TS_NAME = {"in_flight": "Dữ liệu đang bay (bên gửi)", "rwnd": "rwnd quảng bá (bên nhận)",
           "buffer": "Dữ liệu trong bộ đệm nhận"}
TS_STYLE = {"in_flight": "-", "rwnd": "--", "buffer": ":"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e6e5e0",
    "grid.linewidth": 0.8, "axes.edgecolor": "#8a8984", "legend.frameon": False, "lines.linewidth": 2,
})


def load():
    s = pd.read_csv(ROOT / "results" / "summary.csv")
    base = yaml.safe_load(open(ROOT / "configs" / "base.yaml", encoding="utf-8"))
    return s, base


def mbps(x):
    return x * 8 / 1e6


def footer(fig, base, s, extra="", single_run=False):
    n = int(s["n_seeds"].iloc[0])
    tail = "Một lần chạy (seed đầu tiên)." if single_run else f"Trung bình {n} seed, thanh lỗi = độ lệch chuẩn."
    txt = (f"Cố định: MSS = {base['mss']} B, dữ liệu = {base['total_bytes'] / 1e6:g} MB, "
           f"băng thông = {base['bandwidth'] / 1e6:g} Mbit/s, RTO = {base['rto']} s. {extra}{tail}")
    width = int(fig.get_figwidth() * 15)
    fig.text(0.01, 0.005, textwrap.fill(txt, width), fontsize=8.5, color="#5f5e5a", ha="left", va="bottom")


def sweep_plot(ax, s, group, xscale=1.0, y="goodput", ytrans=mbps, theory=True):
    g = s[s.group == group]
    for sc in [k for k in COLOR if k in set(g.scenario)]:
        d = g[g.scenario == sc].sort_values("value")
        x = d["value"] * xscale
        ax.errorbar(x, ytrans(d[f"{y}_mean"]), yerr=ytrans(d[f"{y}_std"].fillna(0)), color=COLOR[sc],
                    marker=MARK[sc], ms=7, capsize=3, label=NAME[sc])
        if theory:
            ax.plot(x, ytrans(d["theory_goodput_mean"]), color=THEORY, ls="--", lw=1.4,
                    label="Lý thuyết min(B/RTT, băng thông, R_app)" if sc == "S1_nhe" or len(set(g.scenario)) == 1 else None)


def save(fig, name):
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(OUT / name, dpi=200)
    plt.close(fig)
    print("  ->", "plots/" + name)


# ----------------------------------------------------------------------------------------------
def fig_buffer(s, base):
    fig, ax = plt.subplots(figsize=(8, 5))
    sweep_plot(ax, s, "sweep_buffer", xscale=1 / 1024)
    ax.set_xscale("log", base=2)
    ax.set_xticks([8, 16, 32, 64, 128, 256], ["8", "16", "32", "64", "128", "256"])
    ax.set_xlabel("Dung lượng bộ đệm nhận B (KiB)")
    ax.set_ylabel("Goodput (Mbit/s)")
    ax.set_title("Hình 6. Goodput theo dung lượng bộ đệm nhận")
    ax.legend(loc="upper left")
    footer(fig, base, s, f"RTT = {base['rtt'] * 1000:g} ms. ")
    save(fig, "fig06_goodput_theo_buffer.png")


def fig_rtt(s, base):
    fig, ax = plt.subplots(figsize=(8, 5))
    sweep_plot(ax, s, "sweep_rtt", xscale=1000)
    ax.set_xlabel("RTT (ms)")
    ax.set_ylabel("Goodput (Mbit/s)")
    ax.set_title("Hình 7. Goodput theo RTT")
    ax.legend(loc="upper right")
    footer(fig, base, s, f"B = {base['buffer_size']} B. ")
    save(fig, "fig07_goodput_theo_rtt.png")


def fig_app_rate(s, base):
    g = s[s.group == "sweep_app_rate"].sort_values("value")
    x = g["value"] / 1000
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 7.5), sharex=True)
    a1.errorbar(x, g["goodput_mean"] / 1000, yerr=g["goodput_std"].fillna(0) / 1000, color=COLOR["S1_nhe"],
                marker="o", ms=7, capsize=3, label="Mô phỏng")
    a1.plot(x, g["theory_goodput_mean"] / 1000, color=THEORY, ls="--", lw=1.4, label="Lý thuyết min(B/RTT, R_app)")
    wl = (base["buffer_size"] // base["mss"]) * base["mss"] / base["rtt"] / 1000
    a1.axvline(wl, color=THEORY, lw=1, ls=":")
    a1.text(wl * 1.05, a1.get_ylim()[0] + 20, f"R_app = B/RTT\n≈ {wl:.0f} kB/s", fontsize=9, color="#5f5e5a")
    a1.set_ylabel("Goodput (kB/s)")
    a1.set_title("Hình 8. Tốc độ đọc của ứng dụng và nút cổ chai phía nhận")
    a1.legend(loc="upper left")
    a2.errorbar(x, g["avg_buffer_pct_mean"], yerr=g["avg_buffer_pct_std"].fillna(0), color=COLOR["S3_nang"],
                marker="s", ms=7, capsize=3, label="Mức chiếm bộ đệm nhận trung bình")
    a2.set_ylabel("Bộ đệm nhận bị chiếm (%)")
    a2.set_xlabel("Tốc độ ứng dụng đọc R_app (kB/s, thang log)")
    a2.set_xscale("log")
    a2.set_ylim(0, 100)
    a2.legend(loc="upper right")
    footer(fig, base, s, f"B = {base['buffer_size']} B, RTT = {base['rtt'] * 1000:g} ms. ")
    save(fig, "fig08_anh_huong_toc_do_doc.png")


def fig_loss(s, base):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.8))
    pct = lambda v: v  # noqa: E731
    sweep_plot(a1, s, "sweep_loss", xscale=100)
    a1.set_xlabel("Tỷ lệ mất gói mỗi chiều (%)")
    a1.set_ylabel("Goodput (Mbit/s)")
    a1.set_title("Hình 9a. Goodput theo tỷ lệ mất gói")
    a1.legend(loc="upper right", fontsize=9)
    sweep_plot(a2, s, "sweep_loss", xscale=100, y="timeout_count", ytrans=pct, theory=False)
    a2.set_xlabel("Tỷ lệ mất gói mỗi chiều (%)")
    a2.set_ylabel("Số lần hết thời gian chờ RTO")
    a2.set_title("Hình 9b. Số lần timeout")
    a2.legend(loc="upper left", fontsize=9)
    footer(fig, base, s, f"B = {base['buffer_size']} B, RTT = {base['rtt'] * 1000:g} ms. ")
    save(fig, "fig09_anh_huong_mat_goi.png")


def fig_read_interval(s, base):
    g = s[s.group == "sweep_read_interval"].sort_values("value")
    x = g["value"] * 1000
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.8))
    a1.errorbar(x, g["goodput_mean"] / 1000, yerr=g["goodput_std"].fillna(0) / 1000, color=COLOR["S3_nang"],
                marker="s", ms=7, capsize=3, label="Mô phỏng (S3)")
    a1.plot(x, g["theory_goodput_mean"] / 1000, color=THEORY, ls="--", lw=1.4, label="R_app = 100 kB/s")
    a1.set_xscale("log")
    a1.set_xlabel("Chu kỳ ứng dụng đọc (ms, thang log)")
    a1.set_ylabel("Goodput (kB/s)")
    a1.set_title("Hình 10a. Goodput khi ứng dụng đọc theo cục")
    a1.legend(loc="lower left")
    a2.errorbar(x, g["zero_window_time_mean"], yerr=g["zero_window_time_std"].fillna(0), color=COLOR["S3_nang"],
                marker="s", ms=7, capsize=3, label="Tổng thời gian rwnd = 0")
    a2.set_xscale("log")
    a2.set_xlabel("Chu kỳ ứng dụng đọc (ms, thang log)")
    a2.set_ylabel("Thời gian zero window (s)")
    a2.set_title("Hình 10b. Thời gian bên gửi bị chặn (rwnd = 0)")
    a2.legend(loc="upper left")
    footer(fig, base, s, f"B = {base['buffer_size']} B, RTT = {base['rtt'] * 1000:g} ms. ")
    save(fig, "fig10_chu_ky_doc.png")


def fig_scenarios(s, base):
    g = s[s.group == "scenarios"].set_index("scenario").loc[list(NAME)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.8))
    xs = range(len(g))
    labels = ["S1\nđọc nhanh", "S2\ntrung bình", "S3\nđọc chậm", "S4\ntạm dừng"]
    a1.bar(xs, g["goodput_mean"] / 1000, width=0.55, color=[COLOR[k] for k in g.index], label="Mô phỏng")
    a1.scatter(xs, g["theory_goodput_mean"] / 1000, marker="_", s=900, color="#3d3d3a", zorder=3,
               label="Giới hạn lý thuyết")
    for i, (v, th) in enumerate(zip(g["goodput_mean"] / 1000, g["theory_goodput_mean"] / 1000)):
        a1.text(i, max(v, th) + 14, f"{v:.0f}", ha="center", fontsize=10, color="#3d3d3a")
    a1.set_ylim(0, (g["theory_goodput_mean"].max() / 1000) * 1.2)
    a1.set_xticks(list(xs), labels)
    a1.set_ylabel("Goodput (kB/s)")
    a1.set_title("Hình 11a. Goodput 4 kịch bản")
    a1.legend(loc="upper right")
    a2.bar(xs, g["avg_buffer_pct_mean"], width=0.55, color=[COLOR[k] for k in g.index])
    for i, v in enumerate(g["avg_buffer_pct_mean"]):
        a2.text(i, v + 2, f"{v:.0f}%", ha="center", fontsize=10, color="#3d3d3a")
    a2.set_xticks(list(xs), labels)
    a2.set_ylim(0, 100)
    a2.set_ylabel("Bộ đệm nhận bị chiếm trung bình (%)")
    a2.set_title("Hình 11b. Mức chiếm bộ đệm nhận")
    a2.grid(axis="x", visible=False)
    a1.grid(axis="x", visible=False)
    footer(fig, base, s, f"B = {base['buffer_size']} B, RTT = {base['rtt'] * 1000:g} ms. ")
    save(fig, "fig11_so_sanh_kich_ban.png")


def fig_timeseries(s, base, sc, title, fname, t_max=None):
    p = ROOT / "results" / "raw" / f"timeseries_{sc}.csv"
    ts = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(10, 5.4))
    t_end = ts["time_s"].max() if t_max is None else t_max
    for key in ("in_flight", "rwnd", "buffer"):
        d = ts[ts.series == key].sort_values("time_s")
        t = list(d["time_s"]) + [t_end]
        v = list(d["value"] / 1024) + [d["value"].iloc[-1] / 1024]
        ax.step(t, v, where="post", color=TS_COLOR[key], ls=TS_STYLE[key], lw=1.8, label=TS_NAME[key])
    cfg = yaml.safe_load(open(ROOT / "configs" / "scenarios.yaml", encoding="utf-8"))["scenarios"][sc]
    if cfg.get("app_pause_at") is not None:
        a, d = cfg["app_pause_at"], cfg["app_pause_duration"]
        ax.axvspan(a, a + d, color="#f1efe8", zorder=0)
        ax.text(a + d / 2, base["buffer_size"] / 1024 * 0.8, "ứng dụng ngừng đọc", ha="center", fontsize=10,
                color="#5f5e5a")
    ev_style = {"event:probe": ("v", "#3d3d3a", "window probe"),
                "event:window_update": ("^", "#7f77dd", "window update")}
    for key, (mk, col, lab) in ev_style.items():
        e = ts[(ts.series == key) & (ts.time_s <= t_end)]
        if len(e):
            ax.scatter(e["time_s"], [base["buffer_size"] / 1024 * 1.08] * len(e), marker=mk, s=60,
                       color=col, zorder=5, label=f"{lab} ({len(e)} lần)")
    ax.axhline(base["buffer_size"] / 1024, color=THEORY, lw=1, ls="-.")
    ax.text(t_end, base["buffer_size"] / 1024, " B", va="center", fontsize=9.5, color="#5f5e5a")
    ax.set_xlim(0, t_end)
    ax.set_ylim(0, base["buffer_size"] / 1024 * 1.15)
    ax.set_xlabel("Thời gian (s)")
    ax.set_ylabel("KiB")
    ax.set_title(title)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3, fontsize=9.5)
    footer(fig, base, s, f"B = {base['buffer_size']} B, RTT = {base['rtt'] * 1000:g} ms. ", single_run=True)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(OUT / fname, dpi=200)
    plt.close(fig)
    print("  ->", "plots/" + fname)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    s, base = load()
    fig_buffer(s, base)
    fig_rtt(s, base)
    fig_app_rate(s, base)
    fig_loss(s, base)
    fig_read_interval(s, base)
    fig_scenarios(s, base)
    fig_timeseries(s, base, "S3_nang", "Hình 12. Diễn biến theo thời gian – S3 (ứng dụng đọc chậm)",
                   "fig12_chuoi_thoi_gian_S3.png", t_max=3.0)
    fig_timeseries(s, base, "S4_tam_dung", "Hình 13. Zero window khi ứng dụng tạm dừng đọc – S4",
                   "fig13_chuoi_thoi_gian_S4.png", t_max=9.0)


if __name__ == "__main__":
    main()
