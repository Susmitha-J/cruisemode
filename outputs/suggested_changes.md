# Suggested Changes

**Total Patches Applied:** 3

## PATCH-001: pii_logging

**File:** `.sandbox/app.py`

Masked PII fields in log statement — now logs only payment_id and amount

**Related findings:** OWASP-001

---

## PATCH-002: clean_code

**File:** `.sandbox/refund_service.py`

Narrowed broad 'except Exception' to specific types (ValueError, TypeError)

**Related findings:** CC-001

---

## PATCH-003: sonarqube_smell

**File:** `.sandbox/refund_service.py`

Added refactoring note for cognitive complexity (SQ-001, CC-003)

**Related findings:** SQ-001, CC-003

---

