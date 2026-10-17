"""Report bytes live outside ORM metadata; GCS access uses workload identity."""
from functools import lru_cache
from pathlib import Path
from typing import Protocol
from uuid import UUID

from app.backend.core.config import settings


class ReportStore(Protocol):
    def put(self, key: str, content: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


def checked_key(key: str) -> str:
    # Only server-generated UUID filenames are valid; reject traversal and prefixes.
    if not key.endswith(".pdf"):
        raise ValueError("Invalid report key")
    UUID(key.removeprefix("triageai_report_")[:-4])
    return key


class LocalReportStore:
    def __init__(self, root: str):
        self.root = Path(root)

    def put(self, key: str, content: bytes) -> None:
        import os
        import tempfile
        target = self.root / checked_key(key)
        self.root.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=self.root)
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(content)
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def get(self, key: str) -> bytes:
        return (self.root / checked_key(key)).read_bytes()


    def delete(self, key: str) -> None:
        (self.root / checked_key(key)).unlink(missing_ok=True)


class GCSReportStore:
    def __init__(self, bucket: str):
        from google.cloud import storage
        self.bucket = storage.Client().bucket(bucket)

    def put(self, key: str, content: bytes) -> None:
        self.bucket.blob(checked_key(key)).upload_from_string(
            content, content_type="application/pdf", timeout=30,
        )

    def get(self, key: str) -> bytes:
        from google.api_core.exceptions import NotFound
        try:
            return self.bucket.blob(checked_key(key)).download_as_bytes(timeout=30)
        except NotFound as exc:
            raise FileNotFoundError(key) from exc


    def delete(self, key: str) -> None:
        from google.api_core.exceptions import NotFound
        try:
            self.bucket.blob(checked_key(key)).delete(timeout=30)
        except NotFound:
            pass  # Retrying a partially completed cleanup is safe.


@lru_cache(maxsize=4)
def _gcs_store(bucket: str) -> GCSReportStore:
    return GCSReportStore(bucket)


def get_report_store(backend: str | None = None) -> ReportStore:
    selected = backend or settings.REPORT_STORAGE_BACKEND
    if selected == "gcs":
        return _gcs_store(settings.REPORT_GCS_BUCKET)
    if selected == "local":
        return LocalReportStore(settings.REPORT_OUTPUT_DIR)
    raise ValueError("Unknown report storage backend")
