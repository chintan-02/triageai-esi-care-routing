import json
from pathlib import Path


def test_model_artifact_placeholders_are_valid_json() -> None:
    artifact_dir = Path("model_artifacts")

    for filename in ["thresholds.json", "feature_schema.json", "model_metadata.json"]:
        with (artifact_dir / filename).open() as file:
            json.load(file)
