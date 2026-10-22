#!/bin/bash
# Cài skill ket-khoa trên máy cloud (Claude cloud / Codex cloud). Setup script của môi trường gọi file này sau khi
# git clone repo về /opt/ket-khoa. Chỉ chép hướng dẫn skill cho mọi tài khoản trên máy — KHÔNG đụng khóa nào.
set -u
D="$(cd "$(dirname "$0")" && pwd)"
chmod -R a+rX "$D" 2>/dev/null || true
for h in /root /home/*; do
  [ -d "$h" ] || continue
  owner="$(stat -c %U "$h" 2>/dev/null || echo root)"
  for base in .claude .codex .agents; do
    new_base=0; [ -d "$h/$base" ] || new_base=1
    new_skills=0; [ -d "$h/$base/skills" ] || new_skills=1
    mkdir -p "$h/$base/skills/ket-khoa" && cp "$D/SKILL.md" "$h/$base/skills/ket-khoa/SKILL.md"
    # thư mục do script tạo ra phải thuộc về chủ máy, không để root giữ (Claude / Codex còn ghi vào đó)
    [ "$new_base" = 1 ] && chown "$owner" "$h/$base" 2>/dev/null
    [ "$new_skills" = 1 ] && chown "$owner" "$h/$base/skills" 2>/dev/null
    chown -R "$owner" "$h/$base/skills/ket-khoa" 2>/dev/null
  done
done
echo "ket-khoa: da cai tai $D — thu: python3 $D/ket.py kiem"
exit 0
