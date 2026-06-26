"""
Ranking Pipeline.

Orchestrates the full ranking workflow:
  1. Stream candidates from file
  2. Score each candidate
  3. Sort by composite score
  4. Return top N candidates with ranks assigned
"""
import sys
from src.data_loader import stream_candidates
from src.scoring import score_candidate


def rank_candidates(
    candidates_path: str,
    top_n: int = 100,
    show_progress: bool = True,
) -> list[dict]:
    
    scored_results = []
    total = 0
    honeypot_count = 0
    skipped_count = 0

    if show_progress:
        print(f"Loading and scoring candidates from: {candidates_path}")
        print("=" * 60)

    try:
        from tqdm import tqdm
        iterator = tqdm(
            stream_candidates(candidates_path),
            desc="Scoring candidates",
            unit=" candidates",
        )
    except ImportError:
        iterator = stream_candidates(candidates_path)

    for candidate in iterator:
        total += 1
        result = score_candidate(candidate)

        if result["is_honeypot"]:
            honeypot_count += 1
            continue  # Exclude honeypots from ranking entirely

        if result["skipped"]:
            skipped_count += 1
            # Still include in case we need to fill top N,
            # but they'll have very low scores
            scored_results.append({
                "candidate_id": result["candidate_id"],
                "score": result["composite_score"],
                "components": result["components"],
                "candidate": candidate,
            })
            continue

        scored_results.append({
            "candidate_id": result["candidate_id"],
            "score": result["composite_score"],
            "components": result["components"],
            "candidate": candidate,
        })

    if show_progress:
        print(f"\n{'=' * 60}")
        print(f"Total candidates processed:  {total:,}")
        print(f"Honeypots detected & removed: {honeypot_count}")
        print(f"Coarse-filtered (low title): {skipped_count:,}")
        print(f"Candidates scored in detail:  {total - honeypot_count - skipped_count:,}")

    # Sort by score descending (rounded to 4 decimal places to match CSV output), then candidate_id ascending for tiebreaks
    scored_results.sort(key=lambda x: (-round(x["score"], 4), x["candidate_id"]))

    # Take top N and assign ranks
    top = scored_results[:top_n]
    for i, entry in enumerate(top):
        entry["rank"] = i + 1

    if show_progress and top:
        print(f"\nTop {len(top)} candidates selected.")
        print(f"  Score range: {top[0]['score']:.4f} (rank 1) -> "
              f"{top[-1]['score']:.4f} (rank {len(top)})")

    return top
