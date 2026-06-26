"""
Honeypot Detection Module.

The dataset contains ~80 honeypot candidates with subtly impossible profiles.
Examples from the spec:
  - 8 years of experience at a company founded 3 years ago
  - "expert" proficiency in 10 skills with 0 years used
  - Career dates that are internally contradictory

Honeypots are forced to relevance tier 0 in the ground truth.
Submissions with honeypot rate > 10% in top 100 are DISQUALIFIED.

Strategy: Apply multiple heuristic checks. A single anomaly is a yellow flag;
multiple anomalies = honeypot.
"""
from datetime import datetime


# Reference date for calculations (roughly "now" in the dataset context)
REFERENCE_DATE = datetime(2026, 6, 1)


def detect_honeypot(candidate: dict) -> tuple[bool, list[str]]:
    
    red_flags = []

    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    years_exp = profile.get("years_of_experience", 0)

    # ---- CHECK 1: Expert skills with 0 duration ----
    # Honeypot pattern: "expert" proficiency in many skills with 0 months used
    expert_zero = 0
    for skill in skills:
        prof = skill.get("proficiency", "")
        duration = skill.get("duration_months", 1)
        if prof == "expert" and duration == 0:
            expert_zero += 1

    if expert_zero >= 3:
        red_flags.append(
            f"{expert_zero} skills listed as 'expert' with 0 months duration"
        )
    elif expert_zero >= 2:
        # Two is suspicious
        red_flags.append(
            f"{expert_zero} skills listed as 'expert' with 0 months duration"
        )

    # ---- CHECK 2: Too many expert skills for experience level ----
    expert_count = sum(1 for s in skills if s.get("proficiency") == "expert")
    if expert_count >= 10:
        red_flags.append(
            f"{expert_count} expert-level skills — unrealistically high"
        )
    elif expert_count >= 7 and years_exp < 4:
        red_flags.append(
            f"{expert_count} expert skills with only {years_exp:.1f} years experience"
        )

    # ---- CHECK 3: Claimed experience vs actual career span ----
    if career:
        try:
            start_dates = []
            for role in career:
                sd = role.get("start_date")
                if sd:
                    start_dates.append(datetime.strptime(sd, "%Y-%m-%d"))

            if start_dates:
                earliest = min(start_dates)
                career_span_years = (REFERENCE_DATE - earliest).days / 365.25

                # Claimed experience exceeds possible career span by a lot
                if years_exp > career_span_years + 3:
                    red_flags.append(
                        f"Claims {years_exp:.1f} yrs experience but career "
                        f"starts only {career_span_years:.1f} yrs ago"
                    )
        except (ValueError, TypeError):
            pass

    # ---- CHECK 4: Role duration vs date math mismatch ----
    for role in career:
        try:
            start = datetime.strptime(role["start_date"], "%Y-%m-%d")
            if role.get("end_date"):
                end = datetime.strptime(role["end_date"], "%Y-%m-%d")
            elif role.get("is_current"):
                end = REFERENCE_DATE
            else:
                continue

            actual_months = max((end - start).days / 30.44, 0)
            claimed_months = role.get("duration_months", 0)

            # If claimed duration wildly exceeds actual date range
            # e.g., claims 96 months but dates only span 24 months
            if claimed_months > 0 and claimed_months > actual_months * 2 + 6:
                red_flags.append(
                    f"Role at {role.get('company', '?')}: claims {claimed_months} "
                    f"months but dates span ~{actual_months:.0f} months"
                )
                break  # One such flag is enough
        except (ValueError, TypeError, KeyError):
            pass

    # ---- CHECK 5: Impossible overlapping career dates ----
    dated_roles = []
    for role in career:
        try:
            s = datetime.strptime(role["start_date"], "%Y-%m-%d")
            if role.get("end_date"):
                e = datetime.strptime(role["end_date"], "%Y-%m-%d")
            elif role.get("is_current"):
                e = REFERENCE_DATE
            else:
                continue
            dated_roles.append((s, e, role.get("company", "?")))
        except (ValueError, TypeError, KeyError):
            pass

    dated_roles.sort(key=lambda x: x[0])
    for i in range(len(dated_roles) - 1):
        _, end_i, comp_i = dated_roles[i]
        start_j, _, comp_j = dated_roles[i + 1]
        overlap_days = (end_i - start_j).days
        if overlap_days > 180:  # > 6 months overlap is suspicious
            red_flags.append(
                f"Roles at {comp_i} and {comp_j} overlap by "
                f"{overlap_days} days (~{overlap_days // 30} months)"
            )
            break

    # ---- CHECK 6: Skill duration exceeds total experience ----
    if years_exp > 0:
        max_possible_months = years_exp * 12 + 24  # generous buffer
        impossibly_long_skills = 0
        for skill in skills:
            if skill.get("duration_months", 0) > max_possible_months:
                impossibly_long_skills += 1

        if impossibly_long_skills >= 2:
            red_flags.append(
                f"{impossibly_long_skills} skills with duration exceeding "
                f"total career span ({years_exp:.0f} years)"
            )

    # ---- CHECK 7: Profile completeness vs verified signals mismatch ----
    completeness = signals.get("profile_completeness_score", 50)
    verified_email = signals.get("verified_email", True)
    verified_phone = signals.get("verified_phone", True)

    # Very high completeness but nothing verified — suspicious
    if completeness > 90 and not verified_email and not verified_phone:
        # This alone isn't a strong honeypot signal, but combined with others...
        pass  # Don't flag by itself

    # ---- CHECK 8: Signup date after last_active_date ----
    try:
        signup = datetime.strptime(signals.get("signup_date", ""), "%Y-%m-%d")
        last_active = datetime.strptime(signals.get("last_active_date", ""), "%Y-%m-%d")
        if signup > last_active:
            red_flags.append(
                f"Signup date ({signals['signup_date']}) is after "
                f"last active date ({signals['last_active_date']})"
            )
    except (ValueError, TypeError):
        pass

    # ---- DECISION: 2+ red flags = honeypot ----
    is_honeypot = len(red_flags) >= 2

    return is_honeypot, red_flags
