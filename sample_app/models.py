"""
Pydantic models for the Refund API sample application.
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RefundRequest(BaseModel):
    """Request model for processing a refund."""
    payment_id: str = Field(..., description="Unique payment identifier")
    payment_status: PaymentStatus = Field(..., description="Current payment status")
    amount: float = Field(..., description="Refund amount in USD")
    customer_email: str = Field(..., description="Customer's email address")
    card_number: str = Field(..., description="Customer's card number")


class RefundResponse(BaseModel):
    """Response model for a processed refund."""
    refund_id: str = Field(..., description="Generated refund identifier")
    payment_id: str = Field(..., description="Original payment identifier")
    status: str = Field(..., description="Refund status")
    amount: float = Field(..., description="Refunded amount")
    message: str = Field(..., description="Status message")
