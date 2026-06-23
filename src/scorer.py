# scorer.py — UPGRADED
# Combines all 9 feature scores into one final score.
# semantic score comes from embedder.py (Stage 2 of pipeline).
# availability is a multiplier — not a direct weight.
#
# Weight reasoning:
# skill_match (27%)  — JD names exact tools, technical fit is primary gate
# career_fit (24%)   — JD explicitly warns about keyword stuffers
# experience_fit (10%) — years matter but what you did matters more
# semantic (15%)     — meaning-level JD match from sentence-transformers
# location_fit (8%)  — important but solvable with relocation
# platform_demand (6%) — crowd-sourced recruiter validation
# github (5%)        — JD calls it a strong positive signal
# education (3%)     — tier_1 education is a differentiator for founding team
# profile_quality (2%) — engagement and credibility signal

from features import compute_all_features

WEIGHTS = {
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


def compute_score(candidate, semantic_score=0.0):
    """
    Returns final score (0.0 - 1.0) for one candidate.
    semantic_score comes from the embedder (0.0 if not available).
    Availability is a multiplier — poor availability scales down entire score.
    """
    f = compute_all_features(candidate)

    # Career fit guard — wrong domain candidates cannot be rescued by semantic
    effective_semantic = semantic_score
    if f["career_fit"] <= 0.05:
        effective_semantic = 0.0
    f["semantic"] = effective_semantic

    # Weighted base score
    base = sum(WEIGHTS[k] * f[k] for k in WEIGHTS)

    # Availability multiplier: 0.40 floor means inactive != worthless
    multiplier = 0.40 + 0.60 * f["availability"]

    final = round(base * multiplier, 6)

    return {
        "candidate_id": f["candidate_id"],
        "score":        final,
        "features":     f,
        "multiplier":   round(multiplier, 4),
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
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from loader import load_candidates

    candidates = load_candidates("sample_candidates.json")
    ranked = score_all(candidates)

    print(f"\nTop 15 candidates:\n")
    print(f"{'Rank':<5} {'ID':<15} {'Score':>7} {'Sem':>6} {'Skill':>6} {'Career':>7} {'Exp':>5} {'Plat':>6}")
    print("-" * 70)
    for i, r in enumerate(ranked[:15], 1):
        f = r["features"]
        print(
            f"{i:<5} "
            f"{r['candidate_id']:<15} "
            f"{r['score']:>7.4f} "
            f"{f.get('semantic', 0):>6.3f} "
            f"{f['skill_match']:>6.3f} "
            f"{f['career_fit']:>7.3f} "
            f"{f['experience_fit']:>5.2f} "
            f"{f['platform_demand']:>6.3f}"
        )