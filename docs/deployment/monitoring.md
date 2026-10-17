# Demo monitoring

The provisioner targets the verified live demo only. It creates one operator
email channel, two HTTPS uptime checks and five alert policies. No model, UI,
database schema, IAM grants or application deployment is changed.

| Signal | Configuration | Limitation |
| --- | --- | --- |
| API reachability | HTTPS `/health`, every 15 minutes per checker; 30s timeout; status 200 | Does not verify database readiness |
| Frontend reachability | HTTPS `/login`, same period/timeout/status | Does not execute browser JavaScript |
| Uptime alerts | More than one failed location, persisting 5 minutes; newest sample within 20 minutes | Detection is not immediate; frontend status 200 does not prove JavaScript works |
| API errors | At least 5 container 5xx responses in a five-minute aligned window | No ratio alert at low demo traffic; pre-container rejections excluded |
| Cleanup failure | Job error logs, nonzero system status, or `failed_workspaces > 0`; notifications limited to once per hour | Keep structured summary emission and nonzero exit on failure |
| Cleanup heartbeat | No completed-execution metric for three hours | Must first have observed data; deleted resources may not trigger absence |

Uptime checks are synthetic requests and can start Cloud Run instances. `/health`
does not query PostgreSQL, whereas frequent `/ready` polling would query Neon and
interfere with idle suspension. A cold start can still initialize DB connections.
Fifteen-minute probes reduce but do not eliminate usage. Review current pricing,
provider quotas and actual billing; do not assume monitoring is free. Private
staging is not given public access for uptime monitoring.

## Prepare on the operator Mac

Use the existing Python 3.12 `.venv-cloud`. The script uses only Python's standard
library plus the authenticated gcloud CLI. `certifi` supplies the Mac CA bundle.

```bash
gcloud services enable monitoring.googleapis.com --project=triageai-chintan-2026
export SSL_CERT_FILE="$(python -m certifi)"
python scripts/configure_cloud_monitoring.py --email patel.chintan380@gmail.com
```

The script defaults to a **local dry run with no cloud calls**. Inspect
`/tmp/triageai-monitoring-plan/plan.json`. Placeholder IDs are resolved only during
apply; do not POST the dry-run JSON as-is. It includes the email but no passwords
or tokens. The project owner can bootstrap this; do not grant runtime identities
Monitoring Admin. A restricted operator would need permissions to create/read
uptime checks, alert policies, notification channels and log notification rules.

## Apply and inspect

```bash
python scripts/configure_cloud_monitoring.py --email patel.chintan380@gmail.com --apply
```

The script reuses exact matching resources by display name and refuses duplicates
or configuration drift instead of overwriting it. It is not an atomic transaction:
if an API call fails, earlier creations remain. Fix the error and rerun; matching
resources are reused. Access tokens are captured in memory and never printed or
written. The local `created.json` records resource names and channel verification
status. It does not establish alert delivery. Do not share credential files.

In Google Cloud Console, Monitoring:

1. Open **Alerting → Edit notification channels**; confirm the operator email,
   complete any verification prompt and send a test notification if offered.
   Confirm receipt, including spam/junk folders. Do not claim delivery otherwise.
2. Open **Uptime checks**. Confirm both targets, HTTPS validation, checker results
   and recent samples; allow multiple probe cycles. API uptime is not DB readiness.
3. Open **Alerting**. Confirm five enabled TriageAI policies, each attached to the
   operator channel. Inspect metric charts to confirm actual series and labels.
4. Inspect the hourly cleanup heartbeat after the next scheduler run. Compare the
   actual execution, `dry_run=false`, and zero `failed_workspaces` in Cloud Logging.

Do not intentionally break the public API, revoke storage IAM, or insert fake
ERROR logs into application streams to test notifications. Channel delivery can
be tested separately. A controlled alert firing exercise should use a temporary
policy or disposable resource and be documented, then removed.

## Incident response

- **Uptime:** check provider status, DNS/TLS, Netlify deploy and API revision logs.
  Inspect `/ready` once to distinguish model/schema/database failures.
- **5xx:** inspect bounded recent logs and revision changes; check memory and DB
  connection usage, then use the recorded traffic rollback if compatible.
- **Cleanup:** inspect scheduler acceptance and the actual execution separately.
  Resolve IAM, secrets, schema or object deletion before retrying. If repeated,
  pause the scheduler and restore it after verification.
- **No completion:** verify Scheduler is enabled, target is the Cloud Run jobs API,
  OAuth identity retains job Invoker, and no execution is stuck. Missing data
  alone does not distinguish a broken schedule from Monitoring ingestion failure.

Outstanding limitations: public demo release automation, independent staging data,
verified cloud database backup/restore, full browser/mobile acceptance and a tested
incident notification exercise. No live drift or accuracy monitoring is claimed.

## Official references

- https://docs.cloud.google.com/monitoring/uptime-checks
- https://docs.cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.uptimeCheckConfigs
- https://docs.cloud.google.com/monitoring/alerts/policies-in-api
- https://docs.cloud.google.com/logging/docs/alerting/log-based-alerts
- https://docs.cloud.google.com/monitoring/api/metrics_gcp_p_z
- https://docs.cloud.google.com/run/docs/execute/jobs-on-schedule
