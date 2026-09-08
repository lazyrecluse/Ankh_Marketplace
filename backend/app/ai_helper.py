import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from . import models

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"


class AIDisabledError(RuntimeError):
    """Raised when the AI assistant is disabled or missing credentials."""
    pass


class AIRateLimitError(RuntimeError):
    """Raised when Gemini API rate limits / quotas are exceeded."""
    pass


def get_gemini_api_key() -> Optional[str]:
    raw = os.getenv("GEMINI_API_KEY")
    return raw.strip() if raw and raw.strip() else None


def get_gemini_model() -> str:
    raw = os.getenv("GEMINI_MODEL")
    return raw.strip() if raw and raw.strip() else DEFAULT_MODEL


def ai_enabled() -> bool:
    """Whether POST /api/ai/chat should serve requests."""
    enabled_flag = os.getenv("ANKH_AI_ENABLED", "true").strip().lower() in ("1", "true", "yes", "on")
    has_key = bool(get_gemini_api_key())
    return enabled_flag and has_key


def retrieve_pertinent_context(
    db: Session,
    message: str,
    user: Optional[models.User] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Retrieve pertinent products and buyer preferences from database tables."""
    # 1. Retrieve Buyer Profile if user is logged in
    buyer_context: Dict[str, Any] = {}
    if user and user.buyer_profile:
        bp = user.buyer_profile
        buyer_context = {
            "preferred_climate": bp.preferred_climate,
            "has_sensitive_skin": bp.has_sensitive_skin,
            "skin_preferences": bp.skin_preferences or [],
            "budget_range": bp.budget_range,
            "typical_order_qty": bp.typical_order_qty,
        }

    # 2. Query Products from database
    products = db.query(models.Product).all()

    # Score products based on query relevance for ranking
    msg_lower = message.lower()
    scored_products = []
    for p in products:
        score = 0
        cat_name = p.category.name.lower() if p.category else ""
        if cat_name and cat_name in msg_lower:
            score += 4
        if p.name.lower() in msg_lower or p.brand.lower() in msg_lower:
            score += 3
        if p.description and any(w in p.description.lower() for w in msg_lower.split() if len(w) > 3):
            score += 1

        # Match climate
        p_climates = [c.lower() for c in (p.recommended_climate or [])]
        for c in ["tropical", "temperate", "polar", "all", "hot", "cold", "summer", "winter"]:
            if c in msg_lower:
                if c in p_climates or "all" in p_climates:
                    score += 3

        # Match sensitive skin / hypoallergenic
        if any(k in msg_lower for k in ["hypoallergenic", "sensitive", "skin", "rash", "allergy", "eczema"]):
            if p.is_hypoallergenic:
                score += 4

        # Match breathability
        if any(k in msg_lower for k in ["breathable", "airy", "ventilation", "sweat"]):
            if p.breathability_rating and p.breathability_rating >= 4:
                score += 3

        # Match user profile if present
        if buyer_context.get("has_sensitive_skin") and p.is_hypoallergenic:
            score += 2
        user_climate = (buyer_context.get("preferred_climate") or "").lower()
        if user_climate and user_climate != "all" and (user_climate in p_climates or "all" in p_climates):
            score += 2

        item = {
            "id": p.id,
            "brand": p.brand,
            "name": p.name,
            "category": p.category.name if p.category else "Uncategorized",
            "in_stock": p.in_stock,
            "price_amount": p.price_amount,
            "currency_symbol": p.currency_symbol,
            "gsm": p.gsm,
            "breathability_rating": p.breathability_rating,
            "is_hypoallergenic": p.is_hypoallergenic,
            "texture_smoothness": p.texture_smoothness,
            "oeko_tex_certified": p.oeko_tex_certified,
            "recommended_climate": p.recommended_climate or [],
            "description": p.description,
            "_score": score,
        }
        scored_products.append(item)

    # Sort so most pertinent records are first in context
    scored_products.sort(key=lambda x: x["_score"], reverse=True)

    # Clean out internal score before serialization
    for p in scored_products:
        del p["_score"]

    return scored_products, buyer_context

def _extract_json_metadata(text: str) -> Tuple[str, List[str], Optional[Dict[str, Any]]]:
    """Extract metadata JSON block from Gemini output and clean prose response."""
    recommended_products: List[str] = []
    suggested_filters: Optional[Dict[str, Any]] = None

    # Look for ```json ... ``` block
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if isinstance(data.get("recommended_products"), list):
                recommended_products = [str(pid) for pid in data["recommended_products"]]
            if isinstance(data.get("suggested_filters"), dict):
                suggested_filters = data["suggested_filters"]
            # Remove the json block from prose
            text = text[:json_match.start()].strip() + "\n" + text[json_match.end():].strip()
            text = text.strip()
        except Exception:
            pass

    return text, recommended_products, suggested_filters


def generate_ai_response(
    db: Session,
    message: str,
    chat_history: list,
    user: Optional[models.User] = None,
) -> dict:
    """Generate textile recommendations using Gemini and RAG database context."""
    api_key = get_gemini_api_key()
    if not ai_enabled() or not api_key:
        raise AIDisabledError(
            "The AI assistant is disabled or GEMINI_API_KEY is not configured. "
            "Please add GEMINI_API_KEY to your environment variables."
        )

    # Retrieve pertinent database rows
    products_context, buyer_context = retrieve_pertinent_context(db, message, user=user)
    valid_product_ids = {p["id"] for p in products_context}

    # Construct prompt with database ground truth
    system_instruction = (
        "You are the Ankh B2B Textile Shopping Assistant, an expert fabric consultant for the Ankh Marketplace.\n"
        "Your role is to advise fashion designers, buyers, and manufacturers on the best textile fabrics for their needs.\n\n"
        "### Ground-Truth Database Context\n"
        "You must ONLY recommend fabrics that exist in the provided catalog context below. DO NOT invent fabric IDs or brands.\n"
        f"Available Products in Database:\n{json.dumps(products_context, indent=2)}\n\n"
    )
    if buyer_context:
        system_instruction += (
            f"Authenticated Buyer Saved Preferences:\n{json.dumps(buyer_context, indent=2)}\n\n"
        )
    system_instruction += (
        "### Instructions\n"
        "1. Answer conversationally, clearly explaining why each fabric suits the user's needs by citing technical specs (GSM, breathability rating, hypoallergenic status, certifications, climate).\n"
        "2. When recommending products, explicitly mention their exact 'id' (e.g. 'linen-1').\n"
        "3. At the very end of your response, ALWAYS include a clean JSON block in exactly this format:\n"
        "```json\n"
        "{\n"
        '  "recommended_products": ["exact_product_id_1", "exact_product_id_2"],\n'
        '  "suggested_filters": {\n'
        '    "category": "linen",\n'
        '    "climate": "Tropical",\n'
        '    "sensitive_skin": true,\n'
        '    "search": "linen"\n'
        "  }\n"
        "}\n"
        "```\n"
        "Only include filters in 'suggested_filters' that directly match the recommendation (omit fields if not applicable)."
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model_name = get_gemini_model()

        # Build contents from history + current message
        contents = []
        for chat in chat_history:
            role = "user" if chat.get("role") == "user" else "model"
            content_text = chat.get("content", "")
            if content_text:
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=content_text)]
                    )
                )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)]
            )
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.6,
            max_output_tokens=768,
        )

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )

        raw_text = response.text or ""
        clean_response, recommended_ids, suggested_filters = _extract_json_metadata(raw_text)

        # Also search response for any mentioned valid product IDs
        for pid in valid_product_ids:
            if pid in raw_text and pid not in recommended_ids:
                recommended_ids.append(pid)

        # Filter to only valid database IDs to prevent hallucinations
        verified_ids = [pid for pid in recommended_ids if pid in valid_product_ids]

        return {
            "response": clean_response,
            "recommended_products": verified_ids,
            "suggested_filters": suggested_filters,
        }

    except AIDisabledError:
        raise
    except AIRateLimitError:
        raise
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Gemini API error during AI chat generation: {err_msg}", exc_info=True)
        # Check for rate limit / quota exhaustion
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "Quota exceeded" in err_msg:
            raise AIRateLimitError(
                "Gemini AI rate limit or quota exceeded. Please wait a moment and try again."
            )
        if "API_KEY_INVALID" in err_msg or "invalid api key" in err_msg.lower():
            raise AIDisabledError(
                "The configured GEMINI_API_KEY is invalid. Please check your API key."
            )
        raise RuntimeError(f"Gemini generation error: {err_msg}")
