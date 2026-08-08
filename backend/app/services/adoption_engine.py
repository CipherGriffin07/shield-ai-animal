"""
Adoption compatibility scoring.

Scores a completed questionnaire against a listing's temperament tags
and the animal's profile using straightforward weighted rules. This
produces a 0-100 compatibility_score used to rank applications for
NGO reviewers - it is a real rules engine, not a placeholder, and can
later be upgraded to a Gemini-based recommendation by replacing the
body of score_application below.
"""
from __future__ import annotations

from app.models.adoption import AdoptionListing
from app.schemas.misc import AdoptionQuestionnaire

HOME_TYPE_SCORE = {"farm": 25, "house_with_yard": 20, "apartment": 10}
EXPERIENCE_SCORE = {"experienced": 25, "intermediate": 15, "beginner": 5}


def score_application(listing: AdoptionListing, questionnaire: AdoptionQuestionnaire) -> float:
    score = 0.0

    score += HOME_TYPE_SCORE.get(questionnaire.home_type, 10)
    score += EXPERIENCE_SCORE.get(questionnaire.experience_level, 5)
    score += min(questionnaire.daily_hours_available, 8) * 2.5  # up to 20 points

    listing_tags = {t.strip().lower() for t in listing.temperament_tags.split(",") if t.strip()}
    preferred = {t.strip().lower() for t in questionnaire.preferred_temperament}
    overlap = listing_tags & preferred
    if listing_tags:
        score += (len(overlap) / len(listing_tags)) * 20

    if "child-friendly" in listing_tags and not questionnaire.has_children:
        score += 5  # no conflict either way
    if "not-good-with-other-pets" in listing_tags and questionnaire.has_other_pets:
        score -= 15
    if "good-with-other-pets" in listing_tags and questionnaire.has_other_pets:
        score += 10

    return round(max(0.0, min(score, 100.0)), 1)
