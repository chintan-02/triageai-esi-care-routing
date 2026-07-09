# Model Artifacts Archive

This folder contains experiment and validation artifacts only.

## Runtime model source of truth

The backend runtime model registry is:

```text
model_registry/esi_345_lightgbm_v2/
```

The FastAPI backend does **not** load runtime models from `model_artifacts/`.

## Final deployment metrics

The official final deployment metric source is:

```text
model_registry/esi_345_lightgbm_v2/reports/lightgbm_v2_test_metrics.json
```

## Archive structure

```text
model_artifacts/
  README.md
  experiments_archive/
    validation/
      deployment_config_reference.json
      deployment_config_v3_reference.json
      final_model_comparison_v3.csv
      lgb_v2_validation_summary.csv
      lgb_v3_validation_summary.csv
      threshold_tuning_validation.csv
```

Files under `experiments_archive/` are historical validation, comparison, and experiment artifacts. They are useful for model-selection context, but they are not used by the deployed backend prediction path.
