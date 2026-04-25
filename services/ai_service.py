# services/ai_service.py
from google import genai
import random
import asyncio
import logging
from db.database import get_db
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

FALLBACK_QUOTES = [
    "Sandali lang, medyo busy ang AI ngayon. Subukan mo ulit mamaya!",
    "Nag-aayos muna ang aming AI coach. Try again in a few minutes!",
    "May technical difficulties kami ngayon. Huwag kang mag-alala, babalik din ito!",
]


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class QuotaExceededError(AIServiceError):
    """Raised when API quota is exhausted."""
    pass


class ModelNotFoundError(AIServiceError):
    """Raised when the specified model is not available."""
    pass


def _is_quota_error(e: Exception) -> bool:
    return "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)


def _is_model_error(e: Exception) -> bool:
    return "404" in str(e) or "not found" in str(e).lower() or "invalid model" in str(e).lower()


def _is_auth_error(e: Exception) -> bool:
    return "401" in str(e) or "403" in str(e) or "API_KEY" in str(e).upper()


def _sync_call_gemini(model: str, prompt: str) -> str:
    """Synchronous Gemini call — runs in a thread via asyncio.to_thread."""
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    if not response or not response.text:
        raise AIServiceError("Empty response received from Gemini API.")
    return response.text.strip()


async def _call_gemini_with_retry(prompt: str, model: str, max_retries: int = 3) -> str:
    """
    Calls Gemini API with exponential backoff retry on quota errors.
    Uses asyncio.to_thread so the sync SDK call doesn't block the event loop.
    Raises specific exceptions for different failure modes.
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            logger.info(f"Calling Gemini model '{model}' (attempt {attempt + 1}/{max_retries})")

            # ✅ Offload blocking SDK call to a thread — keeps FastAPI event loop free
            text = await asyncio.to_thread(_sync_call_gemini, model, prompt)
            return text

        except Exception as e:
            last_exception = e
            error_str = str(e)

            if _is_auth_error(e):
                logger.error("Authentication error — check your GEMINI_API_KEY.")
                raise AIServiceError("Invalid or missing API key. Please check your configuration.") from e

            if _is_model_error(e):
                logger.error(f"Model '{model}' not found or unavailable: {error_str}")
                raise ModelNotFoundError(f"Model '{model}' is not available. Try a different model.") from e

            if _is_quota_error(e):
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5  # 5s → 10s → 20s
                    logger.warning(f"Quota exceeded. Retrying in {wait_time}s... (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error("Quota exceeded after all retries.")
                    raise QuotaExceededError("API quota exhausted. Please try again later or upgrade your plan.") from e

            # Unknown/unexpected error — don't retry
            logger.error(f"Unexpected Gemini API error: {error_str}")
            raise AIServiceError(f"Unexpected error from Gemini API: {error_str}") from e

    raise AIServiceError("Max retries reached without a successful response.") from last_exception


async def generate_motivational_quote():
    """
    Randomly picks one log from DB, generates a motivational quote based on it.
    Returns a quote or a graceful fallback message on failure.
    """
    db = get_db()

    try:
        # ✅ Fetch a random log efficiently — no need to load all logs into memory
        count = await db["logs"].count_documents({})

        if count == 0:
            return {"quote": "Walang logs pa. Mag-log muna para makakuha ng motivational quote!"}

        skip = random.randint(0, count - 1)
        random_log = await db["logs"].find_one(skip=skip)

        if not random_log:
            return {"quote": "Walang logs pa. Mag-log muna para makakuha ng motivational quote!"}

        random_log["_id"] = str(random_log["_id"])

    except Exception as e:
        logger.error(f"Database error while fetching logs: {e}")
        return {
            "quote": "Hindi ma-access ang logs mo ngayon. Check your database connection.",
            "error": "database_error",
        }

    prompt = f"""
You are a Taglish wellness coach. Generate a SHORT motivational reminder (2-3 sentences) about general self-care and mental health.
Use the user's data ONLY as context to know what topic to focus on — but DO NOT mention specific numbers or list their data back to them.
Sound like a general reminder, not a personal report.

USER CONTEXT (for topic guidance only):
- Stress level: {random_log.get('stress_level')}/10
- Sleep: {random_log.get('sleep_hours')} hours
- Skipped breakfast: {"yes" if random_log.get('skipped_breakfast') else "no"}
- Food quality: {random_log.get('food_quality')}
- Activity: {random_log.get('activity')}
- Notes: "{random_log.get('notes') or 'none'}"

STRICT RULES:
1. DO NOT mention exact numbers (no stress scores, no sleep hours)
2. DO NOT list their data back — no "nakita ko na..." or "based on your log..."
3. Sound like a general wellness tip, not a personalized analysis
4. Taglish tone — parang close friend na nagpapadama lang
5. Focus on ONE theme (rest, food, mental health, movement) based on what's most concerning in their data
6. End with a soft, caring reminder — walang pressure
"""

    try:
        quote = await _call_gemini_with_retry(prompt, model="gemini-2.5-flash")
        return {"based_on_log": random_log, "quote": quote}

    except QuotaExceededError:
        return {
            "based_on_log": random_log,
            "quote": random.choice(FALLBACK_QUOTES),
            "error": "quota_exceeded",
            "error_message": "API quota exhausted. Try again later or upgrade your Gemini plan.",
        }
    except ModelNotFoundError as e:
        return {
            "based_on_log": random_log,
            "quote": random.choice(FALLBACK_QUOTES),
            "error": "model_not_found",
            "error_message": str(e),
        }
    except AIServiceError as e:
        logger.error(f"AI service error: {e}")
        return {
            "based_on_log": random_log,
            "quote": random.choice(FALLBACK_QUOTES),
            "error": "ai_service_error",
            "error_message": str(e),
        }