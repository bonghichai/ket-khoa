---
name: ket-khoa
description: >-
  Lấy khóa / token / mật khẩu từ két Infisical để chạy script hoặc gọi API mà không in khóa ra màn hình — trên máy
  riêng, Claude cloud, Codex cloud. Dùng khi việc cần khóa API, token, mật khẩu FTP / DB… Không in giá trị khóa.
---

# Két khóa (Infisical) — lấy khóa an toàn

Script `ket.py` (Python 3, chỉ thư viện chuẩn). Trên cloud: `python3 /opt/ket-khoa/ket.py …` (setup script của môi
trường đã tải về). Trên máy riêng: xem sổ tay dự án để biết đường dẫn.

## Lệnh

```bash
python3 /opt/ket-khoa/ket.py kiem                         # vào được két chưa, vé đọc được ngăn nào, mỗi ngăn bao nhiêu khóa
python3 /opt/ket-khoa/ket.py ten <ngăn>[/thư-mục]          # TÊN khóa (không có giá trị)
python3 /opt/ket-khoa/ket.py chay <ngăn>[/thư-mục] [...] -- <lệnh>   # chạy lệnh, khóa thành biến môi trường (tên khóa = tên biến)
python3 /opt/ket-khoa/ket.py ghi-file <ngăn>[/thư-mục] <TÊN> /tmp/khoa.json   # khóa dạng file; dùng xong phải xóa
```

Ví dụ: `python3 /opt/ket-khoa/ket.py chay <ngăn> -- bash -c 'curl -s -H "Authorization: Bearer $TEN_KHOA" https://…'`
Chưa biết khóa nằm ngăn nào → `kiem` rồi `ten <ngăn>`; sổ tay (`AGENTS.md`) của dự án có thể ghi rõ hơn.

**Trong script** (lấy khóa ngay trong chương trình, không in, không ghi file):
- Python: `sys.path.insert(0, '<thư mục ket-khoa>'); import ket; k = ket.lay('<ngăn>[/thư-mục]', 'TEN_KHOA')`
- Node (≥ 18): `const { layKhoa } = await import(pathToFileURL('<thư mục ket-khoa>/ket.mjs').href); const k = await layKhoa('<ngăn>', 'TEN_KHOA');`
- Script CommonJS cần khóa dạng file ngay lập tức: chạy `ket.py ghi-file` ra file tạm, đọc xong xóa ngay.

## Luật (bắt buộc)

1. **Không in, echo, ghi log, chép vào code / commit / tin nhắn giá trị khóa.** Chỉ dùng `chay` hoặc `ghi-file`; file ghi
   ra phải xóa ngay sau khi dùng. Script không có lệnh in giá trị khóa — cố ý.
2. **Có khóa ≠ được làm.** Việc GHI lên hệ thống thật (deploy, sửa server, gửi tin cho khách, sửa workflow đang chạy, đổi
   DNS…) vẫn phải theo luật của sổ tay dự án và được chủ dự án cho phép rõ.
3. Ngăn nào vé không được cấp thì không hiện / bị chặn — **đúng thiết kế**, đừng tìm khóa ở chỗ khác.
4. Vé chỉ đọc: không thêm / sửa khóa trong két. Cần khóa mới hay đổi khóa → báo chủ dự án.
5. Cloud chỉ ra Internet bằng HTTPS: SSH / FTP / MySQL trực tiếp thường không chạy được từ cloud.
6. Script tự viết gọi trang sau Cloudflare phải đặt User-Agent riêng (Cloudflare hay chặn `Python-urllib` mặc định).

## Lỗi thường gặp

- **401** — máy riêng: thiếu / hỏng file vé; Claude cloud: môi trường chưa có «Thông tin bí mật cho mạng» (Bearer) cho tên
  miền két; Codex cloud: thiếu Network secret `INFISICAL_TOKEN` hoặc chưa bật Internet cho tên miền két → báo chủ dự án.
- **Không có `/opt/ket-khoa/ket.py`** — setup script của môi trường chưa có dòng cài (xem `README.md`).
- **Không kết nối được** — cloud chưa cho phép tên miền két, hoặc máy chủ két đang lỗi.
