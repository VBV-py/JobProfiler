"""
Data Exploration Script — Run once to understand candidate distributions.

Usage:
    python explore_data.py --input data/sample_candidates.json
    python explore_data.py --input data/candidates.jsonl --limit 5000
"""
import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

from src.data_loader import stream_candidates
from src.honeypot_detector import detect_honeypot


def main():
    parser = argparse.ArgumentParser(description="Explore candidate data")
    parser.add_argument("--input", "-i", default="data/sample_candidates.json",
                        help="Path to candidate data file")
    parser.add_argument("--limit", "-l", type=int, default=None,
                        help="Max candidates to process (for large files)")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"File not found: {args.input}")
        return

    print(f"Loading candidates from: {args.input}")
    print("=" * 60)

    titles = Counter()
    industries = Counter()
    countries = Counter()
    locations = Counter()
    all_skills = Counter()
    companies = Counter()
    experience_values = []
    company_sizes = Counter()
    proficiency_dist = Counter()
    honeypots_found = 0
    total = 0

    for candidate in stream_candidates(args.input):
        total += 1
        if args.limit and total > args.limit:
            break

        profile = candidate.get("profile", {})
        titles[profile.get("current_title", "?")] += 1
        industries[profile.get("current_industry", "?")] += 1
        countries[profile.get("country", "?")] += 1
        locations[profile.get("location", "?")] += 1
        companies[profile.get("current_company", "?")] += 1
        company_sizes[profile.get("current_company_size", "?")] += 1
        experience_values.append(profile.get("years_of_experience", 0))

        for skill in candidate.get("skills", []):
            all_skills[skill["name"]] += 1
            proficiency_dist[skill.get("proficiency", "?")] += 1

        is_hp, reasons = detect_honeypot(candidate)
        if is_hp:
            honeypots_found += 1

    print(f"\nTotal candidates processed: {total:,}")
    print(f"Honeypots detected: {honeypots_found}")

    print(f"\n--- Experience Distribution ---")
    if experience_values:
        print(f"  Min: {min(experience_values):.1f}")
        print(f"  Max: {max(experience_values):.1f}")
        print(f"  Mean: {statistics.mean(experience_values):.1f}")
        print(f"  Median: {statistics.median(experience_values):.1f}")
        # Bucket distribution
        buckets = Counter()
        for v in experience_values:
            if v < 2: buckets["0-2"] += 1
            elif v < 5: buckets["2-5"] += 1
            elif v < 9: buckets["5-9 (sweet spot)"] += 1
            elif v < 12: buckets["9-12"] += 1
            else: buckets["12+"] += 1
        for bucket, count in sorted(buckets.items()):
            pct = count / total * 100
            print(f"  {bucket}: {count:,} ({pct:.1f}%)")

    print(f"\n--- Top 20 Titles ---")
    for title, count in titles.most_common(20):
        pct = count / total * 100
        print(f"  {title}: {count:,} ({pct:.1f}%)")

    print(f"\n--- Industries ---")
    for ind, count in industries.most_common(10):
        pct = count / total * 100
        print(f"  {ind}: {count:,} ({pct:.1f}%)")

    print(f"\n--- Countries ---")
    for country, count in countries.most_common(10):
        pct = count / total * 100
        print(f"  {country}: {count:,} ({pct:.1f}%)")

    print(f"\n--- Top 30 Skills ---")
    for skill, count in all_skills.most_common(30):
        pct = count / total * 100
        print(f"  {skill}: {count:,} ({pct:.1f}%)")

    print(f"\n--- Skill Proficiency Distribution ---")
    for prof, count in proficiency_dist.most_common():
        total_skills = sum(proficiency_dist.values())
        pct = count / total_skills * 100
        print(f"  {prof}: {count:,} ({pct:.1f}%)")

    print(f"\n--- Top 15 Companies ---")
    for comp, count in companies.most_common(15):
        pct = count / total * 100
        print(f"  {comp}: {count:,} ({pct:.1f}%)")

    print(f"\n--- Company Sizes ---")
    for size, count in company_sizes.most_common():
        pct = count / total * 100
        print(f"  {size}: {count:,} ({pct:.1f}%)")


if __name__ == "__main__":
    main()
