from functools import lru_cache
from transformers import pipeline
from PIL import Image

MODEL_NAME = "dima806/ai_vs_real_image_detection"


@lru_cache(maxsize=1)
def get_detector():
    return pipeline(
        "image-classification",
        model=MODEL_NAME,
        device=-1
    )


def detect_ai_manipulation(image_path: str) -> dict:
    """
    Detects AI-generated image risk using a Hugging Face model.
    Returns manipulation_risk as low / medium / high / unknown.
    This is only a risk signal, not final fraud proof.
    """

    try:
        image = Image.open(image_path).convert("RGB")
        detector = get_detector()
        results = detector(image)

        scores = {r["label"].upper(): float(r["score"]) for r in results}

        fake_score = scores.get("FAKE", 0.0)
        real_score = scores.get("REAL", 0.0)

        if fake_score >= 0.50:
            manipulation_risk = "high"
        elif fake_score >= 0.25:
            manipulation_risk = "medium"
        else:
            manipulation_risk = "low"

        return {
            "success": True,
            "model_name": MODEL_NAME,
            "manipulation_risk": manipulation_risk,
            "fake_score": round(fake_score, 3),
            "real_score": round(real_score, 3),
            "raw_output": results,
            "note": "This is an AI-image risk signal, not final proof of fraud."
        }

    except Exception as e:
        return {
            "success": False,
            "model_name": MODEL_NAME,
            "manipulation_risk": "unknown",
            "fake_score": None,
            "real_score": None,
            "raw_output": None,
            "error": str(e),
        }