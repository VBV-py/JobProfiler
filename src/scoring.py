"""
Composite Scoring Engine.

Combines all feature scores into a single composite score per candidate.
Pipeline:
  1. Honeypot check → if honeypot, score = 0
  2. Coarse filter on title → skip obvious non-fits
  3. Full feature extraction
  4. Weighted composite with behavioral modifier
"""
from src.feature_engineering import (
    compute_title_relevance,
    compute_skill_match,
    compute_career_trajectory,
    compute_experience_fit,
    compute_location_fit,
    compute_education_score,
)
from src.behavioral_signals import compute_behavioral_modifier
from src.honeypot_detector import detect_honeypot
from src.config import WEIGHTS, COARSE_TITLE_THRESHOLD


def score_candidate(candidate: dict) -> dict:
    
    cid = candidate.get("candidate_id", "UNKNOWN")

    # ---- STEP 1: Honeypot check ----
    is_honeypot, honeypot_reasons = detect_honeypot(candidate)
    if is_honeypot:
        return {
            "candidate_id": cid,
            "composite_score": 0.0,
            "is_honeypot": True,
            "honeypot_reasons": honeypot_reasons,
            "components": {},
            "skipped": False,
        }

    # ---- STEP 2: Quick title check (coarse filter) ----
    title_score = compute_title_relevance(candidate)
    if title_score <= COARSE_TITLE_THRESHOLD:
        # Extremely low title relevance → skip detailed scoring
        return {
            "candidate_id": cid,
            "composite_score": title_score * 0.1,  # Tiny score
            "is_honeypot": False,
            "honeypot_reasons": [],
            "components": {"title_relevance": title_score},
            "skipped": True,
        }

    # ---- STEP 3: Full feature extraction ----
    components = {
        "title_relevance": title_score,
        "skill_match": compute_skill_match(candidate),
        "career_trajectory": compute_career_trajectory(candidate),
        "experience_fit": compute_experience_fit(candidate),
        "location_fit": compute_location_fit(candidate),
        "education": compute_education_score(candidate),
        "behavioral": compute_behavioral_modifier(candidate),
    }

    # ---- STEP 4: Weighted composite ----
    base_score = sum(
        components[key] * WEIGHTS[key]
        for key in WEIGHTS
        if key in components
    )

    # Apply behavioral as a multiplicative modifier
    # Range: score × 0.7 (low engagement) to score × 1.3 (high engagement)
    behavioral = components["behavioral"]
    composite = base_score * (0.70 + 0.60 * behavioral)

    return {
        "candidate_id": cid,
        "composite_score": round(composite, 8),
        "is_honeypot": False,
        "honeypot_reasons": [],
        "components": components,
        "skipped": False,
    }
