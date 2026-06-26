"""
Reasoning Generation Module.

Generates specific, honest, per-candidate reasoning strings for the
submission CSV.

Per the submission spec (Stage 4 checks):
  Reference specific facts from the candidate's profile
  Connect to specific JD requirements
  Acknowledge gaps and concerns honestly
  No hallucination — only mention things in the profile
  Substantively different across candidates (no templates)
  Tone matches the rank position
"""


def generate_reasoning(entry: dict) -> str:
    
    candidate = entry["candidate"]
    components = entry.get("components", {})
    rank = entry["rank"]
    score = entry["score"]

    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])

    # Extract key facts
    title = profile.get("current_title", "Unknown")
    company = profile.get("current_company", "Unknown")
    years = profile.get("years_of_experience", 0)
    location = profile.get("location", "Unknown")
    country = profile.get("country", "Unknown")
    industry = profile.get("current_industry", "Unknown")

    notice = signals.get("notice_period_days", 0)
    response_rate = signals.get("recruiter_response_rate", 0)
    github = signals.get("github_activity_score", -1)
    open_to_work = signals.get("open_to_work_flag", False)
    last_active = signals.get("last_active_date", "")

    # Skill names for reference
    skill_names = [s["name"] for s in skills[:8]]  # Cap at 8 for brevity

    # Count relevant skills
    ai_keywords = ["python", "ml", "ai", "nlp", "embedding", "search",
                   "ranking", "vector", "faiss", "elasticsearch", "pytorch",
                   "tensorflow", "transformer", "bert", "llm", "rag",
                   "recommendation", "retrieval", "deep learning",
                   "data science", "machine learning"]
    relevant_skills = [
        s["name"] for s in skills
        if any(kw in s["name"].lower() for kw in ai_keywords)
    ]

    # ---- BUILD REASONING ----
    parts = []

    # Part 1: Who they are (always include)
    loc_str = location if country == "India" else f"{location}, {country}"
    parts.append(f"{title} at {company} ({years:.1f} yrs, {loc_str})")

    # Part 2: Strengths (vary by component scores)
    strengths = []

    title_score = components.get("title_relevance", 0)
    skill_score = components.get("skill_match", 0)
    career_score = components.get("career_trajectory", 0)
    behavioral_score = components.get("behavioral", 0)

    if title_score >= 0.9:
        strengths.append("strong AI/ML title alignment")
    elif title_score >= 0.5:
        strengths.append("relevant technical role")

    if skill_score >= 0.6 and relevant_skills:
        top_rel = relevant_skills[:3]
        strengths.append(f"key skills: {', '.join(top_rel)}")
    elif skill_score >= 0.4:
        strengths.append("partial skill match with JD requirements")

    if career_score >= 0.6:
        # Look for specifics in career
        has_product = any(
            r.get("company_size", "") not in ["10001+"]
            or "product" in r.get("description", "").lower()
            for r in career
        )
        prod_kws = ["production", "deployed", "shipped", "ranking",
                     "recommendation", "retrieval", "search"]
        has_prod_ml = any(
            any(kw in r.get("description", "").lower() for kw in prod_kws)
            for r in career
        )
        if has_prod_ml:
            strengths.append("production ML/system deployment experience")
        elif has_product:
            strengths.append("solid product-company trajectory")
        else:
            strengths.append("strong career trajectory")

    if github > 40:
        strengths.append(f"GitHub activity score {github:.0f}")

    if response_rate >= 0.6:
        strengths.append(f"responsive ({response_rate:.0%} recruiter response rate)")

    # Part 3: Concerns (vary by rank and gaps)
    concerns = []

    if notice > 90:
        concerns.append(f"long notice ({notice}d)")
    elif notice > 60:
        concerns.append(f"notice period {notice}d")

    if response_rate < 0.25:
        concerns.append(f"low recruiter response ({response_rate:.0%})")

    exp_score = components.get("experience_fit", 0)
    if exp_score < 0.6:
        if years < 4:
            concerns.append(f"limited experience ({years:.0f}y vs 5-9y target)")
        elif years > 12:
            concerns.append(f"over-experienced ({years:.0f}y) for 5-9y target")

    loc_score = components.get("location_fit", 0)
    if loc_score < 0.5 and country != "India":
        concerns.append(f"based outside India ({country})")

    if not open_to_work:
        concerns.append("not actively looking (open_to_work=false)")

    if title_score < 0.3:
        concerns.append(f"non-core title ({title})")

    # ---- ASSEMBLE ----
    reasoning = parts[0]

    if strengths:
        # Pick top 2-3 strengths depending on rank
        n_strengths = 3 if rank <= 20 else 2
        reasoning += ". " + "; ".join(strengths[:n_strengths]).capitalize()

    if concerns:
        # Show concerns more for lower-ranked candidates
        if rank <= 10:
            if concerns:
                reasoning += f". Minor note: {concerns[0]}"
        elif rank <= 50:
            n_concerns = min(2, len(concerns))
            reasoning += ". " + "; ".join(concerns[:n_concerns]).capitalize()
        else:
            n_concerns = min(3, len(concerns))
            reasoning += ". Concerns: " + "; ".join(concerns[:n_concerns])

    # Ensure reasoning ends with a period
    reasoning = reasoning.rstrip(".")
    reasoning += "."

    # Trim to safe length
    if len(reasoning) > 350:
        reasoning = reasoning[:347] + "..."

    return reasoning
