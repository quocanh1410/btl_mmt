# Báo cáo (15–25 trang, không tính phụ lục)

Mỗi người viết section của mình bằng Markdown trong `sections/`. P4 ghép và xuất PDF, ví dụ:
```bash
pandoc report/sections/*.md -o report/ET4230_D09_BaoCao.pdf --pdf-engine=xelatex -V mainfont="Times New Roman" --toc
```
(hoặc chuyển sang Word/LaTeX nếu nhóm thích – thống nhất ở tuần 4).
Hình lấy từ `plots/`, luôn ghi: tham số, số seed, đơn vị.

| File | Nội dung | Người viết | Trang (dự kiến) |
|---|---|---|---|
| 01_muc_tieu.md | Mục tiêu, phạm vi, phân biệt flow vs congestion control | P1 | 1–2 |
| 02_ly_thuyet.md | Sliding window, seq/ACK, advertised window, zero window, persist timer, SWS; tài liệu | P1 | 3–4 |
| 03_kien_truc_mo_phong.md | Kiến trúc, engine sự kiện, mô hình kênh, giả định | P3 | 2–3 |
| 04_mo_hinh_ben_gui.md | Thuật toán bên gửi, RTO, probe | P1 | 2 |
| 05_mo_hinh_ben_nhan.md | Bộ đệm, rwnd, ứng dụng đọc, window update | P2 | 2 |
| 06_thiet_ke_thi_nghiem.md | Kịch bản, tham số cố định/biến đổi, chỉ tiêu & công thức, seed | P4 | 2 |
| 07_phan_tich.md | Kết quả, biểu đồ, so sánh lý thuyết, receiver bottleneck | P4 + P2 | 4–6 |
| 08_doi_chieu_tcp_that.md | Thí nghiệm TCP thật + Wireshark, so sánh định tính | P3 | 2 |
| 09_han_che_ket_luan.md | Hạn chế, bài học, kết luận | P1 + tất cả | 1–2 |
| 10_tai_lieu_tham_khao.md | RFC 9293, RFC 6298, RFC 1122 (SWS), giáo trình… | P1 | 1 |
| 11_phu_luc.md | Phân công, nhật ký, khai báo AI, hướng dẫn chạy | P1 | – |
