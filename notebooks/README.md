# Notebooks

This folder separates the final deployment notebook from historical experiment notebooks.

## Final source of truth

The active final deployment notebook is:

notebooks/FINAL_SOURCE_OF_TRUTH/ESI_345_FINAL_DEPLOYMENT_LIGHTGBM_V2_SAFETY_TUNED_FINAL_VERDICT_CHECKED.ipynb

This notebook is the final source-of-truth reference for the LightGBM V2 ESI 3/4/5 deployment candidate.

## Experiments archive

Historical notebooks are stored under:

notebooks/experiments_archive/

Archive folders:

- final_candidates/: older final-candidate notebooks
- pipeline_archive/: earlier dataset audit, EDA, training, evaluation, and safety-rule notebooks

These archived notebooks are useful for project history and model-development context, but they are not the backend runtime source of truth.

## Runtime model artifacts

The FastAPI backend does not execute notebooks at runtime.

The backend runtime model registry is:

model_registry/esi_345_lightgbm_v2/
