# ket-khoa

Một file `ket.py` (Python 3, thư viện chuẩn) để AI và script lấy khóa từ két **Infisical** **mà không in khóa ra màn
hình**. Repo **không chứa khóa, vé hay thông tin riêng nào** — khóa chỉ nằm trong két; mã ngăn được hỏi két lúc chạy.
Cách dùng + luật cho AI: `SKILL.md`.

## Cài trên máy cloud

**Setup script** của môi trường (Claude cloud: «Setup script»; Codex cloud: «Install script», thêm xuống cuối rồi Publish):

```bash
git clone --depth 1 https://github.com/bonghichai/ket-khoa.git /opt/ket-khoa || { sleep 5; rm -rf /opt/ket-khoa; git clone --depth 1 https://github.com/bonghichai/ket-khoa.git /opt/ket-khoa || true; }; [ -f /opt/ket-khoa/ket.py ] && bash /opt/ket-khoa/cai-dat-cloud.sh || echo "ket-khoa: chua tai duoc"
```

- Tải hỏng (proxy chập chờn) thì tự thử lại 1 lần.
- Hỏng cả 2 lần thì chỉ báo, KHÔNG làm setup script lỗi (setup script lỗi = phiên không mở được) — an toàn cả với
  script có `set -euo pipefail` (Codex).
- Phiên lỡ không có `/opt/ket-khoa`: AI tự tải vào thư mục tạm rồi dùng
  `git clone --depth 1 https://github.com/bonghichai/ket-khoa.git /tmp/ket-khoa && python3 /tmp/ket-khoa/ket.py kiem`.

Vé vào két (chỉ đọc) đặt ở:
- **Claude cloud** — «Thông tin bí mật cho mạng» (Network secrets): tên miền của két, kiểu Bearer.
- **Codex cloud** — Network secret tên `INFISICAL_TOKEN`, đích là tên miền của két; bật Internet cho AI với tên miền đó.

Thử: `python3 /opt/ket-khoa/ket.py kiem`.

## Máy riêng

Clone repo, tạo `ket-cau-hinh.local.json` cạnh `ket.py` (không đưa lên git):

```json
{ "veFile": "<đường dẫn file vé Universal Auth chỉ đọc>", "url": "https://<két của bạn>" }
```

hoặc đặt biến `KET_VE_FILE` / `KET_URL`. Thử: `python3 ket.py kiem`.
