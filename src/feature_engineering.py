"""
Feature Engineering Module.

Extracts structured scores (0.0 – 1.0) for each scoring dimension:
  1. Title/Role Relevance
  2. Skill Match (must-have + nice-to-have)
  3. Career Trajectory (product co, production ML, stability)
  4. Experience Fit (5-9 year sweet spot)
  5. Location Fit (Pune/Noida preferred)
  6. Education (tier + field relevance)

Each function returns a float in [0.0, 1.0].
"""
from src.config import (
    MUST_HAVE_SKILLS_EXACT, MUST_HAVE_KEYWORDS,
    NICE_TO_HAVE_SKILLS_EXACT, NICE_TO_HAVE_KEYWORDS,
    AI_ML_TITLES_KEYWORDS, TECH_TITLES_KEYWORDS, NON_TECH_TITLES,
    CONSULTING_FIRMS, PRODUCT_COMPANY_KEYWORDS,
    PRODUCTION_ML_KEYWORDS, RESEARCH_ONLY_KEYWORDS,
    PREFERRED_LOCATIONS, GOOD_LOCATIONS,
    IDEAL_EXP_MIN, IDEAL_EXP_MAX,
    SOFT_EXP_MIN, SOFT_EXP_MAX, HARD_EXP_MIN,
)


def _normalize(text: str) -> str:
    return text.strip().lower()


def _text_contains_any(text: str, keywords: list[str]) -> int:
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def _skill_name_matches(skill_name: str, exact_set: set, keyword_list: list) -> bool:
    name_lower = skill_name.strip().lower()

    if name_lower in exact_set:
        return True

    for kw in keyword_list:
        if kw in name_lower or name_lower in kw:
            return True

    return False


# 1. TITLE RELEVANCE

def compute_title_relevance(candidate: dict) -> float:
    
    title = _normalize(candidate["profile"].get("current_title", ""))

    if not title:
        return 0.1

    # Check AI/ML titles — best match
    for ai_title in AI_ML_TITLES_KEYWORDS:
        if ai_title in title or title in ai_title:
            return 1.0

    # Check for AI/ML keywords in title
    ai_keywords_in_title = ["ai", "ml", "machine learning", "data scien",
                            "nlp", "deep learning", "search", "ranking",
                            "recommendation"]
    if any(kw in title for kw in ai_keywords_in_title):
        return 0.9

    # Check tech titles — moderate match
    for tech_title in TECH_TITLES_KEYWORDS:
        if tech_title in title or title in tech_title:
            return 0.55

    # Check for generic tech keywords
    tech_keywords = ["engineer", "developer", "programmer", "architect",
                     "technical", "tech lead", "cto"]
    if any(kw in title for kw in tech_keywords):
        return 0.45

    # Check non-tech titles — strong negative
    for non_tech in NON_TECH_TITLES:
        if non_tech in title or title in non_tech:
            return 0.05

    # Unknown / ambiguous title
    return 0.15


# 2. SKILL MATCH

def compute_skill_match(candidate: dict) -> float:
    
    skills = candidate.get("skills", [])
    if not skills:
        return 0.0

    must_have_score = 0.0
    nice_to_have_score = 0.0
    must_have_matched = 0
    nice_to_have_matched = 0

    for skill in skills:
        name = skill.get("name", "")
        proficiency = skill.get("proficiency", "beginner")
        endorsements = skill.get("endorsements", 0)
        duration_months = skill.get("duration_months", 0)

        # Proficiency weight
        prof_weight = {
            "beginner": 0.25,
            "intermediate": 0.55,
            "advanced": 0.80,
            "expert": 1.00,
        }.get(proficiency, 0.25)

        # Trust multiplier — catches keyword stuffers
        # JD: "An endorsement-and-duration trust multiplier on skills
        #      catches lazy keyword stuffing."
        if endorsements == 0 and duration_months <= 3:
            trust = 0.3   # Very low trust
        elif endorsements <= 2 and duration_months <= 6:
            trust = 0.5   # Low trust
        elif endorsements >= 10 and duration_months >= 18:
            trust = 1.15  # High trust — peer-validated
        elif endorsements >= 5 and duration_months >= 12:
            trust = 1.0   # Normal trust
        else:
            trust = 0.8   # Moderate trust

        weighted_value = prof_weight * trust

        # Check must-have match
        is_must_have = _skill_name_matches(
            name, MUST_HAVE_SKILLS_EXACT, MUST_HAVE_KEYWORDS
        )
        if is_must_have:
            must_have_score += weighted_value
            must_have_matched += 1
            continue  # Don't double-count

        # Check nice-to-have match
        is_nice = _skill_name_matches(
            name, NICE_TO_HAVE_SKILLS_EXACT, NICE_TO_HAVE_KEYWORDS
        )
        if is_nice:
            nice_to_have_score += weighted_value
            nice_to_have_matched += 1

    # Also check career descriptions for skill-signal keywords
    career_text = " ".join(
        role.get("description", "") for role in candidate.get("career_history", [])
    ).lower()
    summary = candidate.get("profile", {}).get("summary", "").lower()
    combined_text = career_text + " " + summary

    # Bonus for must-have keywords found in career descriptions
    career_must_have_hits = _text_contains_any(combined_text, MUST_HAVE_KEYWORDS)
    career_nice_have_hits = _text_contains_any(combined_text, NICE_TO_HAVE_KEYWORDS)

    # Text-based bonus (capped)
    must_have_score += min(career_must_have_hits * 0.15, 1.0)
    nice_to_have_score += min(career_nice_have_hits * 0.10, 0.8)

    # Also check skill_assessment_scores from redrob_signals
    assessments = candidate.get("redrob_signals", {}).get("skill_assessment_scores", {})
    for assessed_skill, score in assessments.items():
        if score >= 60:  # Decent assessment score
            is_must = _skill_name_matches(
                assessed_skill, MUST_HAVE_SKILLS_EXACT, MUST_HAVE_KEYWORDS
            )
            if is_must:
                must_have_score += 0.3  # Assessed & verified skill

    # Normalize: ~4-5 must-have matches and ~2-3 nice-to-have would be excellent
    must_have_norm = min(must_have_score / 4.0, 1.0)
    nice_norm = min(nice_to_have_score / 2.5, 1.0)

    return 0.70 * must_have_norm + 0.30 * nice_norm


# 3. CAREER TRAJECTORY

def compute_career_trajectory(candidate: dict) -> float:
    """
    Analyze career history for fit signals:
    - Product company experience (vs consulting-only)
    - Production ML work (not just research)
    - Career stability (not job-hopping for titles)
    - Relevant industry experience

    The JD is very specific:
    - "People who have only worked at consulting firms in their entire career" → disqualified
    - "Title-chasers" switching every 1.5 years → not a fit
    - "Pure research without production deployment" → will not move forward

    Returns: float in [0.0, 1.0]
    """
    career = candidate.get("career_history", [])
    if not career:
        return 0.0

    total_roles = len(career)
    has_product_company = False
    all_consulting = True
    has_production_ml = False
    has_research_only = False
    long_tenures = 0        # Roles > 24 months
    short_stints = 0        # Roles < 18 months
    production_role_count = 0
    relevant_industry_roles = 0

    for role in career:
        company = _normalize(role.get("company", ""))
        description = _normalize(role.get("description", ""))
        industry = _normalize(role.get("industry", ""))
        duration = role.get("duration_months", 0)
        title = _normalize(role.get("title", ""))

        # Check consulting vs product
        is_consulting = any(cf in company for cf in CONSULTING_FIRMS)
        is_product = any(pk in company for pk in PRODUCT_COMPANY_KEYWORDS)

        if not is_consulting:
            all_consulting = False
        if is_product:
            has_product_company = True

        # Check for production ML signals in role description
        prod_hits = _text_contains_any(description, PRODUCTION_ML_KEYWORDS)
        if prod_hits >= 2:
            has_production_ml = True
            production_role_count += 1

        # Check for research-only signals
        research_hits = _text_contains_any(description, RESEARCH_ONLY_KEYWORDS)
        if research_hits >= 2 and prod_hits == 0:
            has_research_only = True

        # Tenure analysis
        if duration > 24:
            long_tenures += 1
        if duration < 18 and not role.get("is_current", False):
            short_stints += 1

        # Relevant industry
        tech_industries = [
            "software", "technology", "internet", "ai", "ml",
            "saas", "fintech", "e-commerce", "startup",
        ]
        if any(ind in industry for ind in tech_industries):
            relevant_industry_roles += 1

    # ---- Build score ----
    score = 0.0

    # Product company experience (strong positive)
    if has_product_company:
        score += 0.20
    elif not all_consulting:
        score += 0.10  # Some non-consulting experience

    # Consulting-only is a disqualifier
    if all_consulting and total_roles >= 2:
        score *= 0.15  # Severe penalty — JD is explicit about this

    # Production ML experience (very strong positive)
    if has_production_ml:
        score += 0.25
        if production_role_count >= 2:
            score += 0.10  # Sustained production ML career

    # Research-only without production is a negative
    if has_research_only and not has_production_ml:
        score *= 0.4

    # Career stability
    if total_roles > 0:
        stability_ratio = long_tenures / total_roles
        score += stability_ratio * 0.15

    # Title-chaser penalty
    if short_stints >= 3 and total_roles >= 4:
        score *= 0.6  # Heavy penalty
    elif short_stints >= 2 and total_roles >= 3:
        score *= 0.8

    # Relevant industry bonus
    if relevant_industry_roles > 0:
        industry_ratio = relevant_industry_roles / total_roles
        score += industry_ratio * 0.15

    # Check for AI/ML role titles in career history
    ai_role_count = 0
    for role in career:
        role_title = _normalize(role.get("title", ""))
        ai_kws = ["ai", "ml", "machine learning", "data scien", "nlp",
                   "search", "ranking", "recommendation"]
        if any(kw in role_title for kw in ai_kws):
            ai_role_count += 1

    if ai_role_count > 0:
        score += min(ai_role_count * 0.1, 0.2)

    return min(max(score, 0.0), 1.0)


# 4. EXPERIENCE FIT

def compute_experience_fit(candidate: dict) -> float:
    
    years = candidate["profile"].get("years_of_experience", 0)

    # Sweet spot: 5-9 years
    if IDEAL_EXP_MIN <= years <= IDEAL_EXP_MAX:
        # Within sweet spot — score peaks at 6-8
        if 6 <= years <= 8:
            return 1.0
        return 0.90

    # Close range: 3-5 or 9-12
    if SOFT_EXP_MIN <= years < IDEAL_EXP_MIN:
        # 3-5 years: could work if other signals are strong
        return 0.65 + (years - SOFT_EXP_MIN) * 0.05

    if IDEAL_EXP_MAX < years <= SOFT_EXP_MAX:
        # 9-12 years: still reasonable
        return 0.80 - (years - IDEAL_EXP_MAX) * 0.05

    # Extended range
    if 12 < years <= 15:
        return 0.50  # Getting over-senior

    if years < HARD_EXP_MIN:
        return 0.05  # Too junior

    # > 15 years
    return 0.30


# 5. LOCATION FIT

def compute_location_fit(candidate: dict) -> float:
    
    location = _normalize(candidate["profile"].get("location", ""))
    country = _normalize(candidate["profile"].get("country", ""))
    willing = candidate.get("redrob_signals", {}).get("willing_to_relocate", False)

    # Preferred locations (Pune, Noida, Delhi NCR)
    for loc in PREFERRED_LOCATIONS:
        if loc in location:
            return 1.0

    # Good locations (Hyderabad, Mumbai, Bangalore)
    for loc in GOOD_LOCATIONS:
        if loc in location:
            return 0.85

    # India, other city
    if country == "india" or "india" in location:
        if willing:
            return 0.65
        return 0.45

    # Outside India — "case-by-case, but we don't sponsor work visas"
    if willing:
        return 0.25
    return 0.10


# 6. EDUCATION

def compute_education_score(candidate: dict) -> float:
    """
    Score based on education relevance.
    Education is a minor signal — the JD doesn't emphasize it.

    Returns: float in [0.0, 1.0]
    """
    education = candidate.get("education", [])

    if not education:
        return 0.35  # No education listed — not disqualifying

    best_score = 0.0

    for edu in education:
        tier = edu.get("tier", "unknown")
        field = _normalize(edu.get("field_of_study", ""))
        degree = _normalize(edu.get("degree", ""))

        # Tier scoring
        tier_score = {
            "tier_1": 1.0,
            "tier_2": 0.75,
            "tier_3": 0.45,
            "tier_4": 0.25,
            "unknown": 0.35,
        }.get(tier, 0.25)

        # Field relevance bonus/penalty
        relevant_fields = [
            "computer science", "machine learning",
            "artificial intelligence", "data science",
            "information technology", "software",
            "mathematics", "statistics", "applied math",
            "electronics", "electrical engineering",
        ]
        irrelevant_fields = [
            "chemical engineering", "civil engineering",
            "mechanical engineering", "commerce",
            "arts", "humanities", "management",
            "marketing", "finance", "accounting",
        ]

        field_modifier = 0.0
        if any(f in field for f in relevant_fields):
            field_modifier = 0.15
        elif any(f in field for f in irrelevant_fields):
            field_modifier = -0.05

        # Degree level bonus
        degree_modifier = 0.0
        advanced_degrees = ["m.tech", "mtech", "m.s", "ms", "m.sc",
                           "msc", "phd", "ph.d", "doctorate"]
        if any(d in degree for d in advanced_degrees):
            degree_modifier = 0.08

        edu_score = tier_score + field_modifier + degree_modifier
        best_score = max(best_score, edu_score)

    return min(max(best_score, 0.0), 1.0)
