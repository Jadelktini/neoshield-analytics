from pydantic import BaseModel, Field
from typing import Optional

class TransactionPayload(BaseModel):
    user_id: int
    card_id: int
    amount: float = Field(..., gt=0, description="Montant de la transaction en EUR")
    currency: str = Field(default="EUR")
    merchant_category: str
    merchant_country: str
    kyc_status: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

class Confirm3DSPayload(BaseModel):
    transaction_id: int
    challenge_success: bool

class TransactionResponse(BaseModel):
    transaction_id: Optional[int] = None
    status: str
    decision: str
    decision_reason: str
    action_required: str
    ai_risk_score: float
    calculated_velocity_kmh: float
    tx_count_10m: int