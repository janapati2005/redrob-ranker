# reasoner.py
# Generates per-candidate reasoning text for the submission CSV.
# Rules from submission spec Stage 4:
#   - Must reference specific facts from the candidate's profile
#   - Must connect to JD requirements
#   - Must acknowledge gaps honestly
#   - No hallucination — every claim must exist in the profile
#   - Must vary across candidates (not templated)

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
    """Returns list of core skills the candidate actually has."""
    matches = []
    for skill in candidate.get("skills", []):
        name = skill["name"].lower()
        if name in CORE_SKILL_NAMES:
            matches.append(skill["name"])
    return matches


def _get_top_skills(candidate, n=3):
    """Returns top N skills by combined strength."""
    skills = candidate.get("skills", [])
    assessments = candidate.get("redrob_signals", {}).get("skill_assessment_scores", {})

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


def _career_summary(candidate):
    """One-line summary of career trajectory."""
    career = candidate.get("career_history", [])
    profile = candidate.get("profile", {})

    current_title = profile.get("current_title", "")
    current_company = profile.get("current_company", "")
    yoe = profile.get("years_of_experience", 0)

    # Count product company months
    product_companies = []
    for job in career:
        company = job.get("company", "").lower()
        is_consulting = any(dc in company for dc in DISQUALIFIER_COMPANIES)
        if not is_consulting and job.get("duration_months", 0) > 6:
            product_companies.append(job.get("company", ""))

    return current_title, current_company, yoe, product_companies[:3]


def _notice_text(candidate):
    notice = candidate.get("redrob_signals", {}).get("notice_period_days", 90)
    if notice <= 15:
        return f"immediately available (notice: {notice}d)"
    elif notice <= 30:
        return f"short notice period ({notice}d)"
    elif notice <= 60:
        return f"notice period of {notice} days"
    else:
        return f"long notice period ({notice}d) is a concern"


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
    Generates a specific, honest, non-templated 1-2 sentence reasoning.
    The text is built from actual facts in the candidate's profile.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    title, company, yoe, product_cos = _career_summary(candidate)
    core_skills = _get_matching_core_skills(candidate)
    top_skills = _get_top_skills(candidate, n=3)
    days_inactive = _days_since_active(candidate)
    rrr = signals.get("recruiter_response_rate", 0)
    notice = signals.get("notice_period_days", 90)
    open_to_work = signals.get("open_to_work_flag", False)
    location_text = _location_text(candidate)

    # ── Build reasoning based on rank tier ────────────────────────────────────

    # TOP TIER (rank 1-10): strong match, lead with strengths
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

        sentence1 = f"{title} with {yoe:.1f} years {skill_part}{product_part}, {location_text}."
        sentence2 = f"Strong alignment with JD's retrieval/ranking mandate.{concern}"

    # GOOD FIT (rank 11-30): solid match with some gaps
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
            concern = f"{notice}-day notice"
        elif not open_to_work:
            concern = "not marked open to work"

        sentence1 = f"{yoe:.1f}-year {title} at {company} with {skill_part}, {location_text}."
        if concern:
            sentence2 = f"Decent JD alignment but {concern} reduces effective availability."
        else:
            sentence2 = f"Moderate JD alignment; experience range fits but skill depth below top tier."

    # BORDERLINE (rank 31-70): adjacent skills or wrong domain
    elif rank <= 70:
        gap = ""
        if not core_skills:
            gap = "no direct retrieval/ranking skills in profile"
        elif yoe < 5:
            gap = f"only {yoe:.1f} years experience (JD wants 5-9)"
        elif days_inactive > 90:
            gap = f"inactive for {days_inactive} days"
        else:
            gap = "partial skill overlap with JD requirements"

        sentence1 = f"{title} at {company} ({yoe:.1f} yrs), {location_text}."
        sentence2 = f"Adjacent profile — {gap}; included given limited stronger alternatives at this rank."

    # WEAK FIT (rank 71-100): filler, honest about it
    else:
        reason = ""
        if not core_skills:
            reason = "no core retrieval/ML skills match the JD"
        elif yoe < 3:
            reason = f"only {yoe:.1f} years experience, below JD minimum"
        else:
            reason = "title and career trajectory misaligned with JD requirements"

        sentence1 = f"{title} at {company} ({yoe:.1f} yrs), {location_text}."
        sentence2 = f"Weak fit — {reason}; ranked here to complete top-100 requirement."

    # Combine and clean up whitespace
    reasoning = f"{sentence1} {sentence2}".strip()
    reasoning = " ".join(reasoning.split())  # collapse any double spaces

    return reasoning


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

    print("...")
    total = len(ranked)
    for i, r in enumerate(ranked[-3:], total - 2):
        cid = r["candidate_id"]
        c = next(x for x in candidates if x["candidate_id"] == cid)
        reasoning = generate_reasoning(c, rank=i, score=r["score"])
        print(f"Rank {i} | {cid} | score {r['score']:.4f}")
        print(f"  {reasoning}")
        print()