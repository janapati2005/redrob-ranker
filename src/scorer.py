# scorer.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from features import compute_all_features

# Full weights when semantic is available (local run)
WEIGHTS_FULL = {
    "semantic":        0.15,
    "skill_match":     0.27,
    "career_fit":      0.24,
    "experience_fit":  0.10,
    "location_fit":    0.08,
    "platform_demand": 0.06,
    "github":          0.05,
    "education":       0.03,
    "profile_quality": 0.02,
}

# Redistributed weights when semantic unavailable (cloud/no-semantic mode)
# 15% redistributed proportionally across other 8 signals
# so total still = 100% and scores are comparable
WEIGHTS_NO_SEMANTIC = {
    "skill_match":     0.32,  # 0.27 + share of 0.15
    "career_fit":      0.28,  # 0.24 + share
    "experience_fit":  0.12,  # 0.10 + share
    "location_fit":    0.09,  # 0.08 + share
    "platform_demand": 0.07,  # 0.06 + share
    "github":          0.06,  # 0.05 + share
    "education":       0.04,  # 0.03 + share
    "profile_quality": 0.02,  # 0.02 + share
}


def compute_score(candidate, semantic_score=0.0):
    """
    Returns final score (0.0 - 1.0) for one candidate.
    If semantic_score=0.0, uses redistributed weights so total = 100%.
    Availability is a multiplier — poor availability scales down entire score.
    """
    f = compute_all_features(candidate)

    # Career fit guard — wrong domain cannot be rescued by semantic
    effective_semantic = semantic_score
    if f["career_fit"] <= 0.05:
        effective_semantic = 0.0
    f["semantic"] = effective_semantic

    # Choose weights based on whether semantic is available
    if effective_semantic > 0.0:
        weights = WEIGHTS_FULL
        base = sum(weights[k] * f[k] for k in weights)
    else:
        # No semantic — redistribute its weight so score is still out of 1.0
        weights = WEIGHTS_NO_SEMANTIC
        base = sum(weights[k] * f[k] for k in weights)

    # Availability multiplier
    multiplier = 0.40 + 0.60 * f["availability"]
    final = round(base * multiplier, 6)

    return {
        "candidate_id": f["candidate_id"],
        "score":        final,
        "features":     f,
        "multiplier":   round(multiplier, 4),
        "has_semantic": effective_semantic > 0.0,
    }


def score_all(candidates, semantic_scores=None):
    """
    Scores all candidates and returns them sorted best-first.
    Tiebreaker: candidate_id ascending (matches competition validator rule).
    """
    if semantic_scores is None:
        semantic_scores = {}

    results = []
    for c in candidates:
        cid = c["candidate_id"]
        sem_score = semantic_scores.get(cid, 0.0)
        results.append(compute_score(c, semantic_score=sem_score))

    results.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    return results


if __name__ == "__main__":
    from loader import load_candidates
    candidates = load_candidates("sample_candidates.json")
    ranked = score_all(candidates)

    print(f"\nTop 15 candidates:\n")
    print(f"{'Rank':<5} {'ID':<15} {'Score':>7} {'Skill':>6} "
          f"{'Career':>7} {'Exp':>5} {'Plat':>6}")
    print("-" * 60)
    for i, r in enumerate(ranked[:15], 1):
        f = r["features"]
        print(
            f"{i:<5} {r['candidate_id']:<15} {r['score']:>7.4f} "
            f"{f['skill_match']:>6.3f} {f['career_fit']:>7.3f} "
            f"{f['experience_fit']:>5.2f} {f['platform_demand']:>6.3f}"
        )