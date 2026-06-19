# scorer.py
# Combines all feature scores into a single candidate score.
# Weights are derived from the JD's scoring criteria.

from features import compute_all_features

# ── Scoring weights ────────────────────────────────────────────────────────────
# These reflect what the JD actually prioritizes:
# Skill match and career fit are the dominant signals.
# Availability is a MULTIPLIER — a great candidate who won't respond is useless.

WEIGHTS = {
    "skill_match":    0.35,
    "career_fit":     0.30,
    "experience_fit": 0.15,
    "location_fit":   0.10,
    "github":         0.10,
}

def compute_score(candidate):
    """
    Returns a final float score (0.0 - 1.0) for one candidate.
    Availability is applied as a multiplier on top of the weighted sum.
    """
    f = compute_all_features(candidate)

    # Weighted base score
    base = sum(WEIGHTS[k] * f[k] for k in WEIGHTS)

    # Availability multiplier: ranges from 0.4 (completely dark) to 1.0 (fully active)
    # We never fully zero someone out on availability alone — they might still be great
    avail = f["availability"]
    multiplier = 0.40 + 0.60 * avail

    final = round(base * multiplier, 6)

    return {
        "candidate_id": f["candidate_id"],
        "score":        final,
        "features":     f,
        "multiplier":   round(multiplier, 4),
    }


def score_all(candidates):
    """
    Scores all candidates and returns them sorted best-first.
    """
    results = []
    for c in candidates:
        results.append(compute_score(c))

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from loader import load_candidates

    candidates = load_candidates("sample_candidates.json")
    ranked = score_all(candidates)

    print(f"\nTop 15 candidates:\n")
    print(f"{'Rank':<5} {'ID':<15} {'Score':>7} {'Mult':>6} {'Skill':>7} {'Career':>7} {'Exp':>6} {'Loc':>6}")
    print("-" * 70)
    for i, r in enumerate(ranked[:15], 1):
        f = r["features"]
        print(
            f"{i:<5} "
            f"{r['candidate_id']:<15} "
            f"{r['score']:>7.4f} "
            f"{r['multiplier']:>6.3f} "
            f"{f['skill_match']:>7.3f} "
            f"{f['career_fit']:>7.3f} "
            f"{f['experience_fit']:>6.2f} "
            f"{f['location_fit']:>6.2f}"
        )

    print(f"\nBottom 5:")
    print("-" * 70)
    for i, r in enumerate(ranked[-5:], len(ranked) - 4):
        f = r["features"]
        print(
            f"{i:<5} "
            f"{r['candidate_id']:<15} "
            f"{r['score']:>7.4f} "
            f"{f['career_fit']:>7.3f} "
            f"{f['skill_match']:>7.3f}"
        )