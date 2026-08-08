"""
Gemini Vision (image triage) and Gemini Chat (assistant) integration.

Requires GEMINI_API_KEY to be set in the environment / .env file.
Get one at https://aistudio.google.com/apikey

Nothing here is mocked: when a key is configured, these functions make
real calls to the Gemini API over HTTPS. When no key is configured,
GeminiNotConfigured is raised immediately so the caller (see
app/routers/reports.py and app/routers/chat.py) can fall back to the
deterministic rule-based engine rather than pretending to have run AI
analysis it didn't actually run.
"""
from __future__ import annotations

import base64
import json

import httpx

from app.config import settings

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiNotConfigured(RuntimeError):
    pass


class GeminiRequestError(RuntimeError):
    pass


VISION_PROMPT = """You are a veterinary triage assistant for an animal rescue platform.
Look at the uploaded photo and the reporter's description, then respond with ONLY a JSON
object (no markdown fences, no extra text) in exactly this shape:

{
  "animal": "Dog | Cat | Bird | Cow | Goat | Snake | Other",
  "injury": "short description of the most likely injury or condition",
  "visible_signs": "short description of visible signs in the image",
  "severity": "Low | Moderate | High | Critical",
  "confidence": 0.0-1.0,
  "bleeding_detected": true|false,
  "fracture_suspected": true|false,
  "first_aid": "concrete, safe first-aid guidance a bystander can follow",
  "recommendation": "what the rescue team should do next"
}

Reporter's description: {description}
"""


async def analyse_image_with_gemini(image_bytes: bytes, mime_type: str, description: str) -> dict:
    if not settings.gemini_api_key:
        raise GeminiNotConfigured("GEMINI_API_KEY is not configured.")

    url = f"{GEMINI_BASE_URL}/{settings.gemini_vision_model}:generateContent"
    prompt = VISION_PROMPT.replace("{description}", description or "No description provided.")
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}},
            ]
        }],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, params={"key": settings.gemini_api_key}, json=payload)

    if response.status_code != 200:
        raise GeminiRequestError(f"Gemini Vision request failed ({response.status_code}): {response.text}")

    data = response.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise GeminiRequestError(f"Could not parse Gemini Vision response: {exc}")

    result["disclaimer"] = "This is an AI-assisted preliminary estimate, not a confirmed veterinary diagnosis."
    result["source"] = "gemini_vision"
    return result


CHAT_SYSTEM_PROMPT = """You are the SHIELD AI assistant, embedded in an animal rescue platform.
Give concise, safe, practical guidance on animal first aid, emergency response, lost-pet advice,
and general animal care. Always tell the user to contact a veterinarian or trained rescuer for
anything serious, and never claim to replace professional veterinary care."""


async def chat_with_gemini(message: str, history: list[dict]) -> str:
    if not settings.gemini_api_key:
        raise GeminiNotConfigured("GEMINI_API_KEY is not configured.")

    url = f"{GEMINI_BASE_URL}/{settings.gemini_chat_model}:generateContent"
    contents = [{"role": "user", "parts": [{"text": CHAT_SYSTEM_PROMPT}]}]
    for turn in history[-10:]:
        role = "model" if turn.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": turn.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    payload = {"contents": contents, "generationConfig": {"temperature": 0.4}}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, params={"key": settings.gemini_api_key}, json=payload)

    if response.status_code != 200:
        raise GeminiRequestError(f"Gemini Chat request failed ({response.status_code}): {response.text}")

    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise GeminiRequestError(f"Could not parse Gemini Chat response: {exc}")
