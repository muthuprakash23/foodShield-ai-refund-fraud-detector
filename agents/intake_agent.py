import os
import re
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from tools.db_tool import get_user_history, get_order_details
from state import FraudState

load_dotenv()


def get_llm():
    return ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
    )


INTAKE_SYSTEM_PROMPT = """
You are a helpful and empathetic food complaint intake agent for a food delivery platform.
Your job is to collect all required complaint details through natural conversation before escalating to the verification team.

You have access to the customer's order context provided below.
Use this context to ask intelligent follow-up questions — never assume which item they are complaining about.

Required fields you must collect:
1. claimed_issue     → full description of the problem
2. issue_type        → one of: contamination, wrong_order, missing_item, quality, other
3. foreign_object    → what they found (hair, insect, stone, etc.) — only if contamination
4. food_claimed      → the specific food item they are complaining about
5. image_path        → confirmation that they have uploaded a photo

Rules:
- Be natural and empathetic, not robotic
- Use the order context to ask specific questions (e.g. "Which item had the issue? Your order had Biryani, Fries, and Coke")
- Never assume which food item the complaint is about — always ask if multiple items exist
- If the customer is vague, ask for clarification
- Once all 4 fields are collected, ask for a photo
- Once photo is confirmed uploaded, respond with EXACTLY this JSON and nothing else:

{{
    "intake_complete": true,
    "claimed_issue": "...",
    "issue_type": "...",
    "foreign_object": "...",
    "food_claimed": "..."
}}
 CRITICAL: Never return the JSON completion signal unless state already contains an uploaded image.
  The system will notify you with "[System: Customer has uploaded the complaint image]" when this happens.
  Until you see that message, keep asking for the photo or questions — do not return JSON.

Order Context:
{order_context}

Refund History Context:
{refund_context}
"""


def dict_to_message(d: dict):
    if d["type"] == "human":
        return HumanMessage(content=d["content"])
    elif d["type"] == "ai":
        return AIMessage(content=d["content"])
    return HumanMessage(content=d["content"])


def message_to_dict(m) -> dict:
    return {"type": m.type, "content": m.content}


def build_system_prompt(order_details: dict, user_history: dict) -> str:
    if order_details.get("found"):
        order_context = f"""
        Order ID: {order_details['order_id']}
        Items: {order_details['food_item']}
        Order Date: {order_details['order_date']}
        Amount: {order_details['amount']}
        """
    else:
        order_context = "Order not found in system."

    if user_history.get("found"):
        refund_context = f"""
        Total Orders: {user_history['total_orders']}
        Refunds in last 30 days: {user_history['refund_count_30days']}
        Refund Ratio: {user_history['refund_ratio_30days']}
        Account Age: {user_history['account_age_days']} days
        """
    else:
        refund_context = "No user history found."

    return INTAKE_SYSTEM_PROMPT.format(
        order_context=order_context,
        refund_context=refund_context,
    )


def intake_node(state: FraudState) -> FraudState:
    order_details = get_order_details(state.order_id) if state.order_id else {}
    user_history = get_user_history(state.user_id) if state.user_id else {}

    system_prompt = build_system_prompt(order_details, user_history)

    updated_messages = [dict_to_message(m) for m in state.messages]

    if state.complaint_text:
        updated_messages.append(HumanMessage(content=state.complaint_text))

    if state.image_path and not any(
        "image uploaded" in m.content.lower()
        for m in updated_messages
        if hasattr(m, "type") and m.type == "human"
    ):
        updated_messages.append(
            HumanMessage(content="[System: Customer has uploaded the complaint image]")
        )

    response = get_llm().invoke(
        [SystemMessage(content=system_prompt)] + updated_messages
    )

    agent_reply = response.content.strip()
    updated_messages.append(AIMessage(content=agent_reply))
    messages_as_dicts = [message_to_dict(m) for m in updated_messages]

    try:
        raw = agent_reply
        if "```" in raw:
            raw = re.sub(r"```(?:json)?", "", raw).strip()

        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())

            if parsed.get("intake_complete"):
                data = state.model_dump()
                data["messages"] = messages_as_dicts
                data["complaint_text"] = None
                data["claimed_issue"] = parsed.get("claimed_issue")
                data["issue_type"] = parsed.get("issue_type")
                data["foreign_object"] = parsed.get("foreign_object")
                data["food_claimed"] = parsed.get("food_claimed")
                data["total_orders"] = user_history.get("total_orders")
                data["refund_count_30days"] = user_history.get("refund_count_30days")
                data["refund_ratio_30days"] = user_history.get("refund_ratio_30days")
                data["next_step"] = "vision_agent"
                return FraudState(**data)

    except (json.JSONDecodeError, AttributeError):
        pass

    data = state.model_dump()
    data["messages"] = messages_as_dicts
    data["complaint_text"] = None
    data["next_step"] = "continue_intake"
    return FraudState(**data)