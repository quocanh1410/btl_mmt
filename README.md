# ET4230 – Đề 09: TCP Flow Control (Sliding Window & Receiver Window)

Mô phỏng sự kiện rời rạc (discrete-event) bên gửi / bên nhận TCP ở mức trừu tượng:
sequence/ACK tích lũy, bộ đệm nhận, **advertised window (rwnd)**, hành vi khi bộ đệm đầy
(zero window + persist/probe). Mục tiêu chính: minh họa và đo **phía nhận trở thành nút cổ chai**.



## Thành viên & phân công (tóm tắt — chi tiết ở [docs/PHAN_CONG.md](docs/PHAN_CONG.md))

| Mã | Thành viên | Vai trò chính | Thư mục / file sở hữu |
|----|-----------|---------------|------------------------|
| P1 | _(điền tên – MSSV)_ | Code: **Bên gửi** + tích hợp; thí nghiệm RTT, mất gói | `src/tcpfc/sender.py`, `src/tcpfc/simulation.py` |
| P2 | _(điền tên – MSSV)_ | Code: **Bên nhận**, rwnd, **chỉ tiêu đo**; thí nghiệm buffer, tốc độ đọc | `src/tcpfc/receiver.py`, `src/tcpfc/metrics.py` |
| P3 | _(điền tên – MSSV)_ | Code: **Kênh**, engine, **chạy thí nghiệm & vẽ biểu đồ**, demo TCP thật | `engine.py`, `channel.py`, `scripts/`, `configs/`, `demo/` |
| P4 | _(điền tên – MSSV)_ | **Báo cáo, slide, hồ sơ nộp** (không code) | `report/`, `docs/` |

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
├── scripts/            # chạy hàng loạt, vẽ biểu đồ (P3)
├── tests/              # kiểm thử pytest (mỗi người viết test cho module của mình)
├── results/raw/        # CSV/JSON kết quả thô (sinh tự động, có commit bản cuối)
├── plots/              # biểu đồ PNG/PDF (sinh tự động)
├── report/             # báo cáo (P4 viết)
├── demo/               # video, pcap, ảnh chụp minh chứng (P3)
└── docs/               # phân công, giao diện module, quy trình git, nhật ký, ghi chú kỹ thuật (ghi_chu/)
```

## Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                 # cài package tcpfc ở chế độ dev
```

Yêu cầu: Python ≥ 3.10. Ghi phiên bản thực tế dùng khi chạy thí nghiệm vào `results/ENVIRONMENT.md`.

## Chạy

```bash
pytest                                           # kiểm thử
python scripts/run_once.py configs/base.yaml     # chạy 1 lần, in chỉ tiêu
python scripts/run_experiments.py                # chạy tất cả kịch bản × 5 seed -> results/raw/
python scripts/plot_results.py                   # vẽ biểu đồ -> plots/
```

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
