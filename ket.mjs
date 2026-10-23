// ket.mjs — lấy khóa từ két Infisical cho script Node, KHÔNG BAO GIỜ in giá trị khóa. Cùng cách nhận vé với ket.py:
//   biến INFISICAL_TOKEN (Codex cloud) → file vé (KET_VE_FILE hoặc «veFile» trong ket-cau-hinh.local.json cạnh file này)
//   → không vé (Claude cloud: cổng môi trường tự gắn vé).
// Dùng (Node ≥ 18):
//   const { layKhoa } = await import('<thư mục ket-khoa>/ket.mjs');   // Windows: import(pathToFileURL(...).href)
//   const k = await layKhoa('ngan[/thu-muc]', 'TEN_KHOA');           // chuỗi giá trị; lỗi → ném Error (câu lỗi không chứa khóa)
//   await layNgan('ngan[/thu-muc]')   → { TEN: giá trị, … }
//   await layTatCa()                  → [{ ngan, thuMuc, ten, giaTri }] mọi ngăn vé đọc được (cho bộ quét lộ khóa)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
let CFG = {};
try { CFG = JSON.parse(fs.readFileSync(path.join(HERE, 'ket-cau-hinh.local.json'), 'utf8')); } catch { /* không có cấu hình riêng */ }
const BASE = (process.env.KET_URL || CFG.url || 'https://keys.nhiemvu68.com').replace(/\/+$/, '');
const VE_FILE = process.env.KET_VE_FILE || CFG.veFile || '';
const ENV = process.env.KET_MOI_TRUONG || CFG.moiTruong || 'prod';
const UA = 'ket-khoa-node/1.0';   // Cloudflare hay chặn User-Agent mặc định của thư viện

const loi = (msg) => new Error('ket: ' + msg);

async function http(method, p, { params, body, headers } = {}) {
  const url = BASE + p + (params ? '?' + new URLSearchParams(params) : '');
  let last;
  for (let i = 0; i < 3; i++) {
    try {
      const r = await fetch(url, {
        method,
        headers: { 'User-Agent': UA, Accept: 'application/json', ...(body ? { 'Content-Type': 'application/json' } : {}), ...headers },
        body: body ? JSON.stringify(body) : undefined,
        signal: AbortSignal.timeout(40000),
      });
      let j = {};
      try { j = await r.json(); } catch { /* không phải JSON */ }
      return [r.status, j];
    } catch (e) { last = e; }   // mạng chập chờn: thử lại
  }
  throw loi(`không kết nối được ${BASE} (${last?.name || 'lỗi mạng'}). Trên cloud: tên miền của két phải được phép.`);
}

let _auth;
async function auth() {
  if (_auth) return _auth;
  const tok = (process.env.INFISICAL_TOKEN || '').trim();
  if (tok) return (_auth = [{ Authorization: 'Bearer ' + tok }, 'biến INFISICAL_TOKEN']);
  if (VE_FILE && fs.existsSync(VE_FILE)) {
    const ve = JSON.parse(fs.readFileSync(VE_FILE, 'utf8'));
    const [code, b] = await http('POST', '/api/v1/auth/universal-auth/login', { body: { clientId: ve.clientId, clientSecret: ve.clientSecret } });
    if (code !== 200 || !b.accessToken) throw loi(`file vé không đăng nhập được (HTTP ${code}).`);
    return (_auth = [{ Authorization: 'Bearer ' + b.accessToken }, 'file vé trên máy']);
  }
  return (_auth = [{}, 'cổng cloud tự gắn vé']);
}
const why401 = (noi) => `két từ chối (401) — đang chạy: ${noi}. Máy riêng: thiếu / hỏng file vé; Claude cloud: môi trường chưa có `
  + '«Thông tin bí mật cho mạng» cho tên miền két; Codex cloud: thiếu Network secret INFISICAL_TOKEN.';

let _ngan;
/** { tên ngăn: mã } — chỉ những ngăn vé này đọc được. */
export async function ngan() {
  if (_ngan) return _ngan;
  const [h, noi] = await auth();
  const [code, b] = await http('GET', '/api/v1/projects', { headers: h, params: { type: 'secret-manager' } });
  if (code === 401) throw loi(why401(noi));
  if (code !== 200) throw loi(`két trả lỗi HTTP ${code} khi hỏi danh sách ngăn.`);
  _ngan = Object.fromEntries((b.projects || []).map((p) => [p.slug, p.id]));
  return _ngan;
}

const cache = new Map();
export async function layNgan(spec) {
  if (cache.has(spec)) return cache.get(spec);
  const [slug, ...rest] = spec.split('/');
  const folder = '/' + rest.join('/').replace(/^\/+|\/+$/g, '');
  const ps = await ngan();
  if (!ps[slug]) throw loi(`ngăn «${slug}» không có, hoặc vé này không được cấp ngăn đó. Vé đọc được: ${Object.keys(ps).sort().join(', ') || '(không ngăn nào)'}`);
  const [h, noi] = await auth();
  const [code, b] = await http('GET', '/api/v4/secrets', {
    headers: h, params: { projectId: ps[slug], environment: ENV, secretPath: folder, viewSecretValue: 'true', expandSecretReferences: 'true' },
  });
  if (code === 401) throw loi(why401(noi));
  if (code === 403) throw loi(`vé này không được đọc «${spec}» (403).`);
  if (code === 404) throw loi(`không có thư mục «${folder}» trong ngăn «${slug}».`);
  if (code !== 200) throw loi(`két trả lỗi HTTP ${code} khi đọc ${spec}.`);
  const out = Object.fromEntries((b.secrets || []).map((s) => [s.secretKey, s.secretValue ?? '']));
  cache.set(spec, out);
  return out;
}

export async function layKhoa(spec, ten) {
  const vals = await layNgan(spec);
  if (!Object.prototype.hasOwnProperty.call(vals, ten)) throw loi(`không có khóa ${ten} trong ${spec}.`);
  return vals[ten];
}

/** Mọi khóa trong mọi ngăn vé đọc được (kể cả thư mục con) — chỉ để so / quét, không in. */
export async function layTatCa() {
  const ps = await ngan();
  const [h] = await auth();
  const out = [];
  for (const [slug, id] of Object.entries(ps)) {
    const [code, b] = await http('GET', '/api/v4/secrets', {
      headers: h, params: { projectId: id, environment: ENV, secretPath: '/', recursive: 'true', viewSecretValue: 'true' },
    });
    if (code !== 200) continue;
    for (const s of b.secrets || []) out.push({ ngan: slug, thuMuc: s.secretPath || '/', ten: s.secretKey, giaTri: s.secretValue ?? '' });
  }
  return out;
}
