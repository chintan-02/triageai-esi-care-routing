# Verified educational cloud demo — October 16, 2026 MDT

The source application commit is `06d5b67`; this documentation may be committed later.
The deployed image is pinned to
`sha256:ddc1eb4e479d1fba16585ab6ae532637556721272a992524b07a25b907f6dcde`.

## Delivery evidence

- Netlify frontend: https://triageai-chintan-staging.netlify.app/
- Cloud Run demo revision: `triageai-demo-00002-buj`.
- Private staging candidate: `triageai-staging-00002-cog`.
- Managed Neon PostgreSQL; Alembic head `0003_demo_controls`; no new migration for the PDF fix.
- Candidate smoke checks: health, database/schema/model readiness, real inference, workspace isolation and private PDF retrieval.
- PDF freshness regression: generate pending snapshot, accept review, generate accepted snapshot, preserve original bytes, reuse unchanged latest PDF.
- Scheduler-triggered cleanup execution `triageai-staging-cleanup-6sq52` completed successfully. A separate disposable-workspace exercise verified one workspace and report deletion, zero matching DB records and object 404.
- Two uptime checks, five operational policies, opening and closure email delivery verified; temporary test policy deleted.
- Application commit CI: backend, PostgreSQL migration/API integration and frontend checks passed.

## Local validation

Release-documentation validation: **160 Python tests passed, 1 PostgreSQL-only test skipped locally; 60 React tests passed across 15 files**. PostgreSQL migration/API integration passed separately in GitHub CI on application commit `06d5b67`. Frontend production build passed.
Historical 96 backend / 52 frontend counts elsewhere describe the earlier demo freeze.

## Boundaries

Educational synthetic-data demo; no diagnosis, prospective clinical validation or patient-care effectiveness claim.
Demo and staging share database/storage infrastructure. Public release was operator-driven; GitHub public deployment automation is not configured.
Registry metrics are offline evaluation, not live model accuracy or drift monitoring. Uptime email delivery does not exercise every production failure condition.
Cloud database restore, independent staging, clinical governance and operational ownership remain future work.

See [operations](../deployment/live-demo-runbook.md) and [monitoring](../deployment/monitoring.md).
