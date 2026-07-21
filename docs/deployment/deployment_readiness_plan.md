# TriageAI / SympDirect — Deployment Readiness Plan

## Purpose

TriageAI / SympDirect is a clinical decision-support workflow for structured intake, ESI care routing, safety escalation, clinician review, auditability, and PDF reporting.

It is not a diagnostic system and does not replace clinician judgment.

## Current Local Demo Architecture

```text
React Frontend
    ↓
FastAPI Backend
    ↓
LightGBM V2 Model Registry
    ↓
SQLite Demo Database
    ↓
Audit Trail + PDF Reports

Local URLs:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8001
Health:   http://localhost:8001/health
Ready:    http://localhost:8001/ready
