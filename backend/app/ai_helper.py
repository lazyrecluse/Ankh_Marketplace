import logging
import os
import urllib.request
import json
from sqlalchemy.orm import Session
from . import models

logger = logging.getLogger(__name__)


class AIDisabledError(RuntimeError):
    """Raised when the local LLM assistant is switched off for this deployment.

    Distinct from a generation failure: the caller turns this into a 503 rather
    than a 500, and it must not fall back to the keyword scorer, which would
    make a disabled assistant look like a working one.
    """


def ai_enabled() -> bool:
    """Whether POST /api/ai/chat should serve requests.

    Defaults to OFF. The model is a ~1.1 GB GGUF downloaded on first use and
    loaded in-process, which is far too heavy for a small deployment instance,
    so it has to be opted into explicitly rather than out of.
    """
    return os.getenv("ANKH_AI_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


MODEL_URL = "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_models")
MODEL_PATH = os.path.join(MODEL_DIR, "qwen2.5-1.5b-instruct-q4_k_m.gguf")

# Global model instance
_llama_model = None

def download_model_if_needed():
    if os.path.exists(MODEL_PATH):
        return
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"Downloading Qwen2.5 model from Hugging Face...")
    # Use urllib to download
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Model download completed successfully.")

def get_llama():
    global _llama_model
    if _llama_model is not None:
        return _llama_model
    
    download_model_if_needed()
    from llama_cpp import Llama
    # Optimize threads to avoid pinning all cores (use min of 2 or cpu_count-1)
    num_threads = max(1, min(2, (os.cpu_count() or 2) - 1))
    _llama_model = Llama(
        model_path=MODEL_PATH,
        n_ctx=512,  # Reduced from 4096 to 512 to significantly lower memory/KV cache footprint
        n_threads=num_threads,
        verbose=False
    )
    return _llama_model

def get_products_context(db: Session) -> str:
    products = db.query(models.Product).all()
    context = []
    for p in products:
        # gallery and recommended_climate are native JSON columns now (Phase 1)
        context.append({
            "id": p.id,
            "brand": p.brand,
            "name": p.name,
            "in_stock": p.in_stock,
            "description": p.description,
            "price_amount": p.price_amount,
            "currency_symbol": p.currency_symbol,
            "gsm": p.gsm,
            "breathability_rating": p.breathability_rating,
            "is_hypoallergenic": p.is_hypoallergenic,
            "texture_smoothness": p.texture_smoothness,
            "oeko_tex_certified": p.oeko_tex_certified,
            "recommended_climate": p.recommended_climate or []
        })
    return json.dumps(context, indent=2)

# Configuration toggles
# Set to False to disable fallback logic entirely (e.g., in production/deployment).
# It will also auto-disable if DEPLOYMENT_ENV is 'production' or PRODUCTION is 'true'.
FALLBACK_ENABLED = True

def fallback_ai_response(db: Session, message: str) -> dict:
    products = db.query(models.Product).all()
    message_lower = message.lower()

    recommended_products = []
    response_parts = []

    for p in products:
        match_score = 0
        if p.name.lower() in message_lower or p.brand.lower() in message_lower:
            match_score += 3

        climates = p.recommended_climate or []
        for c in climates:
            if c.lower() in message_lower:
                match_score += 2

        if p.is_hypoallergenic and any(k in message_lower for k in ["hypoallergenic", "sensitive", "rash", "allergy", "skin"]):
            match_score += 2

        if p.breathability_rating and p.breathability_rating >= 4 and any(k in message_lower for k in ["breathable", "heat", "hot", "summer"]):
            match_score += 1

        if match_score > 0:
            recommended_products.append(p)

    if recommended_products:
        response_parts.append("Based on your request, here are the most relevant textile products from our catalog:")
        for p in recommended_products[:3]:
            desc_snippet = p.description[:100] + "..." if len(p.description) > 100 else p.description
            response_parts.append(f"- **{p.brand} {p.name}** (ID: {p.id}): {desc_snippet} (Price: {p.currency_symbol}{p.price_amount})")
        response_parts.append("\nLet me know if you would like more details about these options!")
        rec_ids = [p.id for p in recommended_products[:3]]
    else:
        response_parts.append("I am the Ankh B2B Textile Shopping Assistant. I couldn't find a direct keyword match in our catalog for your query, but here are some popular products to get started:")
        if products:
            for p in products[:2]:
                response_parts.append(f"- **{p.brand} {p.name}** (ID: {p.id}) - {p.description[:80]}...")
            rec_ids = [p.id for p in products[:2]]
        else:
            rec_ids = []

    return {
        "response": "\n".join(response_parts),
        "recommended_products": rec_ids
    }

def generate_ai_response(db: Session, message: str, chat_history: list) -> dict:
    # Checked before the try below, deliberately: the except clause falls back to
    # the keyword scorer, which would mask a disabled assistant as a working one.
    if not ai_enabled():
        raise AIDisabledError(
            "The AI assistant is disabled in this deployment. Set ANKH_AI_ENABLED=true "
            "and install backend/requirements-ai.txt to turn it on."
        )

    is_prod = os.getenv("DEPLOYMENT_ENV") == "production" or os.getenv("PRODUCTION") == "true" or os.getenv("ENV") == "production"

    try:
        llm = get_llama()
        catalog_context = get_products_context(db)
        
        system_prompt = (
            "You are the Ankh B2B Textile Shopping Assistant. Use the provided product catalog to suggest relevant fabrics to the user.\n"
            "Use your general knowledge about textiles, climates, and skin sensitivities to resolve their requests.\n"
            "Explain your recommendations in simple layman terms. If a fabric has properties like hypoallergenic or high breathability, relate that to their needs (e.g. skin rashes, heat).\n\n"
            "Product Catalog Context:\n"
            f"{catalog_context}\n\n"
            "Respond conversationally. If you recommend specific products, make sure to include their exact 'id' value as references in your response."
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        for chat in chat_history:
            messages.append({"role": chat.get("role", "user"), "content": chat.get("content", "")})
        
        messages.append({"role": "user", "content": message})
        
        # Format the prompt using chat template
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=256,  # Reduced max tokens to speed up generation and save resources
            temperature=0.7
        )
        
        content = response["choices"][0]["message"]["content"]
        
        # Extract product IDs from context that were mentioned
        mentioned_ids = []
        products = db.query(models.Product).all()
        for p in products:
            if p.id in content:
                mentioned_ids.append(p.id)
                
        return {
            "response": content,
            "recommended_products": mentioned_ids
        }
    except Exception as e:
        if is_prod:
            logger.error(f"AI chat LLM generation failed in production: {e}", exc_info=True)
            raise
        logger.warning(f"AI chat LLM generation failed, using fallback scorer: {e}")
        return fallback_ai_response(db, message)
