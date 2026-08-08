from __future__ import annotations

from fastapi import APIRouter

from app.schemas.misc import ChatRequest, ChatResponse
from app.services.gemini_service import GeminiNotConfigured, GeminiRequestError, chat_with_gemini

router = APIRouter(prefix="/api/chat", tags=["Chatbot"])


def _rule_based_reply(message: str) -> str:
    text = message.lower()
    if any(w in text for w in ["not breathing", "unconscious", "heavy bleeding", "hit by car"]):
        urgency = "This sounds critical. Contact the nearest veterinarian or emergency rescue service immediately."
    elif "snake" in text:
        urgency = "Keep everyone away. Do not attempt to catch or touch the snake. Contact wildlife rescue or the Forest Department."
    elif "bird" in text:
        urgency = "Place the bird in a ventilated cardboard box only if it can be done safely. Keep it quiet and avoid feeding."
    elif "bleeding" in text:
        urgency = "Keep the animal calm. Use a clean cloth near the wound without pressing excessively, and arrange veterinary care."
    elif "lost" in text or "missing" in text:
        urgency = "Post a Lost & Found report with a clear photo and last-seen location so nearby users and NGOs can help spot a match."
    elif "adopt" in text:
        urgency = "Check the Adoption page for animals ready for a home, and fill in the compatibility questionnaire for a better match."
    else:
        urgency = "Observe from a safe distance, avoid force-feeding or giving medicine, and arrange trained rescue support."

    return (
        f"{urgency}\n\nImportant: this guidance is preliminary. Do not endanger yourself and seek professional "
        "veterinary help.\n\nYou can submit a rescue report from the Report an Animal page."
    )


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    try:
        reply = await chat_with_gemini(payload.message, [h.model_dump() for h in payload.history])
        return ChatResponse(reply=reply, source="gemini")
    except (GeminiNotConfigured, GeminiRequestError):
        return ChatResponse(reply=_rule_based_reply(payload.message), source="rule_based_fallback")
