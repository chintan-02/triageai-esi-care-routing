import { spawnSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';

const raw = process.env.VITE_API_BASE_URL;
let api;
try { api = new URL(raw); } catch { throw new Error('Set VITE_API_BASE_URL to the HTTPS backend origin.'); }
if (api.protocol !== 'https:' || api.username || api.password || api.pathname !== '/' || api.search || api.hash ||
    api.hostname === 'localhost' || api.hostname.endsWith('.localhost') || api.hostname === '127.0.0.1') {
  throw new Error('VITE_API_BASE_URL must be a public HTTPS origin without credentials, path or query.');
}
if (process.env.VITE_USE_MOCK_API !== 'false') throw new Error('Netlify requires VITE_USE_MOCK_API=false.');
const build = spawnSync('npm', ['run', 'build'], { stdio: 'inherit' });
if (build.status !== 0) process.exit(build.status ?? 1);
const csp = [
  "default-src 'self'", "script-src 'self'", "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' https://fonts.gstatic.com", "img-src 'self' data: blob:", `connect-src 'self' ${api.origin}`,
  "media-src 'self' blob:", "object-src 'none'", "base-uri 'none'", "frame-ancestors 'none'", "form-action 'none'",
].join('; ');
writeFileSync('dist/_headers', `/*\n  Content-Security-Policy: ${csp}\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), geolocation=(), microphone=(self)\n  X-Frame-Options: DENY\n\n/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n`);
