"""SQLAlchemy ORM models for TriageAI persistence."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.backend.db.base import Base
from app.backend.utils.ids import new_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="clinician", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False)
    chief_complaint: Mapped[str] = mapped_column(Text, nullable=False)
    symptom_duration: Mapped[str | None] = mapped_column(String, nullable=True)
    pain_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    respiratory_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    systolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diastolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    oxygen_saturation: Mapped[float | None] = mapped_column(Float, nullable=True)
    consciousness_level: Mapped[str | None] = mapped_column(String, nullable=True)
    pregnancy: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    arrival_mode: Mapped[str | None] = mapped_column(String, nullable=True)
    additional_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending_review", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    patient: Mapped[Patient] = relationship(back_populates="assessments")
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
    )
    clinician_reviews: Mapped[list["ClinicianReview"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), nullable=False)
    acuity_scale: Mapped[str] = mapped_column(String, default="ESI", nullable=False)
    model_version: Mapped[str | None] = mapped_column(String, nullable=True)
    model_loaded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    predicted_esi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_esi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    probabilities_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_rules_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_source: Mapped[str] = mapped_column(String, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    clinician_summary: Mapped[str] = mapped_column(Text, nullable=False)
    is_placeholder: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    assessment: Mapped[Assessment] = relationship(back_populates="predictions")


class ClinicianReview(Base):
    __tablename__ = "clinician_reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), nullable=False)
    clinician_id: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    final_esi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    assessment: Mapped[Assessment] = relationship(back_populates="clinician_reviews")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assessment_id: Mapped[str | None] = mapped_column(String, nullable=True)
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), nullable=False)
    report_status: Mapped[str] = mapped_column(String, nullable=False)
    download_url: Mapped[str | None] = mapped_column(String, nullable=True)
    include_audit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    assessment: Mapped[Assessment] = relationship(back_populates="reports")
