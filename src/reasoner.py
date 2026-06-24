import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from datetime import date

TODAY = date.today()

DISQUALIFIER_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "tech mahindra"
}

CORE_SKILL_NAMES = {
    "embeddings", "sentence transformers", "faiss", "pinecone",
    "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch",
    "information retrieval", "semantic search", "hybrid search",
    "retrieval", "ranking", "recommendation", "nlp",
    "machine learning", "transformers", "hugging face transformers",
    "huggingface", "ndcg", "mrr", "learning to rank",
    "xgboost", "lightgbm", "vector database",
}


def _get_matching_core_skills(candidate):
    skills = candidate.get("skills", [])
    return [s["name"] for s in skills if s["name"].lower() in CORE_SKILL_NAMES]


def _get_top_skills(candidate, n=3):
    skills = candidate.get("skills", [])
    assessments = candidate.get("redrob_signals", {}).get(
        "skill_assessment_scores", {}
    )

    def strength(s):
        prof = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}
        p = prof.get(s.get("proficiency", "beginner"), 1)
        e = min(s.get("endorsements", 0), 50)
        d = min(s.get("duration_months", 0), 60)
        a = assessments.get(s["name"], -1)
        return p * 10 + e * 0.3 + d * 0.2 + (a * 0.1 if a >= 0 else 0)

    sorted_skills = sorted(skills, key=strength, reverse=True)
    return [s["name"] for s in sorted_skills[:n]]


def _days_since_active(candidate):
    last_active = candidate.get("redrob_signals", {}).get("last_active_date", "")
    if not last_active:
        return 999
    try:
        return (TODAY - date.fromisoformat(last_active)).days
    except Exception:
        return 999


def _location_text(candidate):
    profile = candidate.get("profile", {})
    location = profile.get("location", "")
    country = profile.get("country", "")
    willing = candidate.get("redrob_signals", {}).get("willing_to_relocate", False)

    if country != "India":
        if willing:
            return f"based in {location}, {country} but willing to relocate"
        return f"based in {location}, {country} — location mismatch"
    return f"based in {location}"


def generate_reasoning(candidate, rank, score):
    """
    Generates specific, honest 1-2 sentence reasoning.
    Every fact pulled from actual candidate data — no hallucination.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    title = profile.get("current_title", "")
    company = profile.get("current_company", "")
    yoe = profile.get("years_of_experience", 0)

    core_skills = _get_matching_core_skills(candidate)
    top_skills = _get_top_skills(candidate, n=3)
    days_inactive = _days_since_active(candidate)
    rrr = signals.get("recruiter_response_rate", 0)
    notice = signals.get("notice_period_days", 90)
    open_to_work = signals.get("open_to_work_flag", False)
    location_text = _location_text(candidate)

    # Product companies in career
    career = candidate.get("career_history", [])
    product_cos = []
    for job in career:
        c = job.get("company", "").lower()
        is_consulting = any(dc in c for dc in DISQUALIFIER_COMPANIES)
        if not is_consulting and job.get("duration_months", 0) > 6:
            product_cos.append(job.get("company", ""))

    # ── TOP TIER (rank 1-10) ───────────────────────────────────────────────
    if rank <= 10:
        skill_part = ""
        if core_skills:
            skill_part = f"with hands-on {', '.join(core_skills[:3])} experience"
        elif top_skills:
            skill_part = f"with skills in {', '.join(top_skills[:3])}"

        product_part = ""
        if product_cos:
            product_part = f" at product companies ({', '.join(product_cos[:2])})"

        concern = ""
        if days_inactive > 45:
            concern = f" Concern: inactive for {days_inactive} days."
        elif notice > 60:
            concern = f" Concern: {notice}-day notice period."
        elif rrr < 0.3:
            concern = f" Concern: low recruiter response rate ({rrr:.0%})."

        s1 = f"{title} with {yoe:.1f} years {skill_part}{product_part}, {location_text}."
        s2 = f"Strong alignment with JD retrieval/ranking mandate.{concern}"

    # ── GOOD FIT (rank 11-30) ──────────────────────────────────────────────
    elif rank <= 30:
        skill_part = ""
        if core_skills:
            skill_part = f"{', '.join(core_skills[:2])} background"
        elif top_skills:
            skill_part = f"{top_skills[0]} background"

        concern = ""
        if days_inactive > 60:
            concern = f"inactive {days_inactive} days"
        elif notice > 90:
            concern = f"{notice}-day notice period"
        elif not open_to_work:
            concern = "not marked open to work"

        s1 = f"{yoe:.1f}-year {title} at {company} with {skill_part}, {location_text}."
        if concern:
            s2 = f"Solid JD alignment but {concern} reduces effective availability."
        else:
            s2 = f"Good JD alignment; skill depth slightly below top tier."

    # ── BORDERLINE (rank 31-70) ────────────────────────────────────────────
    elif rank <= 70:
        gap = ""
        if not core_skills:
            gap = "no direct retrieval/ranking skills confirmed in profile"
        elif yoe < 5:
            gap = f"only {yoe:.1f} years experience (JD requires 5-9)"
        elif days_inactive > 90:
            gap = f"platform inactive for {days_inactive} days"
        else:
            gap = "partial skill overlap with JD core requirements"

        s1 = f"{title} at {company} ({yoe:.1f} yrs), {location_text}."
        s2 = f"Adjacent profile — {gap}; included ahead of weaker alternatives."

    # ── WEAK FIT (rank 71-100) ─────────────────────────────────────────────
    else:
        if not core_skills:
            reason = f"no core retrieval or ML skills verified in profile"
        elif yoe < 3:
            reason = f"only {yoe:.1f} years total experience, below JD minimum of 5"
        elif title.lower() in {"marketing manager", "hr manager", "accountant",
                                "operations manager", "customer support"}:
            reason = f"domain mismatch — {title} role outside AI/ML scope"
        else:
            reason = "career trajectory and skill depth below shortlist threshold"

        s1 = f"{title} at {company} ({yoe:.1f} yrs), {location_text}."
        s2 = f"Below shortlist threshold — {reason}; lowest-scoring inclusion in top-100."

    reasoning = f"{s1} {s2}".strip()
    return " ".join(reasoning.split())


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from loader import load_candidates
    from scorer import score_all

    candidates = load_candidates("sample_candidates.json")
    ranked = score_all(candidates)

    print("\nSample reasoning for top 5 and bottom 3:\n")
    for i, r in enumerate(ranked[:5], 1):
        cid = r["candidate_id"]
        c = next(x for x in candidates if x["candidate_id"] == cid)
        reasoning = generate_reasoning(c, rank=i, score=r["score"])
        print(f"Rank {i} | {cid} | score {r['score']:.4f}")
        print(f"  {reasoning}")
        print()

    total = len(ranked)
    for i, r in enumerate(ranked[-3:], total - 2):
        cid = r["candidate_id"]
        c = next(x for x in candidates if x["candidate_id"] == cid)
        reasoning = generate_reasoning(c, rank=i, score=r["score"])
        print(f"Rank {i} | {cid} | score {r['score']:.4f}")
        print(f"  {reasoning}")
        print()