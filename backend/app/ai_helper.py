import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from . import models

logger = logging.getLogger(__name__)

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"


class AIDisabledError(RuntimeError):
    """Raised when the AI assistant is disabled."""
    pass


class AIRateLimitError(RuntimeError):
    """Raised when API rate limits / quotas are exceeded."""
    pass


def get_groq_api_key() -> Optional[str]:
    raw = os.getenv("GROQ_API_KEY")
    return raw.strip() if raw and raw.strip() else None


def get_groq_model() -> str:
    raw = os.getenv("GROQ_MODEL")
    return raw.strip() if raw and raw.strip() else DEFAULT_GROQ_MODEL


def get_gemini_api_key() -> Optional[str]:
    raw = os.getenv("GEMINI_API_KEY")
    return raw.strip() if raw and raw.strip() else None


def get_gemini_model() -> str:
    raw = os.getenv("GEMINI_MODEL")
    return raw.strip() if raw and raw.strip() else DEFAULT_GEMINI_MODEL


def ai_enabled() -> bool:
    """Whether POST /api/ai/chat should serve requests."""
    return os.getenv("ANKH_AI_ENABLED", "true").strip().lower() in ("1", "true", "yes", "on")


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


def call_groq_api(
    api_key: str,
    model: str,
    system_instruction: str,
    message: str,
    chat_history: list,
) -> str:
    """Call Groq chat completions API (Option B)."""
    import httpx

    messages = [{"role": "system", "content": system_instruction}]
    for chat in chat_history:
        role = "user" if chat.get("role") == "user" else "assistant"
        content_text = chat.get("content", "")
        if content_text:
            messages.append({"role": role, "content": content_text})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 768,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        if resp.status_code == 429:
            raise AIRateLimitError("Groq AI rate limit exceeded. Please wait a moment and try again.")
        if resp.status_code in (401, 403):
            raise AIDisabledError("The configured GROQ_API_KEY is invalid.")
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def call_gemini_api(
    api_key: str,
    model: str,
    system_instruction: str,
    message: str,
    chat_history: list,
) -> str:
    """Call Google Gemini API as secondary provider."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
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
        model=model,
        contents=contents,
        config=config,
    )
    return response.text or ""


def generate_heuristic_response(
    db: Session,
    message: str,
    user: Optional[models.User] = None,
) -> dict:
    """Intelligent zero-downtime offline textile consultant."""
    products_context, buyer_context = retrieve_pertinent_context(db, message, user=user)
    msg_lower = message.lower().strip()

    greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "help", "who are you"]
    is_greeting = any(msg_lower == g or msg_lower.startswith(g + " ") or msg_lower.startswith(g + "!") for g in greetings)

    if is_greeting and not any(w in msg_lower for w in ["fabric", "cotton", "silk", "linen", "wool", "denim", "skin", "climate", "gsm"]):
        response_text = (
            "Hello! Welcome to the Ankh Marketplace Textile Assistant.\n\n"
            "I can help you explore premium textile fabrics based on technical specifications such as GSM weight, "
            "breathability rating, hypoallergenic qualities, climate suitability, and OEKO-TEX certifications.\n\n"
            "How can I assist your sourcing today? For example, you can ask:\n"
            "- *'What breathable fabrics do you recommend for hot, humid weather?'*\n"
            "- *'I have sensitive skin and need hypoallergenic materials.'*\n"
            "- *'Show me high-GSM heavyweight fabrics for winter outerwear.'*"
        )
        return {
            "response": response_text,
            "recommended_products": [],
            "suggested_filters": None,
        }

    top_products = products_context[:3] if products_context else []
    recommended_ids = [p["id"] for p in top_products]

    suggested_filters: Dict[str, Any] = {}
    for cat in ["linen", "cotton", "silk", "wool", "denim", "corduroy", "fleece", "leather", "satin", "velvet"]:
        if cat in msg_lower:
            suggested_filters["category"] = cat
            suggested_filters["search"] = cat
            break

    for clim in ["Tropical", "Temperate", "Polar", "All-weather"]:
        if clim.lower() in msg_lower or (clim.lower() == "tropical" and ("hot" in msg_lower or "summer" in msg_lower)):
            suggested_filters["climate"] = clim
            break

    if any(k in msg_lower for k in ["hypoallergenic", "sensitive", "skin", "eczema", "allergy"]):
        suggested_filters["sensitive_skin"] = True

    if not top_products:
        return {
            "response": "I couldn't find any fabrics directly matching those specific criteria in our current catalog. Try adjusting your climate, GSM, or material preferences!",
            "recommended_products": [],
            "suggested_filters": suggested_filters or None,
        }

    lines = ["Based on your specifications, here are our top fabric recommendations:\n"]
    for p in top_products:
        specs = []
        if p.get("gsm"):
            specs.append(f"{p['gsm']} GSM")
        if p.get("breathability_rating"):
            specs.append(f"Breathability {p['breathability_rating']}/5")
        if p.get("is_hypoallergenic"):
            specs.append("Hypoallergenic")
        if p.get("oeko_tex_certified"):
            specs.append("OEKO-TEX Certified")
        climates = ", ".join(p.get("recommended_climate") or [])
        if climates:
            specs.append(f"Ideal for {climates} climates")

        spec_str = " | ".join(specs)
        lines.append(f"• **{p['brand']} {p['name']}** (ID: `{p['id']}`) — {p['currency_symbol']}{p['price_amount']}\n  *{spec_str}*")
        if p.get("description"):
            desc_snip = p["description"][:140] + "..." if len(p["description"]) > 140 else p["description"]
            lines.append(f"  {desc_snip}\n")

    lines.append("Feel free to ask for more details or click below to view these fabrics in the catalog!")
    prose = "\n".join(lines)

    return {
        "response": prose,
        "recommended_products": recommended_ids,
        "suggested_filters": suggested_filters or None,
    }


def generate_ai_response(
    db: Session,
    message: str,
    chat_history: list,
    user: Optional[models.User] = None,
) -> dict:
    """Generate textile recommendations using Groq (Option B) / Gemini with smart fallback."""
    if not ai_enabled():
        raise AIDisabledError("The AI assistant is currently disabled.")

    groq_key = get_groq_api_key()
    gemini_key = get_gemini_api_key()

    # If neither Groq nor Gemini API key is configured, use the smart local heuristic engine.
    # This guarantees 100% uptime for local debugging with zero external configuration needed.
    if not groq_key and not gemini_key:
        logger.info("No external LLM API key configured; serving response via smart heuristic advisor.")
        return generate_heuristic_response(db, message, user=user)

    products_context, buyer_context = retrieve_pertinent_context(db, message, user=user)
    valid_product_ids = {p["id"] for p in products_context}

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

    raw_text = None

    # 1. Try Groq (Option B - Primary)
    if groq_key:
        try:
            raw_text = call_groq_api(
                api_key=groq_key,
                model=get_groq_model(),
                system_instruction=system_instruction,
                message=message,
                chat_history=chat_history,
            )
        except (AIDisabledError, AIRateLimitError):
            raise
        except Exception as e:
            logger.warning(f"Groq API call failed: {e}. Falling back to heuristic advisor.", exc_info=True)

    # 2. Try Gemini (Secondary) if Groq wasn't configured or failed
    if not raw_text and gemini_key:
        try:
            raw_text = call_gemini_api(
                api_key=gemini_key,
                model=get_gemini_model(),
                system_instruction=system_instruction,
                message=message,
                chat_history=chat_history,
            )
        except (AIDisabledError, AIRateLimitError):
            raise
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}. Falling back to heuristic advisor.", exc_info=True)

    # 3. If external LLM succeeded, parse JSON and verify products
    if raw_text:
        clean_response, recommended_ids, suggested_filters = _extract_json_metadata(raw_text)
        for pid in valid_product_ids:
            if pid in raw_text and pid not in recommended_ids:
                recommended_ids.append(pid)
        verified_ids = [pid for pid in recommended_ids if pid in valid_product_ids]
        return {
            "response": clean_response,
            "recommended_products": verified_ids,
            "suggested_filters": suggested_filters,
        }

    # 4. Fallback to smart heuristic advisor if external providers timed out or encountered errors
    return generate_heuristic_response(db, message, user=user)

