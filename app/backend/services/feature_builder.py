"""Explainable intake feature building for ESI 3/4/5 inference."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from app.backend.schemas.intake import PatientIntakeRequest


SEVERE_KEYWORDS = {
    "severe",
    "crushing",
    "unresponsive",
    "confusion",
    "confused",
    "fainting",
    "syncope",
    "heavy bleeding",
    "bleeding heavily",
}


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.lower()).strip()


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def build_raw_features_from_intake(intake: PatientIntakeRequest) -> dict[str, Any]:
    complaint_clean = _clean_text(intake.chief_complaint)
    context_clean = _clean_text(intake.additional_context)
    combined_text = f"{complaint_clean} {context_clean}".strip()

    systolic_bp = intake.systolic_bp
    diastolic_bp = intake.diastolic_bp
    heart_rate = intake.heart_rate
    oxygen_saturation = intake.oxygen_saturation
    respiratory_rate = intake.respiratory_rate
    temperature_c = intake.temperature_c

    pulse_pressure = None
    if systolic_bp is not None and diastolic_bp is not None:
        pulse_pressure = systolic_bp - diastolic_bp

    mean_arterial_pressure = None
    if systolic_bp is not None and diastolic_bp is not None:
        mean_arterial_pressure = (systolic_bp + (2 * diastolic_bp)) / 3

    shock_index = None
    if heart_rate is not None and systolic_bp:
        shock_index = heart_rate / systolic_bp

    abnormal_vital_count = sum(
        [
            int(heart_rate is not None and (heart_rate < 50 or heart_rate > 120)),
            int(systolic_bp is not None and systolic_bp < 90),
            int(oxygen_saturation is not None and oxygen_saturation < 92),
            int(respiratory_rate is not None and respiratory_rate > 24),
            int(temperature_c is not None and temperature_c >= 38.0),
        ]
    )

    features = {
        "patient_age": intake.patient_age,
        "age": intake.patient_age,
        "sex": intake.sex,
        "chief_complaint": intake.chief_complaint,
        "symptom_duration": intake.symptom_duration,
        "pain_score": intake.pain_score,
        "temperature_c": temperature_c,
        "heart_rate": heart_rate,
        "respiratory_rate": respiratory_rate,
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "oxygen_saturation": oxygen_saturation,
        "triage_vital_hr": heart_rate,
        "triage_vital_sbp": systolic_bp,
        "triage_vital_dbp": diastolic_bp,
        "triage_vital_rr": respiratory_rate,
        "triage_vital_o2": oxygen_saturation,
        "triage_vital_temp": temperature_c,
        "o2_missing_flag": int(oxygen_saturation is None),
        "total_vitals_missing": sum(
            vital is None
            for vital in [
                heart_rate,
                systolic_bp,
                diastolic_bp,
                respiratory_rate,
                oxygen_saturation,
                temperature_c,
            ]
        ),
        "shock_index": shock_index,
        "pulse_pressure": pulse_pressure,
        "mean_arterial_pressure": mean_arterial_pressure,
        "abnormal_hr_flag": int(heart_rate is not None and (heart_rate < 50 or heart_rate > 120)),
        "low_sbp_flag": int(systolic_bp is not None and systolic_bp < 90),
        "low_o2_flag": int(oxygen_saturation is not None and oxygen_saturation < 92),
        "high_rr_flag": int(respiratory_rate is not None and respiratory_rate > 24),
        "fever_flag": int(temperature_c is not None and temperature_c >= 38.0),
        "abnormal_vital_count": abnormal_vital_count,
        "triage_vital_hr_missing_flag": int(heart_rate is None),
        "triage_vital_sbp_missing_flag": int(systolic_bp is None),
        "triage_vital_dbp_missing_flag": int(diastolic_bp is None),
        "triage_vital_rr_missing_flag": int(respiratory_rate is None),
        "triage_vital_o2_missing_flag": int(oxygen_saturation is None),
        "triage_vital_temp_missing_flag": int(temperature_c is None),
        "consciousness_level": intake.consciousness_level,
        "pregnancy": intake.pregnancy,
        "arrival_mode": intake.arrival_mode,
        "additional_context": intake.additional_context,
        "chief_complaint_clean": complaint_clean,
        "complaint_length": len(complaint_clean),
        "has_chest_pain": int(_contains_any(combined_text, ("chest pain", "chest discomfort"))),
        "has_shortness_of_breath": int(
            _contains_any(
                combined_text,
                ("shortness of breath", "sob", "difficulty breathing", "breathless"),
            )
        ),
        "has_fever": int(_contains_any(combined_text, ("fever", "febrile"))),
        "has_abdominal_pain": int(
            _contains_any(combined_text, ("abdominal pain", "stomach pain", "abdomen"))
        ),
        "has_headache": int(_contains_any(combined_text, ("headache", "migraine"))),
        "has_dizziness": int(_contains_any(combined_text, ("dizzy", "dizziness", "vertigo"))),
        "has_bleeding": int(_contains_any(combined_text, ("bleeding", "blood loss", "hemorrhage"))),
        "has_vomiting": int(_contains_any(combined_text, ("vomiting", "vomit", "emesis"))),
        "has_injury": int(_contains_any(combined_text, ("injury", "trauma", "fall", "fracture"))),
        "has_confusion": int(_contains_any(combined_text, ("confusion", "confused", "altered"))),
        "has_severe_keyword": int(any(keyword in combined_text for keyword in SEVERE_KEYWORDS)),
    }

    features.update(
        {
            "cc_chestpain": features["has_chest_pain"],
            "cc_shortnessofbreath": features["has_shortness_of_breath"],
            "cc_fever": features["has_fever"],
            "cc_abdominalpain": features["has_abdominal_pain"],
            "cc_headache": features["has_headache"],
            "cc_dizziness": features["has_dizziness"],
            "cc_vaginalbleeding": int("vaginal bleeding" in combined_text),
            "cc_bleeding_bruising": features["has_bleeding"],
            "cc_vomiting": features["has_vomiting"],
            "cc_trauma": features["has_injury"],
            "cc_confusion": features["has_confusion"],
            "cc_group_cardiac": features["has_chest_pain"],
            "cc_group_respiratory": features["has_shortness_of_breath"],
            "cc_group_abdominal": features["has_abdominal_pain"],
            "cc_group_trauma": features["has_injury"],
            "cc_group_neuro": int(
                bool(features["has_headache"] or features["has_dizziness"] or features["has_confusion"])
            ),
            "cc_group_infection": features["has_fever"],
            "cc_group_minor_msk_skin": 0,
            "gender_Female": int((intake.sex or "").lower() == "female"),
            "gender_Male": int((intake.sex or "").lower() == "male"),
        }
    )

    arrival_mode = (intake.arrival_mode or "").lower().replace("-", "_").replace(" ", "_")
    if arrival_mode:
        features[f"arrivalmode_{arrival_mode}"] = 1
    return features


def _schema_features(feature_schema: dict[str, Any]) -> list[str]:
    features = feature_schema.get("features")
    if not features:
        return []

    if all(isinstance(feature, str) for feature in features):
        return list(features)

    column_names = []
    for feature in features:
        if isinstance(feature, dict):
            name = feature.get("name") or feature.get("column")
            if name:
                column_names.append(str(name))
    return column_names


def _default_for_feature(name: str, feature_schema: dict[str, Any]) -> Any:
    default_values = feature_schema.get("default_values")
    if isinstance(default_values, dict) and name in default_values:
        return default_values[name]

    defaults = feature_schema.get("defaults")
    if isinstance(defaults, dict) and name in defaults:
        return defaults[name]

    if name.startswith("has_") or name.endswith("_length"):
        return 0
    return None


def align_features_to_schema(
    raw_features: dict[str, Any],
    feature_schema: dict[str, Any],
) -> pd.DataFrame:
    columns = _schema_features(feature_schema)
    if not columns:
        return pd.DataFrame([raw_features])

    aligned = {
        column: raw_features.get(column, _default_for_feature(column, feature_schema))
        for column in columns
    }
    frame = pd.DataFrame([aligned], columns=columns)
    return frame.apply(pd.to_numeric, errors="coerce")


def build_model_input(
    intake: PatientIntakeRequest,
    feature_schema: dict[str, Any],
) -> pd.DataFrame:
    raw_features = build_raw_features_from_intake(intake)
    return align_features_to_schema(raw_features, feature_schema)
