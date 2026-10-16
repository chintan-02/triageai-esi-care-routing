# Frontend dependency remediation

The initial dependency audit reported 20 findings (5 moderate, 13 high,
2 critical). Compatible lockfile updates resolved the patched transitive
packages, including DOMPurify and React Router. The critical tinypool findings
were in the Vitest development/test dependency chain, not a deployed Python
inference service. React Router's reported advisory concerns RSC mode; this
application is a client-rendered Vite SPA. These distinctions affect exposure,
but do not remove the need to update dependencies.

Vitest is explicitly upgraded to 5.0.5. Tailwind 3.4.19 still depended on braces
3.0.3, for which GHSA-vfj7-8cjw-p6xm listed no patched release. Tailwind is upgraded
to 4.3.3 with its matching PostCSS plugin, removing that dependency chain. No
forced audit fixes, advisory suppressions or unsupported transitive overrides
are used.

The existing JavaScript Tailwind configuration remains loaded through @config.
Existing color values, shadows, default borders, placeholders, button cursors
and ring defaults are preserved by src/styles/tailwind-compat.css. Renamed
shadow, radius, blur and outline utilities follow the official v4 migration
mapping. Component structure and product behavior are unchanged. Generated CSS
selector coverage was checked against the previous build. Visual browser
verification is still required: test success and utility coverage are not
pixel-perfect visual validation.

Tailwind 4 requires modern browsers (Safari 16.4+, Chrome 111+, Firefox 128+).
The frontend declares the Vitest-supported Node engines; .nvmrc selects Node 24.
The development Dockerfile uses Node 24 and npm ci with the committed lockfile.
Local Vite dev/preview servers bind loopback by default; Compose explicitly
binds its container dev server to 0.0.0.0.

## Mac update

Stop the frontend dev server first. From the repository root, while on
feat/cloud-run-deployment, run git pull --ff-only. Then:

```bash
cd app/frontend/react_app
node --version
npm ci
npm audit
npm test
npm run lint
npm run build
```

Use Node 24, or a supported Node 22 release at least 22.12.0. If nvm is installed,
`nvm install` followed by `nvm use` reads the committed .nvmrc. Restart Vite using
the previously configured API URL and repeat the synthetic intake/review/PDF
workflow. Check the login screen, dashboard, intake, detail and report screens
at desktop and mobile widths.

## Verification

At remediation time npm audit reported zero findings. This is a point-in-time
advisory result, not proof of complete application security. CI now runs
npm audit --audit-level=moderate in addition to tests, lint and production build.

References:
- https://github.com/advisories/GHSA-vfj7-8cjw-p6xm
- https://tailwindcss.com/docs/upgrade-guide
- https://vitest.dev/guide/migration/
