"""
Behavioral Signals Scoring Module.

Computes a behavioral engagement modifier (0.0 – 1.0) from the 23
Redrob platform signals.

The JD is explicit:
"A perfect-on-paper candidate who hasn't logged in for 6 months and has
a 5% recruiter response rate is, for hiring purposes, not actually available.
Down-weight them appropriately."

Signal importance hierarchy (from JD context):
  HIGH:   recruiter_response_rate, last_active_date, open_to_work_flag
  MEDIUM: notice_period_days, interview_completion_rate, avg_response_time_hours
  LOW:    profile_completeness, github_activity, verification flags, saved_by_recruiters
"""
from datetime import datetime
from src.config import (
    NOTICE_IDEAL_MAX, NOTICE_OKAY_MAX, NOTICE_PENALTY_START,
    RESPONSE_TIME_FAST, RESPONSE_TIME_OK, RESPONSE_TIME_SLOW,
    RESPONSE_TIME_VERY_SLOW,
    INACTIVE_RECENT, INACTIVE_MODERATE, INACTIVE_STALE, INACTIVE_DEAD,
)

# Reference date for recency calculations
REFERENCE_DATE = datetime(2026, 6, 1)


def compute_behavioral_modifier(candidate: dict) -> float:
    
    signals = candidate.get("redrob_signals", {})
    if not signals:
        return 0.5  # No signals → neutral

    weighted_sum = 0.0
    total_weight = 0.0

    # ---- HIGH PRIORITY SIGNALS ----

    response_rate = signals.get("recruiter_response_rate", 0.0)
    weighted_sum += response_rate * 3.0
    total_weight += 3.0

    last_active_str = signals.get("last_active_date", "")
    recency_score = 0.5  
    if last_active_str:
        try:
            last_active = datetime.strptime(last_active_str, "%Y-%m-%d")
            days_inactive = (REFERENCE_DATE - last_active).days
            if days_inactive < 0:
                days_inactive = 0  

            if days_inactive <= INACTIVE_RECENT:
                recency_score = 1.0
            elif days_inactive <= INACTIVE_MODERATE:
                recency_score = 0.75
            elif days_inactive <= INACTIVE_STALE:
                recency_score = 0.40
            elif days_inactive <= INACTIVE_DEAD:
                recency_score = 0.15
            else:
                recency_score = 0.05  
        except ValueError:
            recency_score = 0.5
    weighted_sum += recency_score * 2.5
    total_weight += 2.5

    open_to_work = signals.get("open_to_work_flag", False)
    weighted_sum += (1.0 if open_to_work else 0.3) * 2.0
    total_weight += 2.0

    # ---- MEDIUM PRIORITY SIGNALS ----

    notice = signals.get("notice_period_days", 60)
    if notice <= NOTICE_IDEAL_MAX:
        notice_score = 1.0
    elif notice <= NOTICE_OKAY_MAX:
        notice_score = 0.70
    elif notice <= NOTICE_PENALTY_START:
        notice_score = 0.40
    elif notice <= 120:
        notice_score = 0.20
    else:
        notice_score = 0.10  
    weighted_sum += notice_score * 1.5
    total_weight += 1.5

    interview_rate = signals.get("interview_completion_rate", 0.5)
    weighted_sum += interview_rate * 1.5
    total_weight += 1.5

    avg_hours = signals.get("avg_response_time_hours", 72)
    if avg_hours <= RESPONSE_TIME_FAST:
        time_score = 1.0
    elif avg_hours <= RESPONSE_TIME_OK:
        time_score = 0.80
    elif avg_hours <= RESPONSE_TIME_SLOW:
        time_score = 0.55
    elif avg_hours <= RESPONSE_TIME_VERY_SLOW:
        time_score = 0.30
    else:
        time_score = 0.10
    weighted_sum += time_score * 1.0
    total_weight += 1.0

    offer_rate = signals.get("offer_acceptance_rate", -1)
    if offer_rate >= 0:
        weighted_sum += offer_rate * 1.0
        total_weight += 1.0

    # ---- LOW PRIORITY SIGNALS ----

    completeness = signals.get("profile_completeness_score", 50) / 100.0
    weighted_sum += completeness * 0.5
    total_weight += 0.5

    github = signals.get("github_activity_score", -1)
    if github >= 0:
        github_score = github / 100.0
        weighted_sum += github_score * 0.8
        total_weight += 0.8

    verified_count = 0
    if signals.get("verified_email"):
        verified_count += 1
    if signals.get("verified_phone"):
        verified_count += 1
    if signals.get("linkedin_connected"):
        verified_count += 1
    verified_score = verified_count / 3.0
    weighted_sum += verified_score * 0.5
    total_weight += 0.5

    saved = signals.get("saved_by_recruiters_30d", 0)
    saved_score = min(saved / 10.0, 1.0)
    weighted_sum += saved_score * 0.5
    total_weight += 0.5

    views = signals.get("profile_views_received_30d", 0)
    views_score = min(views / 20.0, 1.0)
    weighted_sum += views_score * 0.3
    total_weight += 0.3

    appearances = signals.get("search_appearance_30d", 0)
    appear_score = min(appearances / 100.0, 1.0)
    weighted_sum += appear_score * 0.2
    total_weight += 0.2

    if total_weight > 0:
        return weighted_sum / total_weight
    return 0.5
