# TriageAI backend readiness implementation

Branch: `feat/cloud-run-deployment`  
Baseline commit: `2afb41c`  
Scope: local implementation and verification; no cloud resources provisioned.

## Implemented architecture

The existing React application authenticates against FastAPI. FastAPI issues
random, short-lived bearer tokens and stores only SHA-256 token hashes in the
application database. The browser holds its token in tab-scoped sessionStorage,
not localStorage. This avoids cross-site cookie dependence between Netlify and
Cloud Run. Browser JavaScript can access sessionStorage: deployment still needs
XSS prevention and a tested CSP. No secret or administrator credential belongs
in a Vite environment variable.

The authenticated database dependency attaches a server-resolved principal.
Assessment creation records its owner. Assessment lists, dashboards, details,
reviews, audits and report downloads enforce that owner. Attempts to access
another visitor's IDs return 404. Submitted reviewer identities and roles are
replaced with the authenticated principal. Anonymous users receive 401.

Demo users have the Doctor **workflow role**, enabling the review/override
experience inside their own workspace. This is not verification of clinical
credentials. Public registration cannot assign Admin privileges. Public demo
account/session creation can be disabled with PUBLIC_DEMO_ENABLED=false.

Passwords are salted PBKDF2-SHA256 hashes with 600,000 iterations. Sessions expire
and logout revokes the stored token. There is no password reset, email
verification, managed identity provider or staff administration in this release.

## Run locally

Use Python 3.12 for the pinned backend runtime. From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-backend.txt
cp .env.example .env
python -m alembic upgrade head
python -m uvicorn app.backend.api.main:app --host 127.0.0.1 --port 8001
```

In another terminal:

```bash
cd app/frontend/react_app
npm ci
npm run dev
```

Open http://localhost:5173 and select **Start a private demo session**. The
workspace is initially empty. Use the existing intake examples to create
synthetic assessments. Registered demo accounts retain access after signing in
again; anonymous workspace access ends when its session expires or is revoked.
Health and readiness endpoints remain public. Other workflow endpoints require
`Authorization: Bearer <session-token>`.

Startup does not create or alter database tables by default. The explicit
AUTO_CREATE_TABLES=true escape hatch is restricted to development/test. Staging
and production verify the Alembic revision at startup and readiness; migration
must be a separate completed job before new API instances receive traffic.

## PostgreSQL

Set DATABASE_URL to a dedicated database using the psycopg dialect:

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

Use the appropriate verified TLS/Cloud SQL connection configuration for the
chosen hosting environment. Do not use public unrestricted database ingress.
Use a migration identity for schema changes and a separate, restricted runtime
identity. The pool defaults to five connections and no overflow **per process**;
size the total against Cloud Run instance limits and PostgreSQL capacity.

```bash
python -m alembic upgrade head
python -m alembic check
```

For a new database this applies baseline revision `2dc4cd53d258`, followed by
`0002_sessions_storage`. Migration scripts contain explicit, versioned DDL and do
not import live ORM metadata to create tables.

Existing databases created with create_all() need an inspected baseline adoption:
back up first; compare their schema to the baseline revision; reconcile any
schema drift; only then stamp `2dc4cd53d258` and upgrade. Do not blindly stamp a
legacy database. This is not an automated SQLite-to-PostgreSQL data conversion.

Legacy assessments have NULL owners after upgrade and are intentionally hidden
from public sessions. Do not assign them to a shared public demo user.

The old SQLite reset/seed scripts remain local-only maintenance tools. Their
unowned seeded records are not automatically exposed to visitor sessions.

## Durable reports

Local development uses an atomic filesystem report store. Deployment uses a
private GCS bucket via application default credentials / workload identity:

```env
REPORT_STORAGE_BACKEND=gcs
REPORT_GCS_BUCKET=your-private-report-bucket
```

PDF generation uses a temporary directory. The file is uploaded before its
report record is marked generated. PostgreSQL stores the object key and backend,
not a signed public URL. Downloads verify assessment ownership and proxy the
private object through FastAPI. Failed uploads return a generic 503 and mark the
report failed. A missing object is distinct from a storage outage.

Bucket access must be limited to the runtime identity; do not make the bucket
public. Keep the configured bucket stable: moving existing objects between
buckets requires a deliberate data migration. Database and object storage are
not one transaction; a crash between upload and DB commit can leave an orphan
object. Reconciliation/retention must be implemented before public launch.

The existing PDF is a snapshot at generation time. This change does not redesign
historical report versioning or automatic invalidation following later reviews.

## Deployment configuration contract

Staging/production require:

```env
APP_ENV=staging
DEBUG=false
AUTO_CREATE_TABLES=false
DATABASE_URL=postgresql+psycopg://...
CORS_ALLOWED_ORIGINS=["https://your-frontend.netlify.app"]
REPORT_STORAGE_BACKEND=gcs
REPORT_GCS_BUCKET=your-private-report-bucket
SESSION_TTL_MINUTES=60
```

Missing durable storage, SQLite, wildcard/non-HTTPS origins, debug mode or
startup schema mutation is rejected by configuration validation. The backend
container uses Python 3.12 and a non-root user, includes migration scripts, and
listens on port 8001. Configure Cloud Run's container port accordingly.

## Verification

Install the full legacy/test requirements for the complete Python suite:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
npm --prefix app/frontend/react_app test
npm --prefix app/frontend/react_app run build
```

The legacy domain-contract tests intentionally override the authenticated DB
dependency to isolate existing business contracts. `test_auth_ownership.py` is
marked `security` and runs the real authentication dependencies, including real
LightGBM inference and private report download checks.

To run against a disposable PostgreSQL database (tests DROP tables):

```bash
MIGRATION_TEST_DATABASE_URL="$TRIAGEAI_TEST_DATABASE_URL" python -m pytest tests/integration -q
python -m pytest tests/backend -q
```

Set TRIAGEAI_TEST_DATABASE_URL to that disposable database first. Never point
these test settings at staging/production. The PostgreSQL CI job provisions a
PostgreSQL 17 service, runs versioned migration checks, then runs backend tests
with PostgreSQL. A skipped local PostgreSQL test is not PostgreSQL verification.

## Gates before public launch

1. Run the PostgreSQL CI job and verify the Docker image on its target platform.
2. Verify private GCS upload/download with the intended runtime service account.
3. Add shared abuse controls: session issuance/login throttles, bounded inference
   and uploads, per-workspace resource quotas, and request limits. CORS is not an
   abuse-control or authentication mechanism.
4. Implement scheduled expiry cleanup and database/object retention, including
   orphan reconciliation. Expired sessions deny access but do not delete data.
5. Configure cloud identity, IAM, secrets, backups and a tested restore procedure.
6. Add monitoring/alerts, measure resource requirements, and set a cost budget.
7. Harden frontend headers/CSP; validate public HTTPS origins and browser flows.
8. Complete automated deployment/rollback and staging smoke checks before adding
   the public URL to the portfolio.

These are remaining release gates, not claims that this branch is production
ready or clinically validated.

## Verification recorded in this workspace

- Untouched baseline: 96 Python tests, 52 frontend tests, production build passed.
- Final implementation: 115 Python tests passed; one PostgreSQL migration case
  skipped because no local PostgreSQL server is available.
- Final frontend: 56 tests passed; lint and production build passed.
- SQLite: fresh upgrade, repeated upgrade, legacy row preservation, downgrade /
  re-upgrade, schema-drift check, and outdated-schema rejection passed.
- Running HTTP API: readiness, real LightGBM inference, CORS preflight, isolated
  assessments/dashboard, trusted reviewer identity, PDF generation/download,
  cross-user denial and logout revocation passed.
- GCS adapter behavior and remote-report lifecycle are tested with fakes; a real
  bucket and IAM integration have not been tested.
- Docker is unavailable in this execution environment; no image build or Compose
  runtime verification was performed.
- Browser E2E was attempted but Chromium could not be installed because its
  download was invalid. No browser E2E pass is claimed.
- At initial local verification, PostgreSQL CI had not been executed remotely.
  No deployment, resource provisioning, or public release was performed.
  Consult the draft pull request for subsequent CI results.
