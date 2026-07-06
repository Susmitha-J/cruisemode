# Acceptance Criteria — Refund API Feature

## AC-001: Refund Amount Validation
- Refund amount must be greater than zero.
- Requests with zero or negative amounts must return HTTP 400.

## AC-002: Completed Payment Requirement
- Refund is allowed only for payments with status `completed`.
- Requests for non-completed payments must return an appropriate error.

## AC-003: Pending Payment Conflict
- Pending payments must return HTTP 409 (Conflict).

## AC-004: PII Logging Safety
- Logs must NOT expose customer email.
- Logs must NOT expose card number.
- Logs must NOT expose account number.
- Logs must NOT expose the full request body.

## AC-005: Test Coverage
- Unit tests must cover refund validation logic.
- API tests must cover all HTTP status code scenarios.
- All unit and API tests must pass before Jenkins feature build.
