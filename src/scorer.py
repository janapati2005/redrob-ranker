# scorer.py
from features import compute_all_features

WEIGHTS = {
    "skill_match":    0.35,
    "career_fit":     0.30,
    "experience_fit": 0.15,
    "location_fit":   0.10,
    "github":         0.10,
}


def compute_score(candidate):
    f = compute_all_features(candidate)
    base = sum(WEIGHTS[k] * f[k] for k in WEIGHTS)
    multiplier = 0.40 + 0.60 * f["availability"]
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
    Tiebreaker: candidate_id ascending (matches competition validator rule).
    """
    results = [compute_score(c) for c in candidates]
    results.sort(key=lambda x: (-x["score"], x["candidate_id"]))
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