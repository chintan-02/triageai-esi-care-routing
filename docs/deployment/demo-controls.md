# Public demo controls and retention

The API uses the existing database for shared request counters and quota
reservations. No Redis service is introduced. PostgreSQL is required in cloud
environments; SQLite supports local verification. Counters survive API restarts
and are shared by all instances using the same database and RATE_LIMIT_SECRET.

## Defaults

| Control | Default |
| --- | --- |
| Public auth attempts per resolved client address | 10/minute |
| Public auth attempts globally | 100/minute |
| Demo/registration attempts per client address | 20/hour |
| Demo/registration attempts globally | 200/hour |
| Login attempts per normalized account identifier | 20/hour |
| Authenticated API requests per workspace | 120/minute |
| Authenticated API requests globally | 1000/minute |
| Intake/prediction requests per workspace | 10/minute |
| PDF generation/get-or-generate per workspace | 5/minute |
| Existing report downloads per workspace | 30/minute |
| NLP requests per workspace | 20/minute |
| Speech requests per workspace | 5/minute |
| All the above expensive operations globally | 500/hour |
| Assessment slots per workspace | 20 |
| Report slots per workspace | 30 |
| Review slots per workspace | 100 |
| JSON/ordinary request bytes | 64 KiB |
| Audio file bytes | 5 MiB |
| Multipart body overhead allowance | 64 KiB |
| Generated report bytes | 2 MiB |
| Demo inactivity before retention eligibility | 24 hours |
| Workspaces / expired sessions / old counter rows considered per cleanup run | 100 each |

These are configurable demo starting points, not load-test-derived production
capacity settings. The limiter is fixed-window, so it can allow a boundary burst
of up to twice a limit. Accepted earlier checks remain charged if a later check
or the business request fails. Saturated buckets stop incrementing. Database
errors fail closed with 503; exceeded rates return 429 and Retry-After. The
frontend displays retry guidance, and CORS exposes that header.

Client addresses and account identifiers are HMACed into counter keys; raw
values and bearer tokens are not stored in counters. All API instances must
share a private, stable RATE_LIMIT_SECRET (32+ characters in staging/production).
Rotating it changes key namespaces and resets effective limits, so rotate it
intentionally. Configure it through Secret Manager at deployment time.

The application reads ASGI's resolved client address, not arbitrary
X-Forwarded-For headers. Staging must verify the trusted proxy/client-address
configuration before public use. Without correct trusted forwarding, legitimate
visitors may share a proxy's bucket; do not solve that by trusting all incoming
forwarded headers. Health/readiness probes are exempt from application limits.
Edge controls, service concurrency/instance limits, timeouts and cost monitoring
are still required; this is not complete DDoS protection.

## Quota behavior

Atomic conditional UPDATEs reserve a slot in the same transaction that creates
the record. Concurrent instances cannot each take the last available slot.
Database migrations backfill counts for existing owned records. Failed PDF
uploads retain their report slot, and retries remain rate-limited. Downloading
an existing PDF does not consume a new report slot. Reviews consume slots too,
bounding repeated edits and their audit events. Exhaustion returns 409 with an
actionable message. Opening a new login session for the same registered account
does not reset its quota. New anonymous workspaces are possible, bounded by
issuance/global operation limits.

Request body limits count actual streamed bytes before JSON or multipart
parsing, including absent or misleading Content-Length. Text/list fields also
have schema bounds. Report generation validates output size before upload.

## Safe cleanup lifecycle

Publicly created accounts are explicitly educational demo accounts. Retention
can remove anonymous and registered demo accounts after inactivity; it does not
provide permanent storage for portfolio visitors.

Eligibility requires all of:

- is_demo=true;
- role is not Admin;
- last activity is older than the configured retention interval;
- no unexpired session exists.

Admin and non-demo/legacy accounts are preserved. Active API requests and login
refresh last activity; cleanup rechecks eligibility in an atomic update before
claiming a workspace. Marking cleanup_pending deliberately preserves the old
activity timestamp so a failed cleanup remains retryable. Pending workspaces
cannot authenticate or obtain another session.

1. Discover a bounded batch. Default mode returns counts only and changes no
   records or objects.
2. On apply, commit the workspace tombstone before external storage I/O.
3. Hold the user row/write lock and delete its known report objects. Missing
   objects are accepted as already deleted. Storage outages fail the workspace.
4. After all object deletes succeed, delete its audits, reviews, predictions,
   reports and assessments in one transaction, then its unshared patients,
   sessions and user row. Shared patient references are preserved defensively.
5. If interrupted, retry the job. Metadata remains available until object
   deletion succeeds; repeated object deletion is idempotent.
6. Purge only the bounded expired session/counter rows discovered for this run.

Report creation persists its backend metadata before uploading to its
deterministic report key. Cleanup therefore covers queued/failed uploads even
if an upload succeeded just before a process died. Cleanup does not scan and
remove arbitrary bucket files or other applications' objects. A dedicated report
bucket and deliberate handling of out-of-band orphan objects are still needed.
The bucket configuration must remain stable until objects are migrated.

## Operator commands

Run migrations first. The cleanup CLI verifies the current schema. Inspect the
selected DATABASE_URL and report storage configuration before invoking it.

```bash
python -m alembic upgrade head
python scripts/cleanup_demo_data.py
```

The second command is a dry run. To apply the configured retention policy:

```bash
python scripts/cleanup_demo_data.py --apply --batch-size 25
```

Output contains aggregate counts, not account emails, clinical text, tokens or
object URLs. A failed workspace gives exit code 1 for scheduler alerting. An
expired workspace that is only partly cleaned remains inaccessible until a
successful retry. Do not recover it by clearing the tombstone while deletion is
in progress.

For the local verification stack:

```bash
docker compose -p triageai-verify exec backend python scripts/cleanup_demo_data.py
```

Cloud scheduling is not provisioned by this change. The next deployment stage
should run this command as an authenticated scheduled Cloud Run job with the
appropriate database and private-bucket permissions, retry policy and alerts.
Avoid running it as an untracked web-server background thread.

## Verification

Tests cover concurrent rate/quota claims using independent DB sessions and a
second engine, spoofed forwarding headers, failed login throttling, global
limits across visitors, body/audio/report size rejection, dry-run preservation,
active/Admin/legacy exclusions, partial storage failure and safe retry, pending
access denial, and shared patient preservation. The PostgreSQL CI job runs these
same backend tests against PostgreSQL and checks migration backfill.

References:
- https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert
- https://docs.cloud.google.com/storage/docs/deleting-objects
