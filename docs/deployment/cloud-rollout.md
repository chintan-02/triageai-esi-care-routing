# Private staging deployment preparation

Status: repository configuration only. No cloud resources, billing, IAM or public
hosting have been changed. Real Cloud Run/GCS integration and browser E2E remain
unverified. Use a fresh synthetic staging database, not recovered local history.

## Architecture and cost decision

Netlify delivers the React assets. Cloud Run runs FastAPI and the existing
LightGBM registry. PostgreSQL stores sessions/domain records; a dedicated private
GCS bucket stores PDFs. Separate Cloud Run jobs perform migrations and retention.
GitHub Actions uses Workload Identity Federation, not service account JSON keys.

Design budget selected by the developer: **up to C$20/month total**. This is a
planning target, not an automatically enforced spending cap. The example leaves
cloud_sql_instance empty for external managed PostgreSQL. Evaluate Neon Free as
a candidate using its current published limits, region choices and backup/restore
capabilities before selecting it. Use separate DB users/secrets and verified TLS;
networking, cold-start latency and egress must be tested from Cloud Run. Cloud SQL
remains optional via its Unix socket integration, subject to a reviewed cost
estimate within the total budget. No provider has been provisioned or selected
irreversibly. The editable region is
northamerica-northeast1; this is not a data-residency compliance claim.

Choose a monthly budget and database provider **before provisioning**. Cloud SQL
must be priced independently of Cloud Run scale-to-zero. Review current regional
compute, storage, backups, builds, logs, egress, Artifact Registry, GCS and Netlify
charges. No zero-cost/free-credit claim is made. Budget alerts are notifications,
not hard spending caps. Start API trials at 1 CPU/1 GiB, concurrency 8, minimum 0,
maximum 2 instances per revision. These are unmeasured starting values; overlapping
revisions and in-flight work can increase total usage. Bound job frequency,
artifact/log retention and builds too. Production infrastructure is not included.

## Bootstrap prerequisites

1. Review/merge the draft PR after CI/local verification. Create GitHub environment
   `staging`, restrict deployment to main and enable required reviewers where
   supported. Keep repository variable CLOUD_DEPLOY_ENABLED unset until bootstrap.
2. Separately review/provision project, budget, Artifact Registry repository,
   PostgreSQL, Secret Manager, service accounts, and GCS bucket with uniform access
   and public access prevention. Enable Cloud Run, Artifact Registry, IAM
   Credentials, Security Token Service, Secret Manager and optional Cloud SQL APIs.
3. Copy deployment/cloud-run/staging.example.json to staging.local.json beside it
   (gitignored). Replace placeholders with IDs and secret references only. Numeric
   secret versions are required; `latest` is rejected. Store three separate database
   URLs and a stable private 32+ character rate key in Secret Manager.
4. Create separate PostgreSQL users for migrations, runtime and cleanup. Migration
   owns the application schema and Alembic version table. Runtime/cleanup need
   CONNECT, schema USAGE, table SELECT/INSERT/UPDATE/DELETE and sequence USAGE/SELECT;
   neither needs CREATE or ownership. Grant SELECT on alembic_version for readiness.
   Set default privileges as the migration owner for future tables/sequences.
5. Cloud SQL URL pattern (URL-encode passwords):
   `postgresql+psycopg://USER:PASSWORD@/triageai?host=/cloudsql/PROJECT:REGION:INSTANCE`.
   Attach the instance through the provided flags and grant Cloud SQL Client where
   needed. Never open database ingress to 0.0.0.0/0. Pool size is 3 per API process,
   zero overflow; reserve connections for jobs and overlapping revisions.

## IAM boundaries

| Identity | Permissions and scope |
| --- | --- |
| Runtime | Secret Accessor on runtime DB URL and rate key; bucket object create/get; Cloud SQL Client if used |
| Migration | Secret Accessor on migration DB URL and rate key; DB schema owner; Cloud SQL Client if used; no bucket access |
| Cleanup | Secret Accessor on cleanup DB URL and rate key; bucket object delete; Cloud SQL Client if used |
| Smoke | Cloud Run Invoker on private staging service only |
| GitHub deploy | Artifact Registry Writer on image repository; Cloud Run Developer for staging service/jobs; Service Account User on runtime/migration/cleanup accounts; OpenID Connect Identity Token Creator on smoke account |

Use bucket-scoped custom roles with storage.objects.create/get for runtime and
storage.objects.delete for cleanup. Add runtime delete only if overwrites require
it. Verify actual SDK permissions in staging; never make the bucket public to
resolve errors. Cloud Run's service agent needs image access across project
boundaries. Bind Workload Identity Federation to exact numeric GitHub owner/repo
IDs, main ref and staging environment claim; grant Workload Identity User only
to that restricted principal set on the deploy identity. No unrestricted pool.

Review inherited project/organization IAM separately. The tool checks service
IAM and the invoker-check-disabled annotation, not every ancestor policy.

## Offline plan and first bootstrap

The renderer uses standard-library Python. Without --apply it makes no cloud
calls, but writes the requested local plan files. Use a real immutable image
backend digest; this placeholder command deliberately fails validation:

```bash
python3 scripts/cloud_run_release.py \
  --config deployment/cloud-run/staging.local.json \
  --image REGION-docker.pkg.dev/PROJECT/REPOSITORY/backend@sha256:ACTUAL_64_HEX_DIGEST \
  --output /tmp/triageai-release-plan
```

Review environment.yaml and plan.json (settings and secret references only).
The release tool requires an **existing private service** with a known revision
receiving 100% traffic; it never treats authorization failure as an absent service.
After cost approval, bootstrap once as an operator:

1. Build/push the AMD64 image, resolve its digest, render/inspect the plan.
2. Execute the reviewed migrate_deploy command, then migrate_execute with --wait.
3. Execute service_deploy from the plan for initial private bootstrap. It sets
   port 8001, disables unauthenticated invocation and configures /ready startup
   probes. Check IAM; grant smoke identity Invoker on that service.
4. Run scripts/cloud_smoke.py with --url SERVICE_URL --audience SERVICE_URL and
   --identity-service-account SMOKE_ACCOUNT. The operator must be allowed to mint
   an ID token for that identity. Synthetic checks cover health/readiness, real
   inference, workspace separation, GCS PDF upload/download and logout. Created
   demo workspaces remain until retention; smoke does not delete them.

## Subsequent manual releases

Set repository variables CLOUD_DEPLOY_ENABLED=true,
GCP_WORKLOAD_IDENTITY_PROVIDER and GCP_DEPLOY_SERVICE_ACCOUNT. Set environment
variable CLOUD_RUN_STAGING_CONFIG to completed configuration JSON. Run `Deploy
private staging` on main only after CI passes that exact main commit.

The workflow builds/pushes AMD64, pins its digest, refreshes federation credentials,
records the previous revision, executes/waits for migrations, deploys the cleanup
job in dry-run mode, deploys an unserved candidate, runs authenticated smoke checks,
then promotes to 100% **private staging** traffic. Failure before promotion leaves
previous traffic untouched. A migration failure still requires inspecting schema
and job logs before retry; do not assume every future DDL operation is atomic.

Cleanup starts dry-run-only, unscheduled, max-retries zero. Review dry-run counts,
verify real GCS delete permissions, then deliberately add --apply to its arguments
and schedule authenticated execution with bounded batches, retry and alerts.
Do not delete report objects via independent bucket lifecycle while retaining
metadata that claims they are generated.

## Netlify and public launch

Connect Netlify to the repository using root netlify.toml: frontend base directory,
dist publish directory, Node 24, VITE_USE_MOCK_API=false and SPA deep-link fallback.
Provide VITE_API_BASE_URL as the actual HTTPS backend origin in build environment.
No credentials belong in VITE variables. The build rejects missing/invalid/
localhost endpoints and mock mode and writes CSP/security headers. connect-src
allows that exact API origin; existing Google Fonts/inline UI styles are allowed,
but inline/eval scripts are not. Deploy previews need separate explicit
origin/backend configuration; never add wildcard Netlify origins to CORS.
CI uses a deliberately nonworking .invalid origin solely for build verification;
do not publish that CI artifact as your live site.

An IAM-private API is not directly usable by normal Netlify browser sessions.
Authenticated CLI smoke checks are not public browser E2E. Public invocation of
a portfolio service needs a separate deliberate release decision, while retaining
application bearer auth, private DB/bucket, exact CORS, quotas and synthetic data.
This staging tool refuses already-public services; prepare a production release
workflow separately rather than using it to update the public service.

Before public launch verify HTTPS/deep links, CORS, real browser auth, inference,
review, PDF download, CSP console, cold starts, concurrency and 401/404/429 states.
Azure speech remains unconfigured; verify honest UI behavior before enabling it.
Verify resolved client IP behind Cloud Run; never trust arbitrary forwarded
headers. Add structured request/error IDs, latency/5xx/DB connection/cleanup
alerts without tokens or clinical text. Dashboard registry scores are offline
evaluation metrics, not measured live accuracy/drift.

## Rollback and backups

The workflow artifact release.json records previous/candidate revisions and image.
On smoke failure inspect candidate/job logs before retry and remove unused tags
when appropriate. To restore traffic use the recorded revision, not LATEST:

```bash
gcloud run services update-traffic SERVICE --project PROJECT --region REGION \
  --to-revisions PREVIOUS_REVISION=100
```

Traffic rollback does not undo schema changes. Use expand/contract migrations and
verify previous API compatibility with the migrated schema before release. Do
not use live Alembic downgrade as routine rollback. Configure PostgreSQL backups,
test restore to a disposable database, and check GCS report consistency before
public use. Mac SQLite backups are not cloud backups. Pin secret versions and
retain compatible prior versions. An image rollback is not data recovery.

## References

- https://github.com/google-github-actions/auth
- https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy
- https://docs.cloud.google.com/sdk/gcloud/reference/run/jobs/deploy
- https://docs.cloud.google.com/sql/docs/postgres/connect-run
- https://docs.cloud.google.com/run/docs/configuring/services/secrets
- https://docs.netlify.com/build/configure-builds/monorepos/
- https://docs.netlify.com/build/frameworks/framework-setup-guides/vite/

Budget research references (verify again before provisioning):
- https://neon.com/docs/introduction/plans
- https://cloud.google.com/sql/pricing
- https://cloud.google.com/run/pricing
