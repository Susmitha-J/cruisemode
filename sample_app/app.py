"""
Sample FastAPI Refund API — demo target application for CruiseMode.

NOTE: This file intentionally contains unsafe PII logging for CruiseMode to detect:
- Logs the full request object (exposes email, card_number)
- Returns card_number in error details (should be masked)
"""

import logging
from fastapi import FastAPI, HTTPException
from sample_app.models import RefundRequest, RefundResponse
from sample_app.refund_service import process_refund

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Refund API",
    description="Sample Refund API for CruiseMode demo",
    version="0.1.0",
)


@app.post("/refund", response_model=RefundResponse)
async def create_refund(request: RefundRequest):
    """
    Process a refund request.

    Accepts payment details and processes the refund if business rules are met.
    """
    # ⚠️ CruiseMode target: UNSAFE PII LOGGING — logs full request including email & card_number
    logger.info("Received refund request: %s", request.model_dump())

    result = process_refund(request)

    if result["code"] == 400:
        raise HTTPException(status_code=400, detail=result["message"])
    elif result["code"] == 409:
        raise HTTPException(status_code=409, detail=result["message"])
    elif result["code"] == 500:
        raise HTTPException(status_code=500, detail=result["message"])

    return RefundResponse(
        refund_id=result["refund_id"],
        payment_id=result["payment_id"],
        status=result["status"],
        amount=result["amount"],
        message=result["message"],
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
