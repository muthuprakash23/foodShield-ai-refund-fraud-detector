from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from langchain_core.messages import BaseMessage

RiskLevel = Literal["low", "medium", "high", "unknown"]
SupportLevel = Literal["yes", "no", "partial", "unclear", "unknown"]
DecisionType = Literal["APPROVE", "REJECT", "ESCALATE", "ASK_MORE_EVIDENCE"]
IssueType = Literal["contamination", "wrong_order", "missing_item", "quality", "other", "unknown"]


class FraudState(BaseModel):

    messages: List[dict] = Field(default_factory=list, description="Conversation history for intake agent")
    next_step: Optional[str] = Field(default=None, description="Routing signal: vision_agent or continue_intake")

    user_id: Optional[str] = Field(default=None, description="Unique user identifier from Streamlit input")
    order_id: Optional[str] = Field(default=None, description="Order ID from Streamlit input")
    total_orders: Optional[int] = Field(default=None, description="Total orders placed by user ever")
    refund_count_30days: Optional[int] = Field(default=None, description="Refunds requested in last 30 days")
    refund_ratio_30days: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Refund ratio over last 30 days")

    complaint_text: Optional[str] = Field(default=None, description="Latest user message in conversation")
    claimed_issue: Optional[str] = Field(default=None, description="Full issue description e.g. hair in food")
    issue_type: Optional[IssueType] = Field(default=None, description="Category of issue")
    foreign_object: Optional[str] = Field(default=None, description="Foreign object found e.g. hair, insect, stone")
    food_claimed: Optional[str] = Field(default=None, description="Specific food item customer is complaining about")

    image_path: Optional[str] = Field(default=None, description="Path to uploaded complaint image")

    food_detected: Optional[str] = Field(default=None, description="Food item VLM sees in the image")
    seen_from_image: Optional[str] = Field(default=None, description="Full visual description from VLM")
    manipulation_risk: Optional[RiskLevel] = Field(default=None, description="Risk that image is edited or AI manipulated")
    vision_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="VLM confidence in its own analysis")

    claim_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence that claimed issue matches image")
    fraud_risk_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Overall fraud risk score 0.0 to 1.0")
    decision_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Decision agent confidence in final verdict")

    retry_count: int = Field(default=0, ge=0, le=5, description="VLM retry attempts for unclear images")

    final_decision: Optional[DecisionType] = Field(default=None, description="APPROVE / REJECT / ESCALATE / ASK_MORE_EVIDENCE")
    reason_for_decision: Optional[str] = Field(default=None, description="Explanation of final decision")

    class Config:
        arbitrary_types_allowed = True