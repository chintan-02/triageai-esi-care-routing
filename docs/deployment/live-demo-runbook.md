# TriageAI live demo operations

Updated 2026-10-17 UTC from operator verification on 2026-10-16 America/Edmonton. This is an educational,
synthetic-data portfolio demo, not a clinical production deployment. Resource
names below are not credentials. Never commit passwords, session tokens, owner
connection strings, gcloud credentials or local virtual environments.

## Verified inventory

| Component | Resource |
| --- | --- |
| Google Cloud project | `triageai-chintan-2026` / `855163679553` |
| Cloud Run / Artifact Registry / GCS region | `northamerica-northeast1` (Montréal) |
| Public browser frontend | `https://triageai-chintan-staging.netlify.app` |
| Public demo API | `https://triageai-demo-3mn3ubivua-nn.a.run.app` |
| IAM-private staging API | `https://triageai-staging-3mn3ubivua-nn.a.run.app` |
| First demo revision | `triageai-demo-00001-lut` |
| First staging revision | `triageai-staging-00001-god` |
| Image repository | `northamerica-northeast1-docker.pkg.dev/triageai-chintan-2026/triageai/backend` |
| Deployed image digest | `sha256:1056f88e246f7e45653e42e0d6813ecd4b20688dd5a432d6180717b5226833ac` |
| Image source commit | `f263f4d` |
| Smoke-helper fix | `ac13dff` (operator confirmed 13 deployment tests passed) |
| PostgreSQL | Neon project `triageai-staging`, branch `production`, database `triageai`, PostgreSQL 17.11 |
| PostgreSQL region | AWS US East 1, N. Virginia |
| Migration head | `0003_demo_controls` |
| Private report bucket | `gs://triageai-chintan-2026-reports` |
| Migration job | `triageai-staging-migrate` |
| Cleanup job | `triageai-staging-cleanup` |
| Scheduler | `triageai-demo-cleanup-hourly`, Montréal, `0 * * * *`, `Etc/UTC` |

Netlify's production deploy context currently builds the feature branch
`feat/cloud-run-deployment`, not main. Its project name includes staging, but it
serves the public demo. Before merging or changing branches, review build and
deployment behavior. The smoke-only fix does not require rebuilding the API image.

### Isolation boundary

Demo and staging are separate Cloud Run services but share the Neon database,
database roles, runtime identity, rate-limit key, report bucket and cleanup job.
Staging is **not** an isolated database test environment. Do not run destructive
migration tests there. Use separate data, storage and identities before claiming
production/staging isolation or introducing real data. Do not import historical
SQLite records into the public demo without reviewing whether they are synthetic.

## Current verified release

- Source application commit: `06d5b67`.
- Image digest: `sha256:ddc1eb4e479d1fba16585ab6ae532637556721272a992524b07a25b907f6dcde`.
- Staging candidate: `triageai-staging-00002-cog`, tested with 0% normal traffic; no staging traffic promotion was recorded.
- Public demo: `triageai-demo-00002-buj`, operator confirmed candidate checks, promotion and browser PDF verification.
- Previous demo revision / compatible application rollback target: `triageai-demo-00001-lut`.
- No schema migration was required. Existing IAM, secrets and scheduler configuration were preserved.
- PDF regression passed: pending snapshot → accepted review → new accepted PDF; original report bytes preserved and unchanged current PDF reused.
- Uptime checks observed successful responses. Five real policies enabled. Temporary delivery test opened and emailed at 23:40 MDT; deleting its policy generated a closure email at 23:44 MDT. Test policy removed; real email channel retained.

## Runtime configuration and IAM

Both services were deployed with 1 CPU, 1 GiB memory, concurrency 8, minimum 0 and
maximum 2 instances, a 60-second request timeout, pool size 3 and overflow 0.
Each service has its own instance limit; these are not a total project spending
cap. CORS permits only `https://triageai-chintan-staging.netlify.app`.

`triageai-demo` grants `roles/run.invoker` to `allUsers` and `triageai-smoke`.
Public invocation does not bypass application bearer authentication or owner
scoping. `triageai-staging` grants Invoker to smoke only (subject to separately
reviewing inherited project/organization policies).

| Identity | Intended permissions |
| --- | --- |
| `triageai-runtime` | Its DB secret, rate-limit secret; bucket-scoped custom role `triageaiReportRuntime`: object create/get |
| `triageai-migrate` | Migration DB secret and rate-limit secret; no bucket access |
| `triageai-cleanup` | Cleanup DB secret and rate-limit secret; bucket-scoped `triageaiReportCleanup`: object delete |
| `triageai-smoke` | Invoker on staging and demo services; no database secret or bucket access |
| `triageai-scheduler` | Invoker on cleanup job only; no execution overrides or data access |

All identity emails end in `@triageai-chintan-2026.iam.gserviceaccount.com`.
Operator `patel.chintan380@gmail.com` has Token Creator on the smoke identity
only. The narrower OpenID Token Creator alone was insufficient for the gcloud
impersonation flow. IAM grants can take several minutes to propagate; diagnose
before granting broader access. No service-account key files are required.

Secret references are pinned to version **1**:

- `triageai-staging-runtime-database:1`
- `triageai-staging-migration-database:1`
- `triageai-staging-cleanup-database:1`
- `triageai-staging-rate-limit:1`

Database URLs use `postgresql+psycopg`, `sslmode=verify-full` and the Linux bundle
`/etc/ssl/certs/ca-certificates.crt`. The Mac binary client needed an explicit
`certifi.where()` CA path; do not disable verification to fix certificate errors.
`triageai_owner` is an operator-only credential, never a deployment credential.
Migration owns tables; runtime has application-table CRUD; cleanup has SELECT/
DELETE and UPDATE on users. Both data roles have SELECT-only on alembic_version
and no public-schema CREATE. Future new tables need reviewed grants; privileges
are not automatically granted to every future table.

## Frontend release

Root `netlify.toml` sets base `app/frontend/react_app`, command
`node scripts/build-netlify.mjs`, publish `dist`, Node 24 and mock mode false.
Netlify UI sets `VITE_API_BASE_URL=https://triageai-demo-3mn3ubivua-nn.a.run.app`.
Changing this variable requires a rebuild. No database secrets belong in VITE
variables, which are bundled into the public client. The build creates exact API
CSP allowlisting and SPA redirects. Deploy previews need separately configured
origins; do not broaden CORS with a wildcard.

## API release and rollback

`scripts/cloud_run_release.py --apply` is **private staging only** and refuses
public services. Do not use it against `triageai-demo`, bypass its guard, or run
its generated cleanup deploy command after scheduling: it would reset cleanup
to dry-run. Public demo release automation is still pending. The existing staging
GitHub workflow is main-only and disabled unless explicitly configured; this
deployment was operator-driven, not a completed automatic production pipeline.

For a future demo update:

1. Run CI for the exact source commit. Build Linux AMD64, inspect the Linux CA
   bundle and push the image. Record its digest and previous serving revision.
2. Back up PostgreSQL and verify restore to a disposable database before schema
   changes. Apply backward-compatible migrations once using the migration job.
3. Deploy the digest to private staging and pass authenticated synthetic smoke
   checks. Shared data means this step is not an isolated schema rehearsal.
4. Deploy the demo revision with `--no-traffic` and a candidate tag, preserving
   its existing IAM and reviewed environment/secret versions. Test candidate
   health, auth, inference and PDF; ID-token audience remains the canonical URL.
5. Promote the exact tested demo revision to 100%; run an incognito browser check
   on the Netlify origin. Record digest, revision, secret versions and test result.

Inspect current demo traffic before any change:

```bash
gcloud run services describe triageai-demo --region=northamerica-northeast1 \
  --project=triageai-chintan-2026 --format='yaml(status.traffic,status.latestReadyRevisionName)'
```

For an application-only rollback, replace `PREVIOUS_VERIFIED_REVISION` with the
recorded known-good revision (the first verified revision above is a historical
baseline, not a permanent rollback target):

```bash
gcloud run services update-traffic triageai-demo --region=northamerica-northeast1 \
  --project=triageai-chintan-2026 --to-revisions=PREVIOUS_VERIFIED_REVISION=100
```

Traffic rollback does not undo migrations, deleted data, changed IAM or secret
versions. Do not use Alembic downgrade as a routine live rollback. For a frontend
regression, restore the last verified Netlify deploy with the matching API URL.
For abuse, emergency closure is removing the demo's `allUsers` Invoker binding;
this intentionally stops ordinary browser access. Keep staging private.

## Hourly cleanup

Saved job arguments: `scripts/cleanup_demo_data.py --apply --batch-size 100`.
Task count/parallelism 1, retries 0, timeout 600 seconds. Scheduler POSTs `{}` to:
`https://run.googleapis.com/v2/projects/triageai-chintan-2026/locations/northamerica-northeast1/jobs/triageai-staging-cleanup:run`
with OAuth using `triageai-scheduler`; retry attempts/duration 0 and HTTP deadline
60 seconds. HTTP success means execution accepted, not cleanup completed.

Each run bounds workspaces, expired sessions and rate buckets separately to 100.
Eligibility requires demo=true, role not Admin, no active session, and updated_at
older than the default 24-hour retention window. Backlogs can persist beyond 24
hours; inspect counts as traffic increases. Failed object deletion retains metadata
for retry. Tombstoned users cannot authenticate while cleanup is pending.

Verified deletion test: aged only disposable user
`6450320a-f28d-4601-81f3-a97ee52d3de4`. Execution
`triageai-staging-cleanup-xfvrc` deleted one workspace and one PDF with zero
failures; user/assessment/report queries returned 0 and GCS returned 404.
Scheduler-triggered execution `triageai-staging-cleanup-6sq52` completed with one
successful task and zero workspace failures; 49 expired rate buckets were found.
The bucket retains a seven-day soft-delete recovery window; a 404 is not proof of
immediate physical erasure. Existing local SQLite backups are not cloud backups.

Inspect schedule and recent executions:

```bash
gcloud scheduler jobs describe triageai-demo-cleanup-hourly \
  --location=northamerica-northeast1 --project=triageai-chintan-2026
gcloud run jobs executions list --job=triageai-staging-cleanup \
  --region=northamerica-northeast1 --project=triageai-chintan-2026 --limit=5
gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="triageai-staging-cleanup" AND jsonPayload.dry_run=false' \
  --project=triageai-chintan-2026 --limit=5 --format='json(timestamp,jsonPayload)'
```

Pause the schedule during investigation, then inspect any already-running job;
pausing does not cancel existing executions:

```bash
gcloud scheduler jobs pause triageai-demo-cleanup-hourly \
  --location=northamerica-northeast1 --project=triageai-chintan-2026
```

Resume with the same command replacing `pause` with `resume`. Do not schedule a
second cleanup job for the shared demo/staging database.

## Monitoring and final acceptance

See [monitoring.md](monitoring.md) for reproducible dry-run/apply commands,
thresholds, email delivery verification and costs. Cloud resources and opening/closure email delivery were verified by the operator; this does not prove every failure condition has been exercised.

Operator confirmed browser intake, real prediction, safety escalation, reviewer
action, audit history and PDF download on 2026-10-16. Still verify mobile layout,
fresh incognito session isolation, direct-route refresh, logout/relogin, cold-start
behavior and browser CSP/network errors. Retain the educational notice. Offline
registry metrics are not live accuracy or proof of clinical validity.

Budget target: C$20/month total, Google Cloud alert budget C$15/month, with 50/80/
100% thresholds. Alerts do not stop spending. Monitor actual Cloud Run, storage,
registry, Scheduler, Monitoring and external-provider usage. Trial credits expire;
scale-to-zero does not make hourly jobs or uptime probes free.
