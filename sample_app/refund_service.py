"""
Refund business logic service.

NOTE: This file intentionally contains issues for CruiseMode to detect and patch:
- Broad exception handling (catch-all Exception)
- Missing validation edge cases
- Code smell: overly complex conditional logic
"""

import logging
import uuid

from sample_app.models import RefundRequest, PaymentStatus

logger = logging.getLogger(__name__)


def process_refund(request: RefundRequest) -> dict:
    """
    Process a refund request.

    Business rules:
    - Amount must be greater than zero
    - Only completed payments may be refunded
    - Pending payments return a conflict status
    """
    try:
        # --- CruiseMode target: broad exception handling wraps everything ---

        # Validate amount
        if request.amount <= 0:
            logger.warning("Invalid refund amount: %s", request.amount)
            return {
                "status": "error",
                "message": "Refund amount must be greater than zero.",
                "code": 400,
            }

        # Check payment status
        if request.payment_status == PaymentStatus.PENDING:
            logger.info("Refund blocked — payment is still pending: %s", request.payment_id)
            return {
                "status": "conflict",
                "message": "Cannot refund a pending payment.",
                "code": 409,
            }

        if request.payment_status != PaymentStatus.COMPLETED:
            logger.info("Refund rejected — payment status: %s", request.payment_status)
            return {
                "status": "error",
                "message": f"Refund not allowed for payment status: {request.payment_status.value}",
                "code": 400,
            }

        # Process the refund
        refund_id = f"RF-{uuid.uuid4().hex[:8].upper()}"
        logger.info("Refund processed: refund_id=%s, payment_id=%s", refund_id, request.payment_id)

        return {
            "status": "success",
            "refund_id": refund_id,
            "payment_id": request.payment_id,
            "amount": request.amount,
            "message": "Refund processed successfully.",
            "code": 200,
        }

    except Exception as e:
        # CruiseMode target: overly broad exception handler
        logger.error("Unexpected error processing refund: %s", str(e))
        return {
            "status": "error",
            "message": "An internal error occurred.",
            "code": 500,
        }
