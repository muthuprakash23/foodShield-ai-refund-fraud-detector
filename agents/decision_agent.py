import os
import re
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from state import FraudState

load_dotenv()


def get_llm():
    return ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
    )


DECISION_SYSTEM_PROMPT = """
You are a senior fraud analyst for a food delivery platform.
Your job is to make a fair, evidence-based decision on a food complaint refund request.

Weigh ALL signals together — no single signal alone should cause rejection.

Decision Rules:
- APPROVE  → manipulation_risk low AND claim matches image AND user history clean
- REJECT   → manipulation_risk high AND claim does not match image AND high refund ratio
- ESCALATE → any signal is medium or conflicting or vision_confidence low
- ASK_MORE_EVIDENCE → image unclear or manipulation_risk unknown and signals neutral

Important:
- Loyal customer with 1 suspicious image → ESCALATE not REJECT
- New account with high manipulation risk → REJECT
- High refund ratio alone is NOT enough to reject
- Be specific in your reasoning

Return ONLY this JSON and nothing else:
{{
    "final_decision": "APPROVE/REJECT/ESCALATE/ASK_MORE_EVIDENCE",
    "fraud_risk_score": 0.0,
    "claim_confidence": 0.0,
    "decision_confidence": 0.0,
    "reason_for_decision": "detailed explanation"
}}
"""


def build_decision_context(state: FraudState) -> str:
    food_match = "UNKNOWN"
    if state.food_claimed and state.food_detected:
        if state.food_claimed.lower() in state.food_detected.lower():
            food_match = "YES"
        else:
            food_match = "NO"

    high_refund = "YES" if state.refund_ratio_30days and state.refund_ratio_30days > 0.4 else "NO"
    new_account = "YES" if state.total_orders and state.total_orders < 5 else "NO"

    return f"""
    === USER HISTORY ===
    User ID             : {state.user_id}
    Total Orders        : {state.total_orders}
    Refunds (30 days)   : {state.refund_count_30days}
    Refund Ratio        : {state.refund_ratio_30days}
    New Account         : {new_account}

    === COMPLAINT ===
    Claimed Issue       : {state.claimed_issue}
    Issue Type          : {state.issue_type}
    Foreign Object      : {state.foreign_object}
    Food Claimed        : {state.food_claimed}

    === IMAGE ANALYSIS ===
    Food Detected       : {state.food_detected}
    Seen From Image     : {state.seen_from_image}
    Manipulation Risk   : {state.manipulation_risk}
    Vision Confidence   : {state.vision_confidence}

    === DERIVED SIGNALS ===
    Food Match          : {food_match}
    High Refund Ratio   : {high_refund}
    """


def decision_node(state: FraudState) -> FraudState:
    context = build_decision_context(state)

    messages = [
        SystemMessage(content=DECISION_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ]

    try:
        response = get_llm().invoke(messages)
        raw = response.content.strip()
        if "```" in raw:
            raw = re.sub(r"```(?:json)?", "", raw).strip()
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found")
    except Exception:
        parsed = {
            "final_decision": "ESCALATE",
            "fraud_risk_score": 0.5,
            "claim_confidence": 0.5,
            "decision_confidence": 0.0,
            "reason_for_decision": "Decision agent failed. Escalating for manual review.",
        }

    data = state.model_dump()
    data["final_decision"] = parsed.get("final_decision")
    data["fraud_risk_score"] = float(parsed.get("fraud_risk_score", 0.5))
    data["claim_confidence"] = float(parsed.get("claim_confidence", 0.5))
    data["decision_confidence"] = float(parsed.get("decision_confidence", 0.0))
    data["reason_for_decision"] = parsed.get("reason_for_decision")
    data["next_step"] = "end"
    return FraudState(**data)