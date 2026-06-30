# Model Artifacts

The deployed staging artifact is the LightGBM V2 Weight + Threshold booster text
model:

- `esi_345_lightgbm_v2_threshold.txt`

V3 artifacts and comparison files under `model_artifacts/validation/` are
reference material only. V3 is not the deployed staging model.

Required metadata/configuration files:

- `feature_schema.json`
- `thresholds.json`
- `model_metadata.json`
- `validation/lgb_v2_validation_summary.csv`
- `validation/threshold_tuning_validation.csv`
- `validation/deployment_config_reference.json`

No joblib model file is required. `preprocessing_artifacts.pkl` is intentionally
not required. Raw datasets are not committed.

This model predicts only ESI 3/4/5 and is decision-support only. An ESI 1/2
safety gate is required for high-risk cases before any ESI 3/4/5 routing is
used for workflow decisions.

Validate artifacts with:

```bash
python ml/inference/validate_artifacts.py
```

Phase 4B connects full runtime inference to this booster if it is not already
fully connected in the active backend environment.
