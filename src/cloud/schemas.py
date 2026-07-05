from __future__ import annotations

"""
BigQuery schemas for CruiseMode data tables.

# TODO: Use these schemas to create BigQuery tables when GCP integration is active.
"""

# Schema for validation_runs table
VALIDATION_RUNS_SCHEMA = [
    {"name": "run_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "feature_name", "type": "STRING", "mode": "REQUIRED"},
    {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
    {"name": "recommendation", "type": "STRING", "mode": "REQUIRED"},
    {"name": "total_findings", "type": "INTEGER", "mode": "NULLABLE"},
    {"name": "patches_applied", "type": "INTEGER", "mode": "NULLABLE"},
    {"name": "tests_passed", "type": "INTEGER", "mode": "NULLABLE"},
    {"name": "tests_failed", "type": "INTEGER", "mode": "NULLABLE"},
    {"name": "duration_seconds", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "oss_blocking", "type": "BOOLEAN", "mode": "NULLABLE"},
]

# Schema for scan_findings table
SCAN_FINDINGS_SCHEMA = [
    {"name": "finding_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "run_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "source_report", "type": "STRING", "mode": "REQUIRED"},
    {"name": "severity", "type": "STRING", "mode": "REQUIRED"},
    {"name": "category", "type": "STRING", "mode": "NULLABLE"},
    {"name": "file", "type": "STRING", "mode": "NULLABLE"},
    {"name": "line", "type": "INTEGER", "mode": "NULLABLE"},
    {"name": "message", "type": "STRING", "mode": "NULLABLE"},
    {"name": "auto_patched", "type": "BOOLEAN", "mode": "NULLABLE"},
    {"name": "risk_score", "type": "FLOAT", "mode": "NULLABLE"},
]
