import os
import re
import json
import base64
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from tools.hf_detector_tool import detect_ai_manipulation
from state import FraudState

load_dotenv()


def get_vlm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )


VISION_PROMPT = """
You are a food complaint image analyst. Be precise and focused.

Customer complaint:
- Claimed Issue: {claimed_issue}
- Food Item: {food_claimed}
- Foreign Object Reported: {foreign_object}

Your task — answer ONLY these specific questions:

1. FOOD DETECTED: What is the main food item in the image? One short answer.

2. FOREIGN OBJECT VISIBLE: Is there a {foreign_object} visibly present in the image?
   Look specifically for: hair strands, insects, cockroaches, stones, plastic.
   Do NOT describe spices, seeds, herbs, or natural food ingredients as foreign objects.
   Answer: yes / no / unclear

3. FOOD MATCH: Does the food in the image look like {food_claimed}?
   Answer: yes / no / partial / unclear

. MANIPULATION: Carefully examine if this image is AI generated or digitally edited.

   AI generated images typically show:
   - Unnaturally perfect or blurry food textures
   - Lighting that doesn't match the background
   - Foreign objects (hair/insect) that look pasted on, no shadow, no depth
   - Overly smooth or plastic-looking food surfaces
   - Inconsistent blur — food sharp but background unrealistically blurred
   - Perfect symmetry that doesn't occur in real food photos
   - Fingers or hands that look distorted if visible

   Be aggressive — if anything looks slightly off, flag it as medium.
   Only say low if the image looks like a genuine phone camera photo with natural imperfections.
   Answer: low / medium / high / unknown

5. CONFIDENCE: How confident are you in this analysis overall? (0.0 to 1.0)

Return ONLY this JSON:
{{
    "food_detected": "...",
    "seen_from_image": "one sentence describing only what is relevant to the complaint",
    "issue_visible": "yes/no/unclear",
    "food_match": "yes/no/partial/unclear",
    "manipulation_signs": "specific signs only, or none",
    "gemini_manipulation_assessment": "low/medium/high/unknown",
    "vision_confidence": 0.0
}}
"""


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def combine_manipulation_risk(
    gemini_assessment: str,
    hf_risk: str,
    hf_fake_score: float
) -> str:
    risk_rank = {"low": 0, "medium": 1, "high": 2, "unknown": -1}

    gemini_rank = risk_rank.get(gemini_assessment, -1)
    hf_rank = risk_rank.get(hf_risk, -1)

    if gemini_rank == -1 and hf_rank == -1:
        return "unknown"
    if gemini_rank == -1:
        return hf_risk
    if hf_rank == -1:
        return gemini_assessment

    final_rank = max(gemini_rank, hf_rank)
    
    if final_rank == 0 and hf_fake_score >= 0.40:
        final_rank = 1

    rank_to_risk = {0: "low", 1: "medium", 2: "high"}
    return rank_to_risk.get(final_rank, "unknown")


def vision_node(state: FraudState) -> FraudState:
    if not state.image_path or not os.path.exists(state.image_path):
        new_retry = state.retry_count + 1

        if new_retry >= 5:
            data = state.model_dump()
            data["retry_count"] = new_retry
            data["food_detected"] = "unknown"
            data["seen_from_image"] = "Image could not be analyzed after maximum retries"
            data["manipulation_risk"] = "unknown"
            data["vision_confidence"] = 0.0
            data["next_step"] = "decision_agent"
            return FraudState(**data)

        data = state.model_dump()
        data["retry_count"] = new_retry
        data["next_step"] = "continue_intake"
        return FraudState(**data)

    image_data = encode_image(state.image_path)

    prompt = VISION_PROMPT.format(
        claimed_issue=state.claimed_issue or "not specified",
        food_claimed=state.food_claimed or "not specified",
        foreign_object=state.foreign_object or "not specified",
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_data}"
                }
            },
        ]
    )

    response = get_vlm().invoke([message])

    try:
        raw = response.content.strip()
        if "```" in raw:
            raw = re.sub(r"```(?:json)?", "", raw).strip()
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            gemini_output = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found")
    except Exception:
        gemini_output = {
            "food_detected": "unknown",
            "seen_from_image": "Gemini analysis failed",
            "issue_visible": "unclear",
            "food_match": "unclear",
            "manipulation_signs": "unknown",
            "gemini_manipulation_assessment": "unknown",
            "vision_confidence": 0.0,
        }

    hf_result = detect_ai_manipulation(state.image_path)

    final_manipulation_risk = combine_manipulation_risk(
        gemini_assessment=gemini_output.get("gemini_manipulation_assessment", "unknown"),
        hf_risk=hf_result.get("manipulation_risk", "unknown"),
        hf_fake_score=hf_result.get("fake_score", 0.0),
    )

    data = state.model_dump()
    data["food_detected"] = gemini_output.get("food_detected")
    data["seen_from_image"] = gemini_output.get("seen_from_image")
    data["vision_confidence"] = float(gemini_output.get("vision_confidence", 0.0))
    data["manipulation_risk"] = final_manipulation_risk
    data["next_step"] = "decision_agent"
    return FraudState(**data)