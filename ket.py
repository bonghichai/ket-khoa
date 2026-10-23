#!/usr/bin/env python3
"""ket — lấy khóa từ két Infisical mà KHÔNG BAO GIỜ in giá trị khóa ra màn hình.

Tự nhận ra đang chạy ở đâu:
  - Biến INFISICAL_TOKEN có giá trị (vd Codex cloud «Network secret»: biến chỉ chứa chữ giữ chỗ, proxy tự thay vé thật)
    → gửi kèm làm Bearer.
  - Có file vé Universal Auth (biến KET_VE_FILE, hoặc «veFile» trong ket-cau-hinh.local.json cạnh script — file này
    không đưa lên git) → đăng nhập bằng vé đó.
  - Không có gì → gửi không kèm vé (Claude cloud: «Thông tin bí mật cho mạng» của môi trường tự gắn vé).
Địa chỉ két: biến KET_URL, hoặc «url» trong ket-cau-hinh.local.json, mặc định https://keys.nhiemvu68.com.

Lệnh (Python 3, chỉ dùng thư viện chuẩn):
  python3 ket.py kiem                                    vào được két chưa, vé đọc được ngăn nào (không in khóa)
  python3 ket.py ten <ngăn>[/thư-mục]                    liệt kê TÊN khóa
  python3 ket.py chay <ngăn>[/thư-mục] [...] -- <lệnh>   chạy lệnh, khóa thành biến môi trường (tên khóa = tên biến)
  python3 ket.py ghi-file <ngăn>[/thư-mục] <TÊN> <file> [--de]   ghi khóa dạng file (SSH key, JSON), quyền 600
Ví dụ:
  python3 ket.py chay <ngăn> -- bash -c 'curl -s -H "Authorization: Bearer $TEN_KHOA" https://api.vi-du.com/...'
  python3 ket.py ghi-file <ngăn>/<thư-mục> TEN_KHOA_JSON /tmp/khoa.json      (dùng xong: rm /tmp/khoa.json)
Không có lệnh in giá trị khóa — cố ý.
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:  # noqa: BLE001
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(HERE, 'ket-cau-hinh.local.json'), encoding='utf-8') as _f:
        CFG = json.load(_f)
except Exception:  # noqa: BLE001
    CFG = {}
BASE = (os.environ.get('KET_URL') or CFG.get('url') or 'https://keys.nhiemvu68.com').rstrip('/')
VE_FILE = os.environ.get('KET_VE_FILE') or CFG.get('veFile') or ''
ENV = os.environ.get('KET_MOI_TRUONG') or CFG.get('moiTruong') or 'prod'
UA = 'ket-khoa/1.0'  # Cloudflare hay chặn User-Agent mặc định «Python-urllib»


def die(msg, code=2):
    print('ket: ' + msg, file=sys.stderr)
    sys.exit(code)


def http(method, path, params=None, body=None, headers=None):
    url = BASE + path + ('?' + urllib.parse.urlencode(params) if params else '')
    data = json.dumps(body).encode() if body is not None else None
    h = {'User-Agent': UA, 'Accept': 'application/json'}
    if data is not None:
        h['Content-Type'] = 'application/json'
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    last = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.status, json.loads(r.read() or b'{}')
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read() or b'{}')
            except Exception:  # noqa: BLE001
                return e.code, {}
        except Exception as e:  # noqa: BLE001  (mạng chập chờn: thử lại)
            last = e
    die(f'không kết nối được {BASE} ({type(last).__name__}). Trên cloud: tên miền của két phải được phép '
        f'(Claude: có «Thông tin bí mật cho mạng»; Codex: bật Internet cho AI + thêm tên miền).')


_AUTH = None


def auth():
    """Trả (header, nơi chạy). Không in vé."""
    global _AUTH
    if _AUTH:
        return _AUTH
    tok = os.environ.get('INFISICAL_TOKEN', '').strip()
    if tok:
        _AUTH = ({'Authorization': 'Bearer ' + tok}, 'biến INFISICAL_TOKEN')
    elif VE_FILE and os.path.exists(VE_FILE):
        with open(VE_FILE, encoding='utf-8') as f:
            ve = json.load(f)
        code, b = http('POST', '/api/v1/auth/universal-auth/login',
                       body={'clientId': ve['clientId'], 'clientSecret': ve['clientSecret']})
        if code != 200 or 'accessToken' not in b:
            die(f'file vé không đăng nhập được (HTTP {code}).')
        _AUTH = ({'Authorization': 'Bearer ' + b['accessToken']}, 'file vé trên máy')
    else:
        _AUTH = ({}, 'cổng cloud tự gắn vé')
    return _AUTH


def why_401():
    return ('két từ chối (401) — đang chạy: ' + auth()[1] + '. Máy riêng: thiếu / hỏng file vé; Claude cloud: môi trường '
            'chưa có «Thông tin bí mật cho mạng» cho tên miền két; Codex cloud: thiếu Network secret INFISICAL_TOKEN.')


_PROJECTS = None


def projects():
    """{tên ngăn: mã} — chỉ những ngăn vé này được đọc (hỏi két lúc chạy, không ghi sẵn trong code)."""
    global _PROJECTS
    if _PROJECTS is None:
        code, b = http('GET', '/api/v1/projects', headers=auth()[0], params={'type': 'secret-manager'})
        if code == 401:
            die(why_401())
        if code != 200:
            die(f'két trả lỗi HTTP {code} khi hỏi danh sách ngăn.')
        _PROJECTS = {p['slug']: p['id'] for p in b.get('projects', [])}
    return _PROJECTS


def split_spec(spec):
    slug, _, folder = spec.partition('/')
    ps = projects()
    if slug not in ps:
        die(f'ngăn «{slug}» không có, hoặc vé này không được cấp ngăn đó. Vé đọc được: ' + (', '.join(sorted(ps)) or '(không ngăn nào)'))
    return slug, ps[slug], ('/' + folder.strip('/')) if folder.strip('/') else '/'


def fetch(spec, values=True):
    slug, pid, folder = split_spec(spec)
    code, b = http('GET', '/api/v4/secrets', headers=auth()[0], params={
        'projectId': pid, 'environment': ENV, 'secretPath': folder,
        'viewSecretValue': str(values).lower(), 'expandSecretReferences': 'true'})
    if code == 200:
        return {s['secretKey']: (s.get('secretValue') if values else None) for s in b.get('secrets', [])}
    if code == 401:
        die(why_401())
    if code == 403:
        die(f'vé này không được đọc «{spec}» (403).')
    if code == 404:
        die(f'không có thư mục «{folder}» trong ngăn «{slug}».')
    die(f'két trả lỗi HTTP {code} khi đọc {spec}: {str(b.get("message", ""))[:150]}')


def lay(spec, ten):
    """Cho script Python: trả giá trị 1 khóa (không in). Lỗi → báo và thoát.
    Dùng: sys.path.insert(0, <thư mục ket-khoa>); import ket; k = ket.lay('ngan[/thu-muc]', 'TEN_KHOA')"""
    vals = fetch(spec, values=True)
    if ten not in vals:
        die(f'không có khóa {ten} trong {spec}')
    return vals[ten]


def cmd_kiem(_args):
    ps = projects()
    print(f'Két: {BASE} — đang chạy: {auth()[1]} — vé đọc được {len(ps)} ngăn')
    for slug, pid in sorted(ps.items()):
        code, b = http('GET', '/api/v4/secrets', headers=auth()[0], params={
            'projectId': pid, 'environment': ENV, 'secretPath': '/', 'recursive': 'true', 'viewSecretValue': 'false'})
        print(f'  {slug:<14} ' + (f'{len(b.get("secrets", []))} khóa' if code == 200 else f'lỗi HTTP {code}'))
    return 0


def cmd_ten(args):
    if not args:
        die('cần <ngăn>[/thư-mục]')
    for n in sorted(fetch(args[0], values=False)):
        print(n)
    return 0


def cmd_chay(args):
    if '--' not in args:
        die('cú pháp: ket.py chay <ngăn>[/thư-mục] [...] -- <lệnh>')
    i = args.index('--')
    specs, command = args[:i], args[i + 1:]
    if not specs or not command:
        die('cần ít nhất 1 ngăn và 1 lệnh')
    env, origin = dict(os.environ), {}
    for spec in specs:
        for k, v in fetch(spec, values=True).items():
            if k in origin and origin[k] != spec:
                print(f'ket: cảnh báo — khóa {k} có ở cả {origin[k]} và {spec}, dùng bản của {spec}', file=sys.stderr)
            env[k] = v
            origin[k] = spec
    if os.name == 'nt' and command[0] in ('bash', 'sh'):
        # Windows: «bash» trơn có thể là WSL — WSL không nhận biến môi trường của Windows → dùng Git Bash.
        for git_bash in ('C:/Program Files/Git/bin/bash.exe', 'C:/Program Files (x86)/Git/bin/bash.exe'):
            if os.path.exists(git_bash):
                command = [git_bash] + command[1:]
                break
    try:
        return subprocess.call(command, env=env)
    except FileNotFoundError:
        die(f'không tìm thấy lệnh «{command[0]}»')


def cmd_ghi_file(args):
    force = '--de' in args
    args = [a for a in args if a != '--de']
    if len(args) != 3:
        die('cú pháp: ket.py ghi-file <ngăn>[/thư-mục] <TÊN> <file> [--de]')
    spec, name, path = args
    vals = fetch(spec, values=True)
    if name not in vals:
        die(f'không có khóa {name} trong {spec}')
    if os.path.exists(path) and not force:
        die(f'file {path} đã có — thêm --de nếu muốn ghi đè')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
        f.write(vals[name])
    try:
        os.chmod(path, 0o600)
    except Exception:  # noqa: BLE001
        pass
    print(f'đã ghi {name} vào {path} ({len(vals[name])} ký tự, quyền 600) — dùng xong thì XÓA file này')
    return 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help', 'help'):
        print(__doc__)
        return 0
    cmd, args = sys.argv[1], sys.argv[2:]
    table = {'kiem': cmd_kiem, 'ten': cmd_ten, 'chay': cmd_chay, 'ghi-file': cmd_ghi_file}
    if cmd not in table:
        die(f'lệnh lạ «{cmd}». Có: kiem, ten, chay, ghi-file (không có lệnh in giá trị khóa — cố ý)')
    return table[cmd](args)


if __name__ == '__main__':
    sys.exit(main())
