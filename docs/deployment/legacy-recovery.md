# Local synthetic demo metadata recovery

This operator command restores historical SQLite records into an already migrated
local/demo SQLite target. It defaults to a read-only dry run. Back up source and
target databases with SQLite's backup API first. Do not use it for real patient
data or as a production migration tool.

The target account must already exist, be Admin, be non-demo, and not be pending
cleanup. All source assessments are explicitly reassigned to this account. Source
users, password hashes and sessions are never imported. Original review/audit
actors, timestamps and stored predictions remain historical; inference is never
rerun. Each assessment gets an import provenance audit event. Source-wide audit
events without an assessment are preserved but remain outside workspace-scoped
API results.

Report metadata is imported with status `failed`, no download URL, and no storage
key. This command does not recover PDF bytes or follow historical URLs. Original
report metadata is retained in the import manifest. Generate a new report in the
application if needed; it is a new artifact, not the recovered historical PDF.

An identical source snapshot is a no-op on retry, including copies with different
filenames. Any existing record-ID collision blocks the entire import. A changed
source snapshot is not merged automatically. Missing references and unsupported
columns are rejected. All target writes, provenance events, and recalculated
workspace quota counters commit in one transaction; failures roll back together.
The operator import can exceed configured workspace quotas; existing records remain
readable but new creation is blocked until capacity is available or deliberately
increased. Dry-run output includes resulting counts for review. Different IDs may
still represent similar synthetic cases; content deduplication is not automatic.

## Mac Docker verification stack

After pulling the branch and rebuilding, copy one backed-up source to the container:

```bash
docker compose -p triageai-verify cp \
  backups/before_import_20261016_013701/triageai.db \
  backend:/tmp/legacy-triageai.db

docker compose -p triageai-verify exec backend python scripts/import_legacy_metadata.py \
  --source /tmp/legacy-triageai.db --owner-email patel.chintan380@gmail.com
```

Review the counts, then append `--apply` to the second command to import. Refresh
the browser and verify assessments, predictions, historical reviews and audit
history. Only then repeat for other explicitly selected snapshots. Prefer the
current `triageai.db` first; the July archive is optional and may contain obsolete
test cases. Do not replace the target database file or run reset/seed commands.

Tests cover old schemas, dry-run preservation, exact history/actor retention,
credential exclusion, metadata-only reports, idempotence, conflicts, orphan
references, account restrictions and rollback after a partial insert failure.
