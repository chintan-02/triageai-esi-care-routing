# Optional installs if your environment is missing packages:
# !pip install pandas numpy scikit-learn lightgbm matplotlib joblib shap

import os
import re
import json
import warnings
import platform
from pathlib import Path
from datetime import datetime, timezone

warnings.filterwarnings("ignore")

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    log_loss,
    roc_auc_score,
    average_precision_score
)
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

import lightgbm as lgb

RANDOM_STATE = 42
MODEL_VERSION = "lightgbm_v3_enhanced_eval"
MODEL_DISPLAY_NAME = "LightGBM V3 Enhanced"

# IMPORTANT: change this to your actual dataset path.
csv_path = Path("/Users/rambo/Documents/integrated_ai/arti_404/triageai-esi-care-routing/Triage_ESI Dataset/triage.csv")

OUTPUT_DIR = Path("/Users/rambo/Documents/integrated_ai/arti_404/triageai-esi-care-routing/model_registry/esi_345_lightgbm_v3")
REPORTS_DIR = OUTPUT_DIR / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_LOG_PATH = OUTPUT_DIR / "prediction_audit_log.jsonl"

CONFIDENCE_THRESHOLD = 0.60

label_map = {3: 0, 4: 1, 5: 2}
reverse_label_map = {0: 3, 1: 4, 2: 5}
class_names = ["ESI 3", "ESI 4", "ESI 5"]

print("Python   :", platform.python_version())
print("OS       :", platform.system(), platform.machine())
print("Pandas   :", pd.__version__)
print("NumPy    :", np.__version__)
print("LightGBM :", lgb.__version__)
print("Output   :", OUTPUT_DIR.resolve())

if not csv_path.exists():
    raise FileNotFoundError(
        f"Dataset not found: {csv_path}\n"
        "Update `csv_path` in Section 0 before running this notebook."
    )

all_columns = pd.read_csv(csv_path, nrows=0).columns.tolist()
print("Total raw columns:", len(all_columns))

if "esi" not in all_columns:
    raise ValueError("Required target column `esi` was not found.")

print("Target column confirmed: esi")

USE_PREVIOUS_DISPO = False

safe_categorical_candidates = [
    "gender",
    "arrivalmode",
    "arrivalmonth",
    "arrivalday",
    "arrivalhour_bin",
    "triage_vital_o2_device",
]

if USE_PREVIOUS_DISPO:
    safe_categorical_candidates.append("previousdispo")

safe_numeric_candidates = [
    "age",
    "n_edvisits",
    "n_admissions",
    "triage_vital_hr",
    "triage_vital_sbp",
    "triage_vital_dbp",
    "triage_vital_rr",
    "triage_vital_o2",
    "triage_vital_temp",
]

blocked_risky_cols = [
    "dep_name",
    "ethnicity",
    "race",
    "lang",
    "religion",
    "maritalstatus",
    "employstatus",
    "insurance_status",
]

categorical_cols = [c for c in safe_categorical_candidates if c in all_columns]
numeric_cols = [c for c in safe_numeric_candidates if c in all_columns]
cc_cols = [c for c in all_columns if c.startswith("cc_")]

selected_feature_cols = categorical_cols + numeric_cols + cc_cols

print("Categorical columns:", len(categorical_cols), categorical_cols)
print("Numeric columns    :", len(numeric_cols), numeric_cols)
print("Chief complaint columns:", len(cc_cols))
print("Blocked risky columns present:", [c for c in blocked_risky_cols if c in all_columns])
print("Selected raw feature count:", len(selected_feature_cols))

LEAKAGE_PATTERNS = [
    "_last", "_min", "_max", "_median",
    "meds_", "med_", "lab", "labs", "imaging", "xray", "ct_", "mri",
    "disposition", "admit", "admission", "edoutcome", "hospital", "diagnosis",
    "_count", "_npos",
]

def find_leakage_like_columns(columns):
    flagged = []
    allowlist = {
        "n_admissions",
        "triage_vital_o2_device",
    }

    for col in columns:
        col_lower = col.lower()

        # cc_abnormallab is a complaint reason, not post-triage lab values.
        if col_lower.startswith("cc_"):
            continue

        if col in allowlist:
            continue

        if any(pattern in col_lower for pattern in LEAKAGE_PATTERNS):
            flagged.append(col)

    return flagged

flagged = find_leakage_like_columns(selected_feature_cols)

if flagged:
    raise ValueError(f"Potential leakage columns selected: {flagged[:30]}")

print("Leakage guard PASSED.")

use_cols = ["esi"] + selected_feature_cols
use_cols = list(dict.fromkeys(use_cols))

print("Loading selected columns...")
df = pd.read_csv(csv_path, usecols=use_cols, low_memory=False)
print("Loaded shape:", df.shape)

df = df.dropna(subset=["esi"]).copy()
df["esi"] = df["esi"].astype(int)

client_df = df[df["esi"].isin([3, 4, 5])].copy()
client_df["esi_label"] = client_df["esi"].map(label_map).astype(int)

client_dist = client_df["esi"].value_counts().sort_index()
client_summary = pd.DataFrame({
    "count": client_dist,
    "percentage": (client_dist / len(client_df) * 100).round(2),
    "model_label": [label_map[i] for i in client_dist.index],
})

print("Client-focused shape:", client_df.shape)
print(client_summary)

if 3 in client_dist.index and 5 in client_dist.index:
    print("Imbalance ratio ESI 3 / ESI 5:", round(client_dist.loc[3] / client_dist.loc[5], 2))

vital_cols = [
    "triage_vital_hr",
    "triage_vital_sbp",
    "triage_vital_dbp",
    "triage_vital_rr",
    "triage_vital_o2",
    "triage_vital_temp",
]

complaint_group_specs = {
    "cardiac": ["chestpain", "palpitation", "syncope"],
    "respiratory": ["shortnessofbreath", "sob", "cough", "asthma", "wheez"],
    "abdominal": ["abdominalpain", "flankpain", "nausea", "emesis", "vomit", "diarrhea"],
    "trauma": ["fall", "mvc", "motorvehicle", "injury", "trauma", "laceration"],
    "neuro": ["headache", "dizziness", "seizure", "weakness", "numbness", "alteredmental"],
    "infection": ["fever", "sorethroat", "cellulitis", "abscess", "rash"],
    "minor_msk_skin": ["backpain", "kneepain", "footpain", "anklepain", "rash", "wound"],
    "allergy": ["allergic", "allergy", "anaphyl", "hives"],
}

def clean_cc_name(col):
    return col.replace("cc_", "").replace("/", "_").replace("-", "_").replace(" ", "_")

def create_row_level_features(input_df, cc_columns):
    out = input_df.copy()

    for col in vital_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    vital_missing_flag_cols = []
    for col in vital_cols:
        if col in out.columns:
            flag_col = f"{col}_missing_flag"
            out[flag_col] = out[col].isna().astype("int8")
            vital_missing_flag_cols.append(flag_col)

    if vital_missing_flag_cols:
        out["total_vitals_missing"] = out[vital_missing_flag_cols].sum(axis=1).astype("int8")
    else:
        out["total_vitals_missing"] = 0

    if "triage_vital_o2_missing_flag" in out.columns:
        out["o2_missing_flag"] = out["triage_vital_o2_missing_flag"]
    elif "triage_vital_o2" in out.columns:
        out["o2_missing_flag"] = out["triage_vital_o2"].isna().astype("int8")
    else:
        out["o2_missing_flag"] = 0

    if {"triage_vital_hr", "triage_vital_sbp"}.issubset(out.columns):
        out["shock_index"] = np.where(
            out["triage_vital_sbp"] > 0,
            out["triage_vital_hr"] / out["triage_vital_sbp"],
            np.nan,
        )
    else:
        out["shock_index"] = np.nan

    if {"triage_vital_sbp", "triage_vital_dbp"}.issubset(out.columns):
        out["pulse_pressure"] = out["triage_vital_sbp"] - out["triage_vital_dbp"]
        out["mean_arterial_pressure"] = (
            out["triage_vital_sbp"] + 2 * out["triage_vital_dbp"]
        ) / 3
    else:
        out["pulse_pressure"] = np.nan
        out["mean_arterial_pressure"] = np.nan

    for col in ["shock_index", "pulse_pressure", "mean_arterial_pressure"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
        out.loc[~np.isfinite(out[col]), col] = np.nan

    out["abnormal_hr_flag"] = (
        (out.get("triage_vital_hr", pd.Series(np.nan, index=out.index)) < 50) |
        (out.get("triage_vital_hr", pd.Series(np.nan, index=out.index)) > 120)
    ).astype("int8")

    out["low_sbp_flag"] = (
        out.get("triage_vital_sbp", pd.Series(np.nan, index=out.index)) < 90
    ).astype("int8")

    out["low_o2_flag"] = (
        out.get("triage_vital_o2", pd.Series(np.nan, index=out.index)) < 94
    ).astype("int8")

    out["high_rr_flag"] = (
        out.get("triage_vital_rr", pd.Series(np.nan, index=out.index)) > 24
    ).astype("int8")

    out["fever_flag"] = (
        out.get("triage_vital_temp", pd.Series(np.nan, index=out.index)) >= 100.4
    ).astype("int8")

    abnormal_vital_flag_cols = [
        "abnormal_hr_flag", "low_sbp_flag", "low_o2_flag", "high_rr_flag", "fever_flag"
    ]
    out["abnormal_vital_count"] = out[abnormal_vital_flag_cols].sum(axis=1).astype("int8")

    complaint_group_cols_local = []
    complaint_group_matches = {}

    for group_name, keywords in complaint_group_specs.items():
        matched = [
            c for c in cc_columns
            if any(keyword in c.lower().replace("_", "") for keyword in keywords)
        ]
        out_col = f"cc_group_{group_name}"

        if matched:
            out[out_col] = out[matched].fillna(0).astype("int8").max(axis=1).astype("int8")
        else:
            out[out_col] = 0

        complaint_group_cols_local.append(out_col)
        complaint_group_matches[out_col] = matched

    if cc_columns:
        for col in cc_columns:
            if col not in out.columns:
                out[col] = 0

        out["cc_total_count"] = out[cc_columns].fillna(0).astype("int8").sum(axis=1).astype("int16")

        cc_names = [clean_cc_name(c) for c in cc_columns]
        cc_matrix = out[cc_columns].fillna(0).astype("int8").values
        active_rows, active_cols_idx = np.where(cc_matrix == 1)

        seq_lists = [[] for _ in range(len(out))]
        for row_idx, col_idx in zip(active_rows, active_cols_idx):
            seq_lists[row_idx].append(cc_names[col_idx])

        out["cc_sequence"] = [" ".join(words) if words else "unknown" for words in seq_lists]
    else:
        out["cc_total_count"] = 0
        out["cc_sequence"] = "unknown"

    clinical_feature_cols_local = [
        "o2_missing_flag",
        "total_vitals_missing",
        "shock_index",
        "pulse_pressure",
        "mean_arterial_pressure",
        "abnormal_hr_flag",
        "low_sbp_flag",
        "low_o2_flag",
        "high_rr_flag",
        "fever_flag",
        "abnormal_vital_count",
        "cc_total_count",
    ] + vital_missing_flag_cols + complaint_group_cols_local

    return out, clinical_feature_cols_local, complaint_group_cols_local, complaint_group_matches

client_df, clinical_feature_cols, complaint_group_cols, complaint_group_matches = create_row_level_features(client_df, cc_cols)
numeric_cols_extended = list(dict.fromkeys(numeric_cols + clinical_feature_cols))

print("Base numeric columns:", len(numeric_cols))
print("Added clinical features:", len(clinical_feature_cols))
print("Extended numeric columns:", len(numeric_cols_extended))
print("Complaint group columns:", complaint_group_cols)
print(client_df[["esi", "esi_label", "cc_sequence"]].head())

SAFETY_GATE_CONFIG = {
    "very_low_o2": 90,
    "low_sbp": 90,
    "very_high_rr": 30,
    "very_low_rr": 8,
    "very_high_hr": 130,
    "very_low_hr": 40,
    "high_fever_f": 104.0,
}

def safe_float(value):
    try:
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None

def apply_esi12_safety_gate(row):
    red_flags = []

    o2 = safe_float(row.get("triage_vital_o2"))
    sbp = safe_float(row.get("triage_vital_sbp"))
    rr = safe_float(row.get("triage_vital_rr"))
    hr = safe_float(row.get("triage_vital_hr"))
    temp = safe_float(row.get("triage_vital_temp"))

    if o2 is not None and o2 < SAFETY_GATE_CONFIG["very_low_o2"]:
        red_flags.append(f"very low oxygen saturation ({o2})")

    if sbp is not None and sbp < SAFETY_GATE_CONFIG["low_sbp"]:
        red_flags.append(f"very low systolic blood pressure ({sbp})")

    if rr is not None and rr > SAFETY_GATE_CONFIG["very_high_rr"]:
        red_flags.append(f"severe respiratory distress signal: high respiratory rate ({rr})")

    if rr is not None and rr < SAFETY_GATE_CONFIG["very_low_rr"]:
        red_flags.append(f"severe respiratory distress signal: very low respiratory rate ({rr})")

    if hr is not None and hr > SAFETY_GATE_CONFIG["very_high_hr"]:
        red_flags.append(f"very high heart rate ({hr})")

    if hr is not None and hr < SAFETY_GATE_CONFIG["very_low_hr"]:
        red_flags.append(f"very low heart rate ({hr})")

    if temp is not None and temp >= SAFETY_GATE_CONFIG["high_fever_f"]:
        red_flags.append(f"very high fever ({temp})")

    cardiac = int(row.get("cc_group_cardiac", 0) or 0)
    respiratory = int(row.get("cc_group_respiratory", 0) or 0)
    trauma = int(row.get("cc_group_trauma", 0) or 0)
    neuro = int(row.get("cc_group_neuro", 0) or 0)
    allergy = int(row.get("cc_group_allergy", 0) or 0)
    abnormal_vital_count = int(row.get("abnormal_vital_count", 0) or 0)

    if cardiac and abnormal_vital_count >= 1:
        red_flags.append("high-risk cardiac complaint with abnormal vital sign")

    if respiratory and abnormal_vital_count >= 1:
        red_flags.append("respiratory complaint with abnormal vital sign")

    if trauma and abnormal_vital_count >= 1:
        red_flags.append("trauma complaint with abnormal vital sign")

    if neuro and abnormal_vital_count >= 1:
        red_flags.append("neurologic complaint with abnormal vital sign")

    if allergy and (respiratory or (sbp is not None and sbp < 100)):
        red_flags.append("possible severe allergic reaction pattern")

    return {
        "safety_gate_triggered": len(red_flags) > 0,
        "red_flags": red_flags,
        "recommended_route": (
            "urgent_clinician_review_or_esi_1_2_escalation_pathway"
            if red_flags else
            "continue_to_esi_3_4_5_model"
        ),
        "safety_gate_note": (
            "Conservative decision-support screen only. "
            "Not a diagnosis and not a replacement for clinician judgment."
        ),
    }

sample_gate_result = apply_esi12_safety_gate(client_df.iloc[0])
sample_gate_result

train_full_df, test_df = train_test_split(
    client_df,
    test_size=0.20,
    stratify=client_df["esi_label"],
    random_state=RANDOM_STATE,
)

train_df, val_df = train_test_split(
    train_full_df,
    test_size=0.15,
    stratify=train_full_df["esi_label"],
    random_state=RANDOM_STATE,
)

print("Train rows:", len(train_df))
print("Val rows  :", len(val_df))
print("Test rows :", len(test_df))
print("Train distribution:", np.bincount(train_df["esi_label"]))
print("Val distribution  :", np.bincount(val_df["esi_label"]))
print("Test distribution :", np.bincount(test_df["esi_label"]))

clinical_ranges = {
    "age": (0, 120),
    "triage_vital_hr": (30, 220),
    "triage_vital_sbp": (50, 280),
    "triage_vital_dbp": (20, 180),
    "triage_vital_rr": (4, 70),
    "triage_vital_o2": (50, 100),
    "triage_vital_temp": (85, 108),
}

def apply_clinical_ranges(df_part):
    df_part = df_part.copy()
    changed = {}

    for col, (low, high) in clinical_ranges.items():
        if col in df_part.columns:
            df_part[col] = pd.to_numeric(df_part[col], errors="coerce")
            mask = (df_part[col] < low) | (df_part[col] > high)
            changed[col] = int(mask.sum())
            df_part.loc[mask, col] = np.nan

    return df_part, changed

train_df, train_outliers = apply_clinical_ranges(train_df)
val_df, val_outliers = apply_clinical_ranges(val_df)
test_df, test_outliers = apply_clinical_ranges(test_df)

print("Train outliers converted to NaN:", {k: v for k, v in train_outliers.items() if v > 0})

for col in numeric_cols_extended:
    if col in train_df.columns:
        train_df[col] = pd.to_numeric(train_df[col], errors="coerce")
        val_df[col] = pd.to_numeric(val_df[col], errors="coerce")
        test_df[col] = pd.to_numeric(test_df[col], errors="coerce")

numeric_medians = {}

for col in numeric_cols_extended:
    if col in train_df.columns:
        median_value = train_df[col].median()
        if pd.isna(median_value):
            median_value = 0
        numeric_medians[col] = float(median_value)
        train_df[col] = train_df[col].fillna(median_value)
        val_df[col] = val_df[col].fillna(median_value)
        test_df[col] = test_df[col].fillna(median_value)

for col in categorical_cols:
    train_df[col] = train_df[col].fillna("Missing").astype(str)
    val_df[col] = val_df[col].fillna("Missing").astype(str)
    test_df[col] = test_df[col].fillna("Missing").astype(str)

try:
    onehot_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
except TypeError:
    onehot_encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)

if categorical_cols:
    X_cat_train = onehot_encoder.fit_transform(train_df[categorical_cols])
    X_cat_val = onehot_encoder.transform(val_df[categorical_cols])
    X_cat_test = onehot_encoder.transform(test_df[categorical_cols])
    cat_feature_names = onehot_encoder.get_feature_names_out(categorical_cols).tolist()
else:
    X_cat_train = np.empty((len(train_df), 0))
    X_cat_val = np.empty((len(val_df), 0))
    X_cat_test = np.empty((len(test_df), 0))
    cat_feature_names = []

print("Numeric medians fitted:", len(numeric_medians))
print("Categorical feature count:", len(cat_feature_names))

existing_numeric_cols = [c for c in numeric_cols_extended if c in train_df.columns]

X_num_train = train_df[existing_numeric_cols].astype("float32").values
X_num_val = val_df[existing_numeric_cols].astype("float32").values
X_num_test = test_df[existing_numeric_cols].astype("float32").values

for col in cc_cols:
    train_df[col] = train_df[col].fillna(0).astype("int8")
    val_df[col] = val_df[col].fillna(0).astype("int8")
    test_df[col] = test_df[col].fillna(0).astype("int8")

X_cc_train = train_df[cc_cols].astype("float32").values if cc_cols else np.empty((len(train_df), 0))
X_cc_val = val_df[cc_cols].astype("float32").values if cc_cols else np.empty((len(val_df), 0))
X_cc_test = test_df[cc_cols].astype("float32").values if cc_cols else np.empty((len(test_df), 0))

X_lgb_train = np.hstack([X_num_train, X_cat_train.astype("float32"), X_cc_train])
X_lgb_val = np.hstack([X_num_val, X_cat_val.astype("float32"), X_cc_val])
X_lgb_test = np.hstack([X_num_test, X_cat_test.astype("float32"), X_cc_test])

raw_feature_columns_lgb = existing_numeric_cols + cat_feature_names + cc_cols

def sanitize_feature_names(names):
    clean_names = []
    seen = {}

    for name in names:
        clean = re.sub(r"[^0-9a-zA-Z_]+", "_", str(name))
        clean = re.sub(r"_+", "_", clean).strip("_")
        if clean == "":
            clean = "feature"

        count = seen.get(clean, 0)
        seen[clean] = count + 1

        if count > 0:
            clean = f"{clean}_{count}"

        clean_names.append(clean)

    return clean_names

feature_columns_lgb = sanitize_feature_names(raw_feature_columns_lgb)

y_train = train_df["esi_label"].values.astype("int64")
y_val = val_df["esi_label"].values.astype("int64")
y_test = test_df["esi_label"].values.astype("int64")

print("X_lgb_train:", X_lgb_train.shape)
print("X_lgb_val  :", X_lgb_val.shape)
print("X_lgb_test :", X_lgb_test.shape)
print("Feature count:", len(feature_columns_lgb))

classes = np.unique(y_train)
weights = compute_class_weight(class_weight="balanced", classes=classes, y=y_train)
class_weights = {int(cls): float(w) for cls, w in zip(classes, weights)}

print("Class weights from train only:")
for cls, w in class_weights.items():
    print(f"  {cls} ({class_names[cls]}): {w:.4f}")

def evaluate_predictions(y_true, y_pred, model_name, probas=None, show_report=True, show_cm=True, verbose=True):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    labels = [0, 1, 2]

    accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)

    precision_per_class = precision_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    recall_per_class = recall_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    f1_per_class = f1_score(y_true, y_pred, labels=labels, average=None, zero_division=0)

    esi3_mask = y_true == 0
    esi3_to_esi5_count = int(((y_true == 0) & (y_pred == 2)).sum())
    esi3_to_esi5_rate = float(esi3_to_esi5_count / max(int(esi3_mask.sum()), 1))

    # Compute AUC metrics before the dict so we can include them directly
    roc_auc_macro = None
    pr_auc_macro = None
    if probas is not None:
        try:
            y_onehot = np.eye(3)[y_true.astype(int)]
            roc_auc_macro = float(roc_auc_score(y_true, probas, multi_class="ovr", average="macro"))
            pr_auc_macro = float(average_precision_score(y_onehot, probas, average="macro"))
        except Exception:
            pass

    metrics = {
        "model": model_name,
        "accuracy": float(accuracy),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "esi3_precision": float(precision_per_class[0]),
        "esi3_recall": float(recall_per_class[0]),
        "esi3_f1": float(f1_per_class[0]),
        "esi4_precision": float(precision_per_class[1]),
        "esi4_recall": float(recall_per_class[1]),
        "esi4_f1": float(f1_per_class[1]),
        "esi5_precision": float(precision_per_class[2]),
        "esi5_recall": float(recall_per_class[2]),
        "esi5_f1": float(f1_per_class[2]),
        "esi3_to_esi5_count": esi3_to_esi5_count,
        "esi3_to_esi5_rate": esi3_to_esi5_rate,
        "roc_auc_macro": roc_auc_macro,
        "pr_auc_macro": pr_auc_macro,
    }

    if verbose:
        print("=" * 90)
        print(model_name)
        print("=" * 90)
        print(f"Accuracy            : {accuracy:.4f}")
        print(f"Macro F1            : {macro_f1:.4f}")
        print(f"Weighted F1         : {weighted_f1:.4f}")
        print(f"ESI 5 F1            : {f1_per_class[2]:.4f}")
        print(f"ESI 3 → ESI 5 count : {esi3_to_esi5_count}")
        print(f"ESI 3 → ESI 5 rate  : {esi3_to_esi5_rate:.4%}")
        if roc_auc_macro is not None:
            print(f"ROC-AUC (macro OvR) : {roc_auc_macro:.4f}")
        if pr_auc_macro is not None:
            print(f"PR-AUC  (macro)     : {pr_auc_macro:.4f}")

    if show_report:
        print(classification_report(y_true, y_pred, labels=labels, target_names=class_names, zero_division=0))

    if show_cm:
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
        disp.plot(values_format="d", cmap="Blues")
        plt.title(model_name)
        plt.savefig(f"{OUTPUT_DIR}/{model_name.replace(' ', '_')}_confusion_matrix.png", bbox_inches="tight")
        plt.close()

    return metrics

def predict_with_esi5_threshold(proba, esi5_threshold=0.50):
    proba = np.asarray(proba)
    pred = np.argmax(proba, axis=1)

    force_esi5 = proba[:, 2] >= esi5_threshold
    pred[force_esi5] = 2

    not_esi5 = ~force_esi5
    if np.any(not_esi5):
        pred[not_esi5] = np.argmax(proba[not_esi5, :2], axis=1)

    return pred

def threshold_tuning_table(y_true, proba, thresholds):
    rows = []

    for t in thresholds:
        pred = predict_with_esi5_threshold(proba, t)
        metrics = evaluate_predictions(
            y_true,
            pred,
            f"threshold={t:.2f}",
            probas=proba,
            show_report=False,
            show_cm=False,
            verbose=False,
        )
        metrics["threshold"] = float(t)
        rows.append(metrics)

    return pd.DataFrame(rows)

RUN_LGB_V2_SEARCH = True

# Safety-first selection targets.
# The earlier V2 target was about 0.71% unsafe ESI 3 -> ESI 5 downgrades.
# We use 0.75% as the practical validation target because validation/test can differ slightly.
SAFETY_TARGET_ESI3_TO_ESI5_RATE = 0.0075      # 0.75%
SAFETY_FALLBACK_ESI3_TO_ESI5_RATE = 0.0080    # 0.80%
SAFETY_LAST_RESORT_ESI3_TO_ESI5_RATE = 0.0100 # 1.00%

esi5_multipliers = [0.75, 1.00, 1.25, 1.50, 1.75]
v2_thresholds = np.round(np.arange(0.45, 0.81, 0.05), 2)

lgb_params_v2 = {
    "objective": "multiclass",
    "num_class": 3,
    "metric": "multi_logloss",
    "learning_rate": 0.02, "feature_fraction": 0.8,
    "num_leaves": 63,
    "max_depth": -1,
    "min_child_samples": 80,
    "feature_fraction": 0.85,
    "bagging_fraction": 0.85,
    "bagging_freq": 5,
    "lambda_l1": 0.1,
    "lambda_l2": 0.5,
    "verbose": -1,
    "seed": RANDOM_STATE,
    "num_threads": -1,
}

if not RUN_LGB_V2_SEARCH:
    raise RuntimeError("RUN_LGB_V2_SEARCH must be True for the final deployment notebook.")

all_threshold_rows = []
v2_candidates = []

for mult in esi5_multipliers:
    tuned_class_weights = class_weights.copy()
    tuned_class_weights[2] = class_weights[2] * mult

    sw_train = np.array([tuned_class_weights[int(label)] for label in y_train], dtype="float32")
    sw_val = np.array([tuned_class_weights[int(label)] for label in y_val], dtype="float32")

    train_set = lgb.Dataset(
        X_lgb_train,
        label=y_train,
        weight=sw_train,
        feature_name=feature_columns_lgb,
        free_raw_data=False,
    )

    val_set = lgb.Dataset(
        X_lgb_val,
        label=y_val,
        weight=sw_val,
        reference=train_set,
        feature_name=feature_columns_lgb,
        free_raw_data=False,
    )

    print("=" * 90)
    print(f"Training LightGBM V2 candidate | ESI 5 multiplier: {mult}")
    print("=" * 90)

    model_candidate = lgb.train(
        lgb_params_v2,
        train_set,
        num_boost_round=800,
        valid_sets=[train_set, val_set],
        valid_names=["train", "validation"],
        callbacks=[
            lgb.early_stopping(stopping_rounds=40, verbose=False),
            lgb.log_evaluation(period=100),
        ],
    )

    val_proba_candidate = model_candidate.predict(
        X_lgb_val,
        num_iteration=model_candidate.best_iteration,
    )

    threshold_df = threshold_tuning_table(y_val, val_proba_candidate, v2_thresholds)
    threshold_df["esi5_weight_multiplier"] = float(mult)
    threshold_df["best_iteration"] = int(model_candidate.best_iteration)

    # Keep every threshold candidate, not only the best F1 candidate per multiplier.
    # This allows the final selector to choose a safer threshold such as 0.70 if needed.
    all_threshold_rows.extend(threshold_df.to_dict("records"))

    v2_candidates.append({
        "multiplier": float(mult),
        "model": model_candidate,
        "tuned_class_weights": tuned_class_weights,
    })

lgb_v2_validation_summary = pd.DataFrame(all_threshold_rows).copy()

# Safety-first candidate pool.
strict_pool = lgb_v2_validation_summary[
    lgb_v2_validation_summary["esi3_to_esi5_rate"] <= SAFETY_TARGET_ESI3_TO_ESI5_RATE
].copy()

fallback_pool = lgb_v2_validation_summary[
    lgb_v2_validation_summary["esi3_to_esi5_rate"] <= SAFETY_FALLBACK_ESI3_TO_ESI5_RATE
].copy()

last_resort_pool = lgb_v2_validation_summary[
    lgb_v2_validation_summary["esi3_to_esi5_rate"] <= SAFETY_LAST_RESORT_ESI3_TO_ESI5_RATE
].copy()

if len(strict_pool) > 0:
    selection_pool = strict_pool
    selection_rule_used = "strict_safety_target_<=0.75%"
elif len(fallback_pool) > 0:
    selection_pool = fallback_pool
    selection_rule_used = "fallback_safety_target_<=0.80%"
elif len(last_resort_pool) > 0:
    selection_pool = last_resort_pool
    selection_rule_used = "last_resort_safety_target_<=1.00%"
else:
    selection_pool = lgb_v2_validation_summary.copy()
    selection_rule_used = "warning_no_candidate_under_1.00%; selected_best_available"
    print("WARNING: No candidate met the 1.00% validation unsafe downgrade ceiling.")

# Among safety-eligible candidates, choose strongest balanced validation performance.
# The test set is still untouched and used only after this selection.
selection_pool = selection_pool.sort_values(
    by=["macro_f1", "esi5_f1", "accuracy", "esi3_to_esi5_rate"],
    ascending=[False, False, False, True],
).reset_index(drop=True)

selected_v2_row = selection_pool.iloc[0].copy()

# Add a selection flag for easier review.
lgb_v2_validation_summary["selection_pool"] = "not_selected_pool"
lgb_v2_validation_summary.loc[
    lgb_v2_validation_summary["esi3_to_esi5_rate"] <= SAFETY_TARGET_ESI3_TO_ESI5_RATE,
    "selection_pool",
] = "strict_<=0.75%"
lgb_v2_validation_summary.loc[
    (lgb_v2_validation_summary["selection_pool"] == "not_selected_pool")
    & (lgb_v2_validation_summary["esi3_to_esi5_rate"] <= SAFETY_FALLBACK_ESI3_TO_ESI5_RATE),
    "selection_pool",
] = "fallback_<=0.80%"
lgb_v2_validation_summary.loc[
    (lgb_v2_validation_summary["selection_pool"] == "not_selected_pool")
    & (lgb_v2_validation_summary["esi3_to_esi5_rate"] <= SAFETY_LAST_RESORT_ESI3_TO_ESI5_RATE),
    "selection_pool",
] = "last_resort_<=1.00%"

best_mult = float(selected_v2_row["esi5_weight_multiplier"])
best_lgb_v2_threshold = float(selected_v2_row["threshold"])

best_candidate = None
for candidate in v2_candidates:
    if candidate["multiplier"] == best_mult:
        best_candidate = candidate
        break

if best_candidate is None:
    raise RuntimeError("Could not locate selected LightGBM V2 candidate.")

best_lgb_v2_model = best_candidate["model"]
best_lgb_v2_multiplier = best_candidate["multiplier"]
best_lgb_v2_class_weights = best_candidate["tuned_class_weights"]

# Sort full summary for review: safety first, then performance.
lgb_v2_validation_summary = lgb_v2_validation_summary.sort_values(
    by=["esi3_to_esi5_rate", "macro_f1", "esi5_f1"],
    ascending=[True, False, False],
).reset_index(drop=True)

# Separate display table: selected pool sorted by final decision priority.
selected_pool_display = selection_pool.copy()
selected_pool_display["selection_rule_used"] = selection_rule_used

display_cols = [
    "selection_rule_used",
    "esi5_weight_multiplier",
    "threshold",
    "accuracy",
    "macro_f1",
    "weighted_f1",
    "esi5_precision",
    "esi5_recall",
    "esi5_f1",
    "esi3_to_esi5_rate",
    "best_iteration",
]

print("Selection rule used:", selection_rule_used)
print("Selected LightGBM V2 multiplier:", best_lgb_v2_multiplier)
print("Selected LightGBM V2 threshold:", best_lgb_v2_threshold)
print("Selected validation unsafe downgrade rate:", f"{selected_v2_row['esi3_to_esi5_rate']:.4%}")
print("Selected validation Macro F1:", f"{selected_v2_row['macro_f1']:.4f}")
print("Selected validation ESI 5 F1:", f"{selected_v2_row['esi5_f1']:.4f}")

print("\nTop safety-eligible candidates by final decision ranking:")
print(selected_pool_display[display_cols].head(15))

print("\nFull candidate review sorted by lowest unsafe downgrade first:")
full_display_cols = [
    "selection_pool",
    "esi5_weight_multiplier",
    "threshold",
    "accuracy",
    "macro_f1",
    "weighted_f1",
    "esi5_precision",
    "esi5_recall",
    "esi5_f1",
    "esi3_to_esi5_rate",
    "best_iteration",
]
print(lgb_v2_validation_summary[full_display_cols].head(25))


lgb_v2_val_proba = best_lgb_v2_model.predict(
    X_lgb_val,
    num_iteration=best_lgb_v2_model.best_iteration,
)

lgb_v2_test_proba = best_lgb_v2_model.predict(
    X_lgb_test,
    num_iteration=best_lgb_v2_model.best_iteration,
)

lgb_v2_val_pred = predict_with_esi5_threshold(lgb_v2_val_proba, best_lgb_v2_threshold)
lgb_v2_test_pred = predict_with_esi5_threshold(lgb_v2_test_proba, best_lgb_v2_threshold)

lgb_v2_val_metrics = evaluate_predictions(
    y_val,
    lgb_v2_val_pred,
    f"{MODEL_DISPLAY_NAME} — Validation",
    probas=lgb_v2_val_proba,
    show_report=False,
    show_cm=False,
)

lgb_v2_test_metrics = evaluate_predictions(
    y_test,
    lgb_v2_test_pred,
    f"{MODEL_DISPLAY_NAME} — Test",
    probas=lgb_v2_test_proba,
)

metrics_test_path = REPORTS_DIR / "lightgbm_v3_test_metrics.json"
with open(metrics_test_path, "w") as f:
    json.dump(lgb_v2_test_metrics, f, indent=2)

validation_summary_path = REPORTS_DIR / "lightgbm_v3_validation_summary.csv"
lgb_v2_validation_summary.to_csv(validation_summary_path, index=False)

print("Saved test metrics:", metrics_test_path)
print("Saved validation summary:", validation_summary_path)

def normalize_rows(proba, eps=1e-12):
    proba = np.asarray(proba, dtype=float)
    proba = np.clip(proba, eps, 1.0)
    return proba / proba.sum(axis=1, keepdims=True)

def multiclass_brier_score(y_true, proba, n_classes=3):
    y_true = np.asarray(y_true).astype(int)
    proba = normalize_rows(proba)
    y_onehot = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((proba - y_onehot) ** 2, axis=1)))

def fit_isotonic_calibrators(y_cal, proba_cal, n_classes=3):
    calibrators = []
    y_cal = np.asarray(y_cal).astype(int)

    for k in range(n_classes):
        y_binary = (y_cal == k).astype(int)
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(proba_cal[:, k], y_binary)
        calibrators.append(iso)

    return calibrators

def apply_isotonic_calibration(proba, calibrators):
    calibrated = np.column_stack([
        calibrator.predict(proba[:, k])
        for k, calibrator in enumerate(calibrators)
    ])
    return normalize_rows(calibrated)

calibration_rows = []

calibration_rows.append({
    "method": "raw_lightgbm_probability",
    "test_brier": multiclass_brier_score(y_test, lgb_v2_test_proba),
    "test_log_loss": log_loss(y_test, normalize_rows(lgb_v2_test_proba), labels=[0, 1, 2]),
})

isotonic_calibrators = fit_isotonic_calibrators(y_val, lgb_v2_val_proba)
lgb_v2_test_proba_isotonic = apply_isotonic_calibration(lgb_v2_test_proba, isotonic_calibrators)

calibration_rows.append({
    "method": "isotonic_one_vs_rest_validation_calibrated",
    "test_brier": multiclass_brier_score(y_test, lgb_v2_test_proba_isotonic),
    "test_log_loss": log_loss(y_test, normalize_rows(lgb_v2_test_proba_isotonic), labels=[0, 1, 2]),
})

platt_calibrator = LogisticRegression(max_iter=1000, solver="lbfgs")
platt_calibrator.fit(lgb_v2_val_proba, y_val)
lgb_v2_test_proba_platt = platt_calibrator.predict_proba(lgb_v2_test_proba)

calibration_rows.append({
    "method": "platt_logistic_validation_calibrated",
    "test_brier": multiclass_brier_score(y_test, lgb_v2_test_proba_platt),
    "test_log_loss": log_loss(y_test, normalize_rows(lgb_v2_test_proba_platt), labels=[0, 1, 2]),
})

calibration_report = pd.DataFrame(calibration_rows).sort_values("test_brier")
print(calibration_report)

calibration_report_path = REPORTS_DIR / "probability_calibration_report.csv"
calibration_report.to_csv(calibration_report_path, index=False)

selected_calibration_method = "raw_lightgbm_probability"
selected_calibrator = None

if calibration_report.iloc[0]["method"] != "raw_lightgbm_probability":
    print("Calibration challenger improved probability score. Review decision metrics before production use.")
else:
    print("Raw LightGBM probabilities remain default.")

# ESI 5 reliability curve data
def reliability_curve_table(y_true, proba, class_index=2, n_bins=10):
    y_binary = (np.asarray(y_true) == class_index).astype(int)
    p = np.asarray(proba)[:, class_index]
    bins = np.linspace(0, 1, n_bins + 1)
    bin_ids = np.digitize(p, bins) - 1

    rows = []
    for b in range(n_bins):
        mask = bin_ids == b
        if mask.sum() == 0:
            continue
        rows.append({
            "bin": b,
            "mean_predicted_probability": float(p[mask].mean()),
            "observed_frequency": float(y_binary[mask].mean()),
            "count": int(mask.sum()),
        })

    return pd.DataFrame(rows)

esi5_reliability_df = reliability_curve_table(y_test, lgb_v2_test_proba, class_index=2)
esi5_reliability_df.to_csv(REPORTS_DIR / "esi5_reliability_curve_raw.csv", index=False)
print(esi5_reliability_df)

# ============================================================
# CALIBRATION DEPLOYMENT DECISION — SAFETY GUARDED
# ============================================================
# Goal:
# Calibration should improve probability quality, but it must not damage clinical decision metrics.
# Selection must be based on validation behavior; test metrics are only reported after the decision.

from sklearn.metrics import accuracy_score, f1_score

CALIBRATION_THRESHOLDS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75]

# Guardrails relative to the raw LightGBM champion.
# These tolerances are intentionally strict because ESI 5 is the minority class and is clinically important.
CALIBRATION_MACRO_F1_DROP_TOLERANCE = 0.0025   # max 0.25 percentage-point Macro F1 drop
CALIBRATION_ESI5_F1_DROP_TOLERANCE = 0.0050    # max 0.50 percentage-point ESI 5 F1 drop
CALIBRATION_UNSAFE_EXTRA_TOLERANCE = 0.0005    # max 0.05 percentage-point extra unsafe downgrade


def apply_esi5_threshold_rule(proba, esi5_threshold):
    """
    Decision rule:
    - Predict ESI 5 only when P(ESI 5) >= threshold.
    - Otherwise choose the best class between ESI 3 and ESI 4.
    """
    proba = normalize_rows(proba)

    esi5_mask = proba[:, 2] >= esi5_threshold
    non_esi5_best = np.argmax(proba[:, :2], axis=1)

    final_preds = non_esi5_best.copy()
    final_preds[esi5_mask] = 2

    return final_preds


def unsafe_esi3_to_esi5_rate(y_true, y_pred):
    """
    Measures unsafe downgrade:
    true ESI 3 predicted as ESI 5.
    """
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)

    esi3_mask = y_true == 0
    if esi3_mask.sum() == 0:
        return 0.0

    return float(((y_true == 0) & (y_pred == 2)).sum() / esi3_mask.sum())


def evaluate_decision_metrics(y_true, proba, threshold):
    proba = normalize_rows(proba)
    preds = apply_esi5_threshold_rule(proba, threshold)

    return {
        "threshold": float(threshold),
        "accuracy": accuracy_score(y_true, preds),
        "macro_f1": f1_score(y_true, preds, average="macro"),
        "weighted_f1": f1_score(y_true, preds, average="weighted"),
        "esi5_f1": f1_score(y_true, preds, labels=[2], average="macro"),
        "esi3_to_esi5_rate": unsafe_esi3_to_esi5_rate(y_true, preds),
        "brier_score": multiclass_brier_score(y_true, proba),
        "log_loss": log_loss(y_true, proba, labels=[0, 1, 2]),
    }


def tune_threshold_on_validation(y_val, proba_val, thresholds):
    """
    Tune threshold on validation only.
    Safety-first: filter by unsafe downgrade, then choose best Macro F1 / ESI 5 F1 / accuracy.
    """
    rows = []

    for threshold in thresholds:
        rows.append(evaluate_decision_metrics(y_val, proba_val, threshold))

    df = pd.DataFrame(rows)

    safe_df = df[df["esi3_to_esi5_rate"] <= SAFETY_TARGET_ESI3_TO_ESI5_RATE].copy()

    if safe_df.empty:
        safe_df = df[df["esi3_to_esi5_rate"] <= SAFETY_FALLBACK_ESI3_TO_ESI5_RATE].copy()

    if safe_df.empty:
        safe_df = df[df["esi3_to_esi5_rate"] <= SAFETY_LAST_RESORT_ESI3_TO_ESI5_RATE].copy()

    if safe_df.empty:
        safe_df = df.copy()

    selected = safe_df.sort_values(
        by=["macro_f1", "esi5_f1", "accuracy"],
        ascending=False
    ).iloc[0]

    return float(selected["threshold"]), df


calibration_candidates = {
    "raw_lightgbm_probability": {
        "val_proba": lgb_v2_val_proba,
        "test_proba": lgb_v2_test_proba,
        "calibrator": None,
    },
    "isotonic_calibrated_probability": {
        "val_proba": apply_isotonic_calibration(lgb_v2_val_proba, isotonic_calibrators),
        "test_proba": lgb_v2_test_proba_isotonic,
        "calibrator": isotonic_calibrators,
    },
    "platt_calibrated_probability": {
        "val_proba": platt_calibrator.predict_proba(lgb_v2_val_proba),
        "test_proba": lgb_v2_test_proba_platt,
        "calibrator": platt_calibrator,
    },
}

# Raw champion baseline uses the already selected LightGBM V2 threshold.
raw_val_metrics = evaluate_decision_metrics(
    y_true=y_val,
    proba=lgb_v2_val_proba,
    threshold=best_lgb_v2_threshold,
)

raw_test_metrics = evaluate_decision_metrics(
    y_true=y_test,
    proba=lgb_v2_test_proba,
    threshold=best_lgb_v2_threshold,
)

calibration_decision_rows = []
calibration_threshold_search_tables = {}

for method_name, obj in calibration_candidates.items():
    if method_name == "raw_lightgbm_probability":
        selected_threshold = float(best_lgb_v2_threshold)
        threshold_table = pd.DataFrame([raw_val_metrics])
    else:
        selected_threshold, threshold_table = tune_threshold_on_validation(
            y_val=y_val,
            proba_val=obj["val_proba"],
            thresholds=CALIBRATION_THRESHOLDS,
        )

    calibration_threshold_search_tables[method_name] = threshold_table

    val_metrics = evaluate_decision_metrics(
        y_true=y_val,
        proba=obj["val_proba"],
        threshold=selected_threshold,
    )

    test_metrics = evaluate_decision_metrics(
        y_true=y_test,
        proba=obj["test_proba"],
        threshold=selected_threshold,
    )

    probability_quality_improved = (
        (val_metrics["brier_score"] < raw_val_metrics["brier_score"]) or
        (val_metrics["log_loss"] < raw_val_metrics["log_loss"])
    )

    macro_preserved = val_metrics["macro_f1"] >= (
        raw_val_metrics["macro_f1"] - CALIBRATION_MACRO_F1_DROP_TOLERANCE
    )

    esi5_preserved = val_metrics["esi5_f1"] >= (
        raw_val_metrics["esi5_f1"] - CALIBRATION_ESI5_F1_DROP_TOLERANCE
    )

    unsafe_preserved = (
        val_metrics["esi3_to_esi5_rate"] <= SAFETY_TARGET_ESI3_TO_ESI5_RATE
    ) and (
        val_metrics["esi3_to_esi5_rate"] <=
        raw_val_metrics["esi3_to_esi5_rate"] + CALIBRATION_UNSAFE_EXTRA_TOLERANCE
    )

    if method_name == "raw_lightgbm_probability":
        eligible_for_deployment = True
        deploy_calibrated_method = False
        decision_reason = "raw champion baseline"
    else:
        eligible_for_deployment = (
            probability_quality_improved and
            macro_preserved and
            esi5_preserved and
            unsafe_preserved
        )
        deploy_calibrated_method = eligible_for_deployment
        failed_checks = []
        if not probability_quality_improved:
            failed_checks.append("probability quality did not improve")
        if not macro_preserved:
            failed_checks.append("Macro F1 not preserved")
        if not esi5_preserved:
            failed_checks.append("ESI 5 F1 not preserved")
        if not unsafe_preserved:
            failed_checks.append("unsafe downgrade safety not preserved")
        decision_reason = "eligible calibrated challenger" if eligible_for_deployment else "; ".join(failed_checks)

    row = {
        "method": method_name,
        "selected_threshold": selected_threshold,
        "deploy_calibrated_method": deploy_calibrated_method,
        "eligible_for_deployment": eligible_for_deployment,
        "decision_reason": decision_reason,

        "val_accuracy": val_metrics["accuracy"],
        "val_macro_f1": val_metrics["macro_f1"],
        "val_weighted_f1": val_metrics["weighted_f1"],
        "val_esi5_f1": val_metrics["esi5_f1"],
        "val_esi3_to_esi5_rate": val_metrics["esi3_to_esi5_rate"],
        "val_brier_score": val_metrics["brier_score"],
        "val_log_loss": val_metrics["log_loss"],

        "test_accuracy": test_metrics["accuracy"],
        "test_macro_f1": test_metrics["macro_f1"],
        "test_weighted_f1": test_metrics["weighted_f1"],
        "test_esi5_f1": test_metrics["esi5_f1"],
        "test_esi3_to_esi5_rate": test_metrics["esi3_to_esi5_rate"],
        "test_brier_score": test_metrics["brier_score"],
        "test_log_loss": test_metrics["log_loss"],

        "val_macro_f1_delta_vs_raw": val_metrics["macro_f1"] - raw_val_metrics["macro_f1"],
        "val_esi5_f1_delta_vs_raw": val_metrics["esi5_f1"] - raw_val_metrics["esi5_f1"],
        "val_unsafe_delta_vs_raw": val_metrics["esi3_to_esi5_rate"] - raw_val_metrics["esi3_to_esi5_rate"],
        "val_brier_delta_vs_raw": val_metrics["brier_score"] - raw_val_metrics["brier_score"],
        "val_log_loss_delta_vs_raw": val_metrics["log_loss"] - raw_val_metrics["log_loss"],
    }

    calibration_decision_rows.append(row)

calibration_deployment_decision = pd.DataFrame(calibration_decision_rows)

# Selection rule:
# Prefer a calibrated challenger only if it passes guardrails.
# If no calibrated challenger passes, keep raw LightGBM probabilities as the deployment default.
eligible_calibrated = calibration_deployment_decision[
    (calibration_deployment_decision["eligible_for_deployment"]) &
    (calibration_deployment_decision["deploy_calibrated_method"])
].copy()

if not eligible_calibrated.empty:
    selected_row = eligible_calibrated.sort_values(
        by=["val_brier_score", "val_log_loss", "val_macro_f1", "val_esi5_f1"],
        ascending=[True, True, False, False],
    ).iloc[0]
else:
    selected_row = calibration_deployment_decision[
        calibration_deployment_decision["method"] == "raw_lightgbm_probability"
    ].iloc[0]

selected_calibration_method = selected_row["method"]
selected_calibration_threshold = float(selected_row["selected_threshold"])
deploy_calibrated_probabilities = bool(selected_row["deploy_calibrated_method"])
selected_deployment_threshold = selected_calibration_threshold

if selected_calibration_method == "raw_lightgbm_probability":
    selected_calibrator = None
else:
    selected_calibrator = calibration_candidates[selected_calibration_method]["calibrator"]

calibration_deployment_decision = calibration_deployment_decision.sort_values(
    by=["eligible_for_deployment", "deploy_calibrated_method", "val_brier_score", "val_macro_f1"],
    ascending=[False, False, True, False],
)

display_columns = [
    "method",
    "selected_threshold",
    "eligible_for_deployment",
    "deploy_calibrated_method",
    "decision_reason",
    "val_macro_f1",
    "val_esi5_f1",
    "val_esi3_to_esi5_rate",
    "val_brier_score",
    "test_macro_f1",
    "test_esi5_f1",
    "test_esi3_to_esi5_rate",
    "test_brier_score",
]

print(calibration_deployment_decision[display_columns])

calibration_deployment_decision_path = REPORTS_DIR / "calibration_deployment_decision.csv"
calibration_deployment_decision.to_csv(calibration_deployment_decision_path, index=False)

print("Selected calibration method:", selected_calibration_method)
print("Selected deployment threshold:", selected_deployment_threshold)
print("Deploy calibrated probabilities:", deploy_calibrated_probabilities)

if deploy_calibrated_probabilities:
    print("Calibration will be used in deployment because it passed probability and clinical guardrails.")
else:
    print("Raw LightGBM probabilities remain deployment default because calibrated challengers did not preserve all clinical guardrails.")


def add_subgroup_columns(df_part):
    out = df_part.copy()

    if "age" in out.columns:
        out["age_group_eval"] = pd.cut(
            pd.to_numeric(out["age"], errors="coerce"),
            bins=[-np.inf, 17, 44, 64, np.inf],
            labels=["0-17", "18-44", "45-64", "65+"],
        ).astype(str)
    else:
        out["age_group_eval"] = "Unknown"

    if "gender" not in out.columns:
        out["gender"] = "Unknown"

    if "arrivalmode" not in out.columns:
        out["arrivalmode"] = "Unknown"

    out["missing_vital_group_eval"] = np.where(
        out.get("total_vitals_missing", pd.Series(0, index=out.index)).astype(float) >= 3,
        "3+ missing vitals",
        "0-2 missing vitals",
    )

    def primary_complaint_group(row):
        for col in complaint_group_cols:
            if int(row.get(col, 0) or 0) == 1:
                return col.replace("cc_group_", "")
        return "other_or_unknown"

    out["primary_complaint_group_eval"] = out.apply(primary_complaint_group, axis=1)
    return out

def subgroup_metrics_table(df_part, y_true, y_pred, group_col, min_n=100):
    df_eval = df_part.copy()
    df_eval["_y_true"] = np.asarray(y_true)
    df_eval["_y_pred"] = np.asarray(y_pred)

    rows = []
    for group_value, g in df_eval.groupby(group_col, dropna=False):
        if len(g) < min_n:
            continue

        metrics = evaluate_predictions(
            g["_y_true"].values,
            g["_y_pred"].values,
            f"{group_col}={group_value}",
            show_report=False,
            show_cm=False,
            verbose=False,
        )

        rows.append({
            "group_column": group_col,
            "group_value": str(group_value),
            "n": int(len(g)),
            "accuracy": metrics["accuracy"],
            "macro_f1": metrics["macro_f1"],
            "weighted_f1": metrics["weighted_f1"],
            "esi5_f1": metrics["esi5_f1"],
            "esi3_to_esi5_rate": metrics["esi3_to_esi5_rate"],
        })

    return pd.DataFrame(rows).sort_values(["group_column", "macro_f1"], ascending=[True, True])

test_eval_df = add_subgroup_columns(test_df)

subgroup_tables = []
for group_col in [
    "age_group_eval",
    "gender",
    "arrivalmode",
    "primary_complaint_group_eval",
    "missing_vital_group_eval",
]:
    subgroup_tables.append(subgroup_metrics_table(test_eval_df, y_test, lgb_v2_test_pred, group_col))

fairness_report = pd.concat(subgroup_tables, ignore_index=True)
print(fairness_report)

fairness_report_path = REPORTS_DIR / "fairness_subgroup_evaluation.csv"
fairness_report.to_csv(fairness_report_path, index=False)

print("Saved fairness report:", fairness_report_path)

RUN_SHAP = True

if RUN_SHAP:
    import shap

    shap_sample_size = min(3000, X_lgb_test.shape[0])
    X_shap = X_lgb_test[:shap_sample_size]

    explainer = shap.TreeExplainer(best_lgb_v2_model)
    shap_values = explainer.shap_values(X_shap)

    plt.figure(figsize=(10, 7))
    shap.summary_plot(
        shap_values,
        X_shap,
        feature_names=feature_columns_lgb,
        max_display=20,
        show=False,
        plot_type="bar",
    )
    plt.title("LightGBM V2 SHAP Feature Importance — Top 20")
    plt.tight_layout()
    plt.close()

    if isinstance(shap_values, list):
        mean_abs = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
    else:
        arr = np.asarray(shap_values)
        if arr.ndim == 3:
            mean_abs = np.abs(arr).mean(axis=(0, 2))
        else:
            mean_abs = np.abs(arr).mean(axis=0)

    shap_importance = pd.DataFrame({
        "feature": feature_columns_lgb,
        "mean_abs_shap": mean_abs,
    }).sort_values("mean_abs_shap", ascending=False)

    shap_importance_path = REPORTS_DIR / "shap_global_feature_importance.csv"
    shap_importance.to_csv(shap_importance_path, index=False)
    print(shap_importance.head(25))
else:
    print("SHAP skipped. Set RUN_SHAP = True to generate explanation reports.")

def transform_for_lgb(raw_df, artifacts):
    df_in = raw_df.copy()

    for col in artifacts["selected_feature_cols"]:
        if col not in df_in.columns:
            if col in artifacts["numeric_cols"] or col in artifacts["categorical_cols"]:
                df_in[col] = np.nan
            else:
                df_in[col] = 0

    cc_columns = artifacts["cc_cols"]
    df_in, _, _, _ = create_row_level_features(df_in, cc_columns)
    df_in, _ = apply_clinical_ranges(df_in)

    for col in artifacts["numeric_cols_extended"]:
        if col not in df_in.columns:
            df_in[col] = np.nan
        df_in[col] = pd.to_numeric(df_in[col], errors="coerce")
        df_in[col] = df_in[col].fillna(artifacts["numeric_medians"].get(col, 0.0))

    X_num = df_in[artifacts["existing_numeric_cols"]].astype("float32").values

    for col in artifacts["categorical_cols"]:
        if col not in df_in.columns:
            df_in[col] = "Missing"
        df_in[col] = df_in[col].fillna("Missing").astype(str)

    if artifacts["categorical_cols"]:
        X_cat = artifacts["onehot_encoder"].transform(df_in[artifacts["categorical_cols"]])
    else:
        X_cat = np.empty((len(df_in), 0))

    for col in cc_columns:
        if col not in df_in.columns:
            df_in[col] = 0
        df_in[col] = df_in[col].fillna(0).astype("int8")

    X_cc = df_in[cc_columns].astype("float32").values if cc_columns else np.empty((len(df_in), 0))
    X = np.hstack([X_num, X_cat.astype("float32"), X_cc])

    expected_n = len(artifacts["feature_columns_lgb"])
    if X.shape[1] != expected_n:
        raise ValueError(f"Feature mismatch. Got {X.shape[1]}, expected {expected_n}.")

    return X, df_in


def maybe_apply_deployment_calibration(proba, artifacts):
    """
    Applies the saved calibration method only if the deployment decision approved it.
    If calibration was evaluated but rejected, raw LightGBM probabilities are used.
    """
    proba = normalize_rows(np.asarray(proba))

    calibration_cfg = artifacts.get("calibration", {})
    deploy_calibrated = calibration_cfg.get("deploy_calibrated_probabilities", False)
    selected_method = calibration_cfg.get("selected_calibration_method", "raw_lightgbm_probability")

    if not deploy_calibrated or selected_method == "raw_lightgbm_probability":
        return proba

    if selected_method == "isotonic_calibrated_probability":
        calibrators = calibration_cfg.get("isotonic_calibrators")
        if calibrators is None:
            raise ValueError("Isotonic calibration selected, but isotonic calibrators are missing.")
        return apply_isotonic_calibration(proba, calibrators)

    if selected_method == "platt_calibrated_probability":
        calibrator = calibration_cfg.get("platt_calibrator")
        if calibrator is None:
            raise ValueError("Platt calibration selected, but Platt calibrator is missing.")
        return normalize_rows(calibrator.predict_proba(proba))

    raise ValueError(f"Unknown calibration method: {selected_method}")


def make_decision_output(proba, esi5_threshold, model_name=MODEL_DISPLAY_NAME, calibration_method="raw_lightgbm_probability"):
    proba = np.asarray(proba).reshape(1, -1)
    pred_label = int(predict_with_esi5_threshold(proba.copy(), esi5_threshold)[0])
    confidence = float(proba[0, pred_label])

    return {
        "model_version": MODEL_VERSION,
        "model_name": model_name,
        "calibration_method": calibration_method,
        "predicted_label": pred_label,
        "predicted_esi": int(reverse_label_map[pred_label]),
        "class_name": class_names[pred_label],
        "confidence": confidence,
        "prob_esi3": float(proba[0, 0]),
        "prob_esi4": float(proba[0, 1]),
        "prob_esi5": float(proba[0, 2]),
        "low_confidence_review": confidence < CONFIDENCE_THRESHOLD,
        "esi5_threshold": float(esi5_threshold),
        "decision_support_note": (
            "Clinical decision-support result for ESI 3/4/5 only. "
            "Not a diagnosis and not a replacement for clinician judgment."
        ),
    }


def predict_single_patient(patient_dict, model, artifacts):
    raw = pd.DataFrame([patient_dict])

    gate_df, _, _, _ = create_row_level_features(raw, artifacts["cc_cols"])
    gate_result = apply_esi12_safety_gate(gate_df.iloc[0])

    if gate_result["safety_gate_triggered"]:
        return {
            "model_version": MODEL_VERSION,
            "safety_gate_triggered": True,
            "red_flags": gate_result["red_flags"],
            "recommended_route": gate_result["recommended_route"],
            "prediction_skipped_reason": "ESI 1/2 red-flag safety gate triggered before ESI 3/4/5 model.",
            "decision_support_note": gate_result["safety_gate_note"],
        }

    X, transformed_df = transform_for_lgb(raw, artifacts)
    raw_proba = model.predict(X, num_iteration=model.best_iteration)
    deploy_proba = maybe_apply_deployment_calibration(raw_proba, artifacts)

    calibration_cfg = artifacts.get("calibration", {})
    selected_method = calibration_cfg.get("selected_calibration_method", "raw_lightgbm_probability")
    deployment_threshold = artifacts.get(
        "deployment_threshold",
        calibration_cfg.get("selected_calibration_threshold", artifacts["best_lgb_v2_threshold"]),
    )

    output = make_decision_output(
        deploy_proba[0],
        esi5_threshold=deployment_threshold,
        model_name=MODEL_DISPLAY_NAME,
        calibration_method=selected_method,
    )
    output["safety_gate_triggered"] = False
    output["red_flags"] = []
    output["recommended_route"] = "esi_3_4_5_decision_support"
    return output


in_memory_artifacts = {
    "selected_feature_cols": selected_feature_cols,
    "categorical_cols": categorical_cols,
    "numeric_cols": numeric_cols,
    "cc_cols": cc_cols,
    "numeric_cols_extended": numeric_cols_extended,
    "existing_numeric_cols": existing_numeric_cols,
    "numeric_medians": numeric_medians,
    "onehot_encoder": onehot_encoder,
    "feature_columns_lgb": feature_columns_lgb,
    "best_lgb_v2_threshold": best_lgb_v2_threshold,
    "deployment_threshold": selected_deployment_threshold,
    "calibration": {
        "selected_calibration_method": selected_calibration_method,
        "selected_calibration_threshold": selected_calibration_threshold,
        "deploy_calibrated_probabilities": deploy_calibrated_probabilities,
        "isotonic_calibrators": isotonic_calibrators,
        "platt_calibrator": platt_calibrator,
    },
}

sample_patient = test_df.iloc[0][selected_feature_cols].to_dict()
sample_prediction = predict_single_patient(sample_patient, best_lgb_v2_model, in_memory_artifacts)
sample_prediction


def log_prediction_event(
    prediction_id,
    prediction_output,
    patient_reference=None,
    clinician_action=None,
    clinician_final_esi=None,
    clinician_note=None,
    audit_log_path=AUDIT_LOG_PATH,
):
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "prediction_id": prediction_id,
        "patient_reference": patient_reference,
        "model_version": prediction_output.get("model_version"),
        "model_name": prediction_output.get("model_name"),
        "safety_gate_triggered": prediction_output.get("safety_gate_triggered"),
        "red_flags": prediction_output.get("red_flags", []),
        "recommended_route": prediction_output.get("recommended_route"),
        "predicted_esi": prediction_output.get("predicted_esi"),
        "confidence": prediction_output.get("confidence"),
        "prob_esi3": prediction_output.get("prob_esi3"),
        "prob_esi4": prediction_output.get("prob_esi4"),
        "prob_esi5": prediction_output.get("prob_esi5"),
        "low_confidence_review": prediction_output.get("low_confidence_review"),
        "clinician_action": clinician_action,
        "clinician_final_esi": clinician_final_esi,
        "clinician_note": clinician_note,
    }

    audit_log_path = Path(audit_log_path)
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(audit_log_path, "a") as f:
        f.write(json.dumps(record) + "\n")

    return record

sample_audit = log_prediction_event(
    prediction_id="sample-001",
    prediction_output=sample_prediction,
    patient_reference="demo_patient",
    clinician_action="pending",
)

sample_audit

# Compatibility variable for artifact metadata
# This keeps old artifact text working with the safety-tuned selection logic.

if "selected_safety_limit" in globals():
    V2_MAX_ESI3_TO_ESI5_RATE = selected_safety_limit
elif "SAFETY_TARGET_ESI3_TO_ESI5_RATE" in globals():
    V2_MAX_ESI3_TO_ESI5_RATE = SAFETY_TARGET_ESI3_TO_ESI5_RATE
else:
    V2_MAX_ESI3_TO_ESI5_RATE = 0.0075

if "selected_deployment_threshold" not in globals():
    selected_deployment_threshold = best_lgb_v2_threshold

if "deploy_calibrated_probabilities" not in globals():
    deploy_calibrated_probabilities = False

if "selected_calibration_method" not in globals():
    selected_calibration_method = "raw_lightgbm_probability"

if "selected_calibration_threshold" not in globals():
    selected_calibration_threshold = best_lgb_v2_threshold

if "calibration_deployment_decision_path" not in globals():
    calibration_deployment_decision_path = REPORTS_DIR / "calibration_deployment_decision.csv"

print("Artifact metadata safety limit:", V2_MAX_ESI3_TO_ESI5_RATE)
print("Selected calibration method:", selected_calibration_method)
print("Selected deployment threshold:", selected_deployment_threshold)
print("Deploy calibrated probabilities:", deploy_calibrated_probabilities)


# Now artifact saving starts
model_path = OUTPUT_DIR / "esi_345_lightgbm_v2_model.txt"
best_lgb_v2_model.save_model(str(model_path))

optional_experiment_artifacts = {
    "scaler_dense": None,
    "scaler_struct": None,
    "tokenizer": None,
    "note": (
        "Scaler/tokenizer are not required for the final LightGBM V2 deployment model. "
        "They are only needed if neural/RNN/GRU experiments are deployed later."
    ),
}

preprocessing_artifacts = {
    "model_version": MODEL_VERSION,
    "model_display_name": MODEL_DISPLAY_NAME,
    "feature_policy": {
        "blocked_risky_cols": blocked_risky_cols,
        "use_previousdispo": USE_PREVIOUS_DISPO,
        "selected_feature_cols": selected_feature_cols,
        "categorical_cols": categorical_cols,
        "numeric_cols": numeric_cols,
        "numeric_cols_extended": numeric_cols_extended,
        "clinical_feature_cols": clinical_feature_cols,
        "complaint_group_cols": complaint_group_cols,
        "complaint_group_specs": complaint_group_specs,
        "cc_cols": cc_cols,
    },
    "selected_feature_cols": selected_feature_cols,
    "categorical_cols": categorical_cols,
    "numeric_cols": numeric_cols,
    "cc_cols": cc_cols,
    "numeric_cols_extended": numeric_cols_extended,
    "existing_numeric_cols": existing_numeric_cols,
    "numeric_medians": numeric_medians,
    "onehot_encoder": onehot_encoder,
    "feature_columns_lgb": feature_columns_lgb,
    "raw_feature_columns_lgb": raw_feature_columns_lgb,
    "label_map": label_map,
    "reverse_label_map": reverse_label_map,
    "class_names": class_names,
    "class_weights_base": class_weights,
    "class_weights_final_v2": best_lgb_v2_class_weights,
    "best_lgb_v2_multiplier": best_lgb_v2_multiplier,
    "best_lgb_v2_threshold": best_lgb_v2_threshold,
    "deployment_threshold": selected_deployment_threshold,
    "confidence_threshold": CONFIDENCE_THRESHOLD,
    "clinical_ranges": clinical_ranges,
    "safety_gate_config": SAFETY_GATE_CONFIG,
    "calibration": {
        "selected_calibration_method": selected_calibration_method,
        "selected_calibration_threshold": selected_calibration_threshold,
        "deploy_calibrated_probabilities": deploy_calibrated_probabilities,
        "isotonic_calibrators": isotonic_calibrators,
        "platt_calibrator": platt_calibrator,
        "calibration_report_path": str(calibration_report_path),
        "calibration_deployment_decision_path": str(calibration_deployment_decision_path),
        "note": (
            "Calibration is deployed only if it improves probability quality while preserving "
            "Macro F1, ESI 5 F1, and unsafe ESI 3-to-ESI 5 downgrade safety."
        ),
    },
    "optional_experiment_artifacts": optional_experiment_artifacts,
}

artifacts_path = OUTPUT_DIR / "esi_345_lightgbm_v2_preprocessing_artifacts.joblib"
joblib.dump(preprocessing_artifacts, artifacts_path)

feature_list_path = OUTPUT_DIR / "esi_345_lightgbm_v2_feature_list.json"
with open(feature_list_path, "w") as f:
    json.dump(feature_columns_lgb, f, indent=2)

threshold_config_path = OUTPUT_DIR / "esi_345_lightgbm_v2_threshold_config.json"

with open(threshold_config_path, "w") as f:
    json.dump({
        "model_version": MODEL_VERSION,
        "best_lgb_v2_threshold": best_lgb_v2_threshold,
        "best_lgb_v2_multiplier": best_lgb_v2_multiplier,
        "deployment_threshold": selected_deployment_threshold,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "selected_calibration_method": selected_calibration_method,
        "selected_calibration_threshold": selected_calibration_threshold,
        "deploy_calibrated_probabilities": deploy_calibrated_probabilities,
        "safety_target_esi3_to_esi5_rate": SAFETY_TARGET_ESI3_TO_ESI5_RATE,
        "safety_fallback_esi3_to_esi5_rate": SAFETY_FALLBACK_ESI3_TO_ESI5_RATE,
        "safety_last_resort_esi3_to_esi5_rate": SAFETY_LAST_RESORT_ESI3_TO_ESI5_RATE,
        "selection_rule": (
            "Safety-first selection. Candidates are first filtered by unsafe ESI 3-to-ESI 5 "
            f"downgrade rate using target <= {SAFETY_TARGET_ESI3_TO_ESI5_RATE:.3f}, "
            f"fallback <= {SAFETY_FALLBACK_ESI3_TO_ESI5_RATE:.3f}, "
            f"and last-resort <= {SAFETY_LAST_RESORT_ESI3_TO_ESI5_RATE:.3f}. "
            "Calibration is deployed only when probability quality improves and clinical guardrails "
            "for Macro F1, ESI 5 F1, and unsafe downgrade rate are preserved."
        ),
    }, f, indent=2)

label_mapping_path = OUTPUT_DIR / "esi_345_label_mapping.json"
with open(label_mapping_path, "w") as f:
    json.dump({
        "label_map": {str(k): int(v) for k, v in label_map.items()},
        "reverse_label_map": {str(k): int(v) for k, v in reverse_label_map.items()},
        "class_names": class_names,
    }, f, indent=2)

deployment_config_path = OUTPUT_DIR / "esi_345_deployment_config.json"
with open(deployment_config_path, "w") as f:
    json.dump({
        "project": "TriageAI / SympDirect",
        "task": "client_focused_esi_3_4_5",
        "model_version": MODEL_VERSION,
        "model_display_name": MODEL_DISPLAY_NAME,
        "model_file": model_path.name,
        "preprocessing_artifacts_file": artifacts_path.name,
        "feature_list_file": feature_list_path.name,
        "threshold_config_file": threshold_config_path.name,
        "label_mapping_file": label_mapping_path.name,
        "target_source_column": "esi",
        "derived_label_column": "esi_label",
        "deployment_threshold": selected_deployment_threshold,
        "selected_calibration_method": selected_calibration_method,
        "deploy_calibrated_probabilities": deploy_calibrated_probabilities,
        "important_warning": "This model excludes ESI 1 and ESI 2. Use the safety gate before this model.",
        "clinical_safety_wording": "Decision support only. Not a diagnostic tool. Does not replace clinicians.",
    }, f, indent=2)

artifact_manifest = {
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "model_version": MODEL_VERSION,
    "required_deployment_artifacts": {
        "model_file": str(model_path),
        "feature_list": str(feature_list_path),
        "onehot_encoder_and_medians": str(artifacts_path),
        "threshold_config": str(threshold_config_path),
        "label_mapping": str(label_mapping_path),
        "deployment_config": str(deployment_config_path),
    },
    "reports": {
        "test_metrics": str(metrics_test_path),
        "validation_summary": str(validation_summary_path),
        "calibration_report": str(calibration_report_path),
        "calibration_deployment_decision": str(calibration_deployment_decision_path),
        "fairness_subgroup_report": str(fairness_report_path),
    },
    "optional_not_deployed": {
        "scaler": "not required for LightGBM V2 deployment",
        "tokenizer": "not required for LightGBM V2 deployment",
    },
}

manifest_path = OUTPUT_DIR / "artifact_manifest.json"
with open(manifest_path, "w") as f:
    json.dump(artifact_manifest, f, indent=2)

print("Saved final deployment artifacts:")
for k, v in artifact_manifest["required_deployment_artifacts"].items():
    print(f"  {k}: {v}")


required_paths = [
    model_path,
    artifacts_path,
    feature_list_path,
    threshold_config_path,
    label_mapping_path,
    deployment_config_path,
    manifest_path,
    metrics_test_path,
    validation_summary_path,
    calibration_report_path,
    calibration_deployment_decision_path,
    fairness_report_path,
]

missing = [str(p) for p in required_paths if not Path(p).exists()]

if missing:
    raise FileNotFoundError(f"Missing deployment artifacts: {missing}")

loaded_artifacts = joblib.load(artifacts_path)

assert loaded_artifacts["feature_columns_lgb"] == feature_columns_lgb
assert loaded_artifacts["label_map"] == label_map
assert loaded_artifacts["reverse_label_map"] == reverse_label_map
assert "onehot_encoder" in loaded_artifacts
assert "numeric_medians" in loaded_artifacts
assert "best_lgb_v2_threshold" in loaded_artifacts
assert "deployment_threshold" in loaded_artifacts
assert "calibration" in loaded_artifacts

print("Deployment artifact check PASSED.")
print("Final model file:", model_path)
print("Final preprocessing artifacts:", artifacts_path)
print("Final model threshold:", loaded_artifacts["best_lgb_v2_threshold"])
print("Final deployment threshold:", loaded_artifacts["deployment_threshold"])
print("Selected calibration method:", loaded_artifacts["calibration"]["selected_calibration_method"])
print("Deploy calibrated probabilities:", loaded_artifacts["calibration"]["deploy_calibrated_probabilities"])
print("Feature count:", len(loaded_artifacts["feature_columns_lgb"]))


