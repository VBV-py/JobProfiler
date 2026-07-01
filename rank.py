#!/usr/bin/env python3
"""
Redrob Hackathon — Intelligent Candidate Discovery & Ranking

"""
import argparse
import csv
import sys
import time
from pathlib import Path

from src.ranker import rank_candidates
from src.reasoning import generate_reasoning


def write_csv(entries: list[dict], output_path: str) -> None:
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Round scores to 4 decimal places and re-sort to satisfy tie-break rule:
    # "If two candidates have the same score, break ties by candidate_id ascending."
    for entry in entries:
        entry["rounded_score"] = round(entry["score"], 4)

    entries.sort(key=lambda x: (-x["rounded_score"], x["candidate_id"]))

    # Re-assign ranks after re-sorting
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header row (must be exactly this)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        # Data rows
        for entry in entries:
            writer.writerow([
                entry["candidate_id"],
                entry["rank"],
                f"{entry['rounded_score']:.4f}",
                entry["reasoning"],
            ])


def main():
    parser = argparse.ArgumentParser(
        description="Rank candidates for the Redrob Hackathon challenge.",
        epilog="Example: python rank.py --candidates ./data/candidates.jsonl --out ./output/team_Tech Elites.csv",
    )
    parser.add_argument(
        "--candidates", "-c",
        required=True,
        help="Path to candidates file (.jsonl, .jsonl.gz, or .json)",
    )
    parser.add_argument(
        "--out", "-o",
        default="./output/submission.csv",
        help="Output CSV path (default: ./output/team_Tech Elites.csv)",
    )
    parser.add_argument(
        "--top-n", "-n",
        type=int,
        default=100,
        help="Number of top candidates (default: 100)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress output",
    )
    args = parser.parse_args()

    # Validate input
    input_path = Path(args.candidates)
    if not input_path.exists():
        print(f"ERROR: Candidates file not found: {args.candidates}")
        sys.exit(1)

    print("=" * 60)
    print("  Redrob Hackathon -- Candidate Ranking System")
    print("=" * 60)
    print(f"  Input:  {args.candidates}")
    print(f"  Output: {args.out}")
    print(f"  Top N:  {args.top_n}")
    print("=" * 60)
    print()

    start_time = time.time()

    # ---- STEP 1: Score & Rank ----
    top_candidates = rank_candidates(
        args.candidates,
        top_n=args.top_n,
        show_progress=not args.quiet,
    )

    # ---- STEP 2: Generate Reasoning ----
    print("\nGenerating per-candidate reasoning...")
    for entry in top_candidates:
        entry["reasoning"] = generate_reasoning(entry)

    # ---- STEP 3: Write CSV ----
    write_csv(top_candidates, args.out)

    elapsed = time.time() - start_time

    # ---- STEP 4: Summary ----
    print()
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  [OK] Wrote {len(top_candidates)} candidates to: {args.out}")
    print(f"  [TIME] Total time: {elapsed:.1f}s / 300s budget")

    if elapsed > 300:
        print("  [WARNING] Exceeded 5-minute time limit!")
    else:
        remaining = 300 - elapsed
        print(f"  [OK] Within budget -- {remaining:.0f}s remaining")

    if top_candidates:
        print(f"\n  Top 5 ranked candidates:")
        for entry in top_candidates[:5]:
            print(f"    Rank {entry['rank']:>3}: {entry['candidate_id']}  "
                  f"score={entry['score']:.4f}")
        print(f"    ...")
        last = top_candidates[-1]
        print(f"    Rank {last['rank']:>3}: {last['candidate_id']}  "
              f"score={last['score']:.4f}")

    print()
    print("  Next step: python validate_submission.py", args.out)
    print("=" * 60)


if __name__ == "__main__":
    main()
