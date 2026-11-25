# ET4230 – Đề 09: TCP Flow Control (Sliding Window & Receiver Window)

Mô phỏng sự kiện rời rạc (discrete-event) bên gửi / bên nhận TCP ở mức trừu tượng:
sequence/ACK tích lũy, bộ đệm nhận, **advertised window (rwnd)**, hành vi khi bộ đệm đầy
(zero window + persist/probe). Mục tiêu chính: minh họa và đo **phía nhận trở thành nút cổ chai**.



## Thành viên & phân công (tóm tắt — chi tiết ở [docs/PHAN_CONG.md](docs/PHAN_CONG.md))

| Mã | Thành viên | Vai trò chính | Thư mục / file sở hữu |
|----|-----------|---------------|------------------------|
| P1 | Quốc Anh | Code: **Bên gửi** + tích hợp; thí nghiệm RTT, mất gói | `src/tcpfc/sender.py`, `src/tcpfc/simulation.py` |
| P2 | Quân | Code: **Bên nhận**, rwnd, **chỉ tiêu đo**; thí nghiệm buffer, tốc độ đọc | `src/tcpfc/receiver.py`, `src/tcpfc/metrics.py` |
| P3 | Đức | Code: **Kênh**, engine, **chạy thí nghiệm & vẽ biểu đồ**, demo TCP thật | `engine.py`, `channel.py`, `scripts/`, `configs/`, `demo/` |
| P4 | Tiến | **Báo cáo, slide** | `report/`, `docs/` |

## Cấu trúc thư mục

```
.
├── src/tcpfc/          # mã nguồn mô phỏng (package Python)
│   ├── engine.py       # bộ lập lịch sự kiện (P3)
│   ├── channel.py      # kênh: trễ một chiều, mất gói (P3)
│   ├── segment.py      # cấu trúc Segment / Ack dùng chung (cả nhóm – sửa phải qua PR)
│   ├── sender.py       # bên gửi: sliding window, RTO, persist timer (P1)
│   ├── receiver.py     # bên nhận: buffer, rwnd, app read (P2)
│   ├── metrics.py      # ghi log & tính chỉ tiêu (P2)
│   └── simulation.py   # ghép các khối, chạy 1 lần mô phỏng (P1)
├── configs/            # kịch bản YAML (P3)
├── scripts/            # run_all.py (chạy tất cả), run_once.py, run_experiments.py, plot_results.py (P3)
├── tests/              # kiểm thử pytest (mỗi người viết test cho module của mình)
├── results/            # summary.csv (mean/std), raw/*.csv mỗi lần chạy, chuỗi thời gian (sinh tự động)
├── plots/              # biểu đồ PNG/PDF (sinh tự động)
├── report/             # báo cáo (P4 viết)
├── demo/               # demo TCP thật 2 máy + Wireshark, pcap, ảnh chụp (P3)
└── docs/               # MO_TA_KY_THUAT.md, phân công, giao diện module, quy trình git, nhật ký
```

## Chạy nhanh (3 lệnh)

Yêu cầu: **Python ≥ 3.10** (Windows / macOS / Linux).

```bash
git clone https://github.com/quocanh1410/btl_mmt.git && cd btl_mmt
pip install -r requirements.txt
python scripts/run_all.py
```

`run_all.py` lần lượt: chạy 26 kiểm thử → chạy toàn bộ thí nghiệm (51 cấu hình × 5 seed, khoảng 10 giây)
→ vẽ 8 biểu đồ vào `plots/` → ghi `results/ENVIRONMENT.md`. Kết quả tổng hợp: `results/summary.csv`.

> Nếu máy có nhiều bản Python, dùng `python3` thay cho `python`. Muốn môi trường riêng:
> `python -m venv .venv` rồi `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`) trước khi `pip install`.

### Chạy 1 lần, thử tham số tùy ý

```bash
python scripts/run_once.py                                    # cấu hình mặc định configs/base.yaml
python scripts/run_once.py --scenario S4_tam_dung --plot      # kịch bản S4, vẽ plots/run_once.png
python scripts/run_once.py --set app_read_rate=2e5 rtt=0.05 loss_rate=0.01 --seed 3
python scripts/trace.py --pause                               # in từng bước bằng lời (để hiểu code chạy thế nào)
```

Các tham số (byte, giây, byte/giây) nằm trong `configs/base.yaml`; kịch bản và tham số quét trong
`configs/scenarios.yaml`.

### Từng bước riêng lẻ

```bash
python -m pytest -q                      # kiểm thử
python scripts/run_experiments.py        # thí nghiệm -> results/summary.csv, results/raw/*.csv
python scripts/plot_results.py           # biểu đồ -> plots/
```

### Demo TCP thật trên 2 máy + Wireshark

Xem [demo/README.md](demo/README.md).

## Kết quả chính

| Kịch bản | Tốc độ đọc ứng dụng | Goodput | Giới hạn lý thuyết | Bộ đệm nhận bị chiếm |
|---|---|---|---|---|
| S1 đọc nhanh | 10 MB/s | 618 kB/s | 642 kB/s (B/RTT) | 0,5 % |
| S2 trung bình | 650 kB/s | 475 kB/s | 642 kB/s | 11 % |
| S3 đọc chậm | 100 kB/s | 99,5 kB/s | 100 kB/s (**bên nhận**) | 77 % |
| S4 tạm dừng đọc 5 s | 100 kB/s | 66 kB/s | – | 84 %, rwnd = 0 trong 4,9 s, 2 probe |

Mô tả mô hình, giả định, công thức chỉ tiêu và nhận xét chi tiết: [docs/MO_TA_KY_THUAT.md](docs/MO_TA_KY_THUAT.md).

| Biểu đồ | Nội dung |
|---|---|
| `fig06` | Goodput theo dung lượng bộ đệm nhận |
| `fig07` | Goodput theo RTT |
| `fig08` | Goodput và mức chiếm bộ đệm theo tốc độ đọc của ứng dụng |
| `fig09` | Goodput và số lần timeout theo tỷ lệ mất gói |
| `fig10` | Ứng dụng đọc theo cục: goodput và thời gian zero window |
| `fig11` | So sánh 4 kịch bản |
| `fig12` | Diễn biến in-flight / rwnd / bộ đệm theo thời gian – S3 |
| `fig13` | Zero window, probe, window update khi ứng dụng tạm dừng – S4 |

## Quy trình làm việc

Đọc [docs/QUY_TRINH_GIT.md](docs/QUY_TRINH_GIT.md) trước khi commit. Tóm tắt:
không push thẳng vào `main`; mỗi việc = 1 issue + 1 nhánh `pX/ten-viec` + 1 Pull Request có ít nhất 1 người review.

## Sản phẩm nộp (theo đề)

- [ ] Báo cáo PDF 15–25 trang (`report/`)
- [ ] Mã nguồn + config + dữ liệu CSV + script vẽ (repo này)
- [ ] Video demo 3–5 phút / pcap / log (`demo/`)
- [ ] Slide bảo vệ
- [ ] Bảng phân công + nhật ký đóng góp ([docs/NHAT_KY_DONG_GOP.md](docs/NHAT_KY_DONG_GOP.md))
- [ ] Khai báo sử dụng AI ([docs/KHAI_BAO_AI.md](docs/KHAI_BAO_AI.md))
- [ ] File nén `ET4230_HK[ky]_N[so-nhom]_D09.zip` (dùng `scripts/make_submission.sh`)
