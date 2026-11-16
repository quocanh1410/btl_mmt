# Quy trình làm việc với Git/GitHub

## Lần đầu
```bash
git clone https://github.com/<owner>/<repo>.git
cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
pytest
```

## Mỗi công việc
1. Lấy (hoặc tạo) một **Issue** trên GitHub, gán cho mình, gắn label `P1`…`P4`.
2. Cập nhật `main` và tạo nhánh:
   ```bash
   git checkout main && git pull
   git checkout -b p2/receiver-rwnd        # pX/mo-ta-ngan
   ```
3. Code + test. Commit nhỏ, thông điệp rõ:
   ```
   feat(receiver): tính rwnd và gửi trong ACK
   fix(sender): không gửi khi rwnd = 0
   test(channel): kiểm tra tỷ lệ mất gói với seed cố định
   docs(report): viết mục 5.2 bộ đệm nhận
   ```
4. `git push -u origin p2/receiver-rwnd` → mở **Pull Request** vào `main`, ghi `Closes #<số issue>`.
5. Ít nhất **1 người khác review và approve**; CI (pytest) phải xanh → P1 (hoặc người viết) merge.
6. Ghi 1 dòng vào `docs/NHAT_KY_DONG_GOP.md` (có thể ngay trong PR đó).

## Quy tắc
- Không push thẳng vào `main` (P1 bật *branch protection*: Settings → Branches → Add rule → `main` → Require a pull request + 1 approval).
- Không commit `.venv/`, file build, video lớn (> 50 MB → để link Google Drive trong `demo/README.md`).
- Không commit mật khẩu, token, khóa API.
- File kết quả trong `results/raw/` chỉ commit **bản chạy cuối** để báo cáo dùng, kèm config và seed.
- Xung đột (conflict): `git pull origin main` vào nhánh của mình, sửa, test lại, push.

## Commit history = minh chứng đóng góp
Giảng viên có thể điều chỉnh điểm cá nhân theo bằng chứng đóng góp. Mỗi người tự commit bằng tài khoản của mình
(cấu hình `git config user.name` / `user.email` đúng), không nhờ người khác commit hộ.
