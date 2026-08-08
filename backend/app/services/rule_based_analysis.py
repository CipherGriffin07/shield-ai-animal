"""
Deterministic, rule-based emergency assessment engine.

This is the same logic your working MVP used, carried over unchanged
in behaviour. It is deliberately kept as a permanent fallback (not a
placeholder) that runs whenever:

  - GEMINI_API_KEY is not configured, or
  - the Gemini Vision call fails or times out

so the platform always returns a usable triage result instead of an
error. When Gemini is configured, app/services/gemini_service.py
calls Gemini first and only falls back to this module on failure.
"""
from __future__ import annotations

CRITICAL_WORDS = ["unconscious", "not breathing", "heavy bleeding", "run over", "hit by car", "seizure"]
HIGH_WORDS = ["bleeding", "fracture", "unable to stand", "deep wound", "burn", "road accident"]
MODERATE_WORDS = ["limping", "swelling", "weak", "small wound", "dehydrated"]

FIRST_AID_DEFAULT = (
    "Keep a safe distance and reduce noise. Move the animal only when it is in immediate danger. "
    "Do not force-feed food, water or medicine. For bleeding, place a clean cloth near the wound "
    "without excessive pressure. Contact a veterinarian or trained rescuer immediately."
)


def infer_animal(provided: str, description: str, filename: str) -> str:
    if provided:
        return provided.title()
    text = f"{description} {filename}".lower()
    for animal in ["dog", "cat", "bird", "cow", "snake", "goat"]:
        if animal in text:
            return animal.title()
    return "Animal"


def analyse_report(animal: str, description: str) -> dict:
    text = description.lower()

    if any(word in text for word in CRITICAL_WORDS):
        severity, confidence = "Critical", 0.93
        injury = "Possible life-threatening trauma"
        signs = "Critical indicators detected from the written description"
    elif any(word in text for word in HIGH_WORDS):
        severity, confidence = "High", 0.88
        injury = "Possible serious external injury"
        signs = "Bleeding, mobility or trauma-related signs may be present"
    elif any(word in text for word in MODERATE_WORDS):
        severity, confidence = "Moderate", 0.78
        injury = "Possible moderate injury or weakness"
        signs = "Visible discomfort or reduced mobility may be present"
    else:
        severity, confidence = "Low", 0.66
        injury = "No severe injury confirmed from available information"
        signs = "Limited visible/emergency indicators supplied"

    bleeding_detected = "bleed" in text
    fracture_suspected = "fracture" in text or "unable to stand" in text or "broken" in text

    recommendation = (
        "Escalate to the nearest NGO/veterinary team immediately."
        if severity in ("Critical", "High")
        else "Assign a volunteer for assessment and monitor for changes."
    )

    return {
        "animal": animal,
        "injury": injury,
        "visible_signs": signs,
        "severity": severity,
        "confidence": confidence,
        "bleeding_detected": bleeding_detected,
        "fracture_suspected": fracture_suspected,
        "first_aid": FIRST_AID_DEFAULT,
        "recommendation": recommendation,
        "disclaimer": "This is an AI-assisted preliminary estimate, not a confirmed veterinary diagnosis.",
        "source": "rule_based_fallback",
    }


def calculate_priority(analysis: dict, description: str) -> int:
    base = {"Low": 25, "Moderate": 50, "High": 75, "Critical": 92}[analysis["severity"]]
    text = description.lower()
    if "road" in text or "traffic" in text:
        base += 5
    if "bleeding" in text:
        base += 4
    if "baby" in text or "puppy" in text or "kitten" in text:
        base += 2
    return min(base, 100)
