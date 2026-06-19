from datetime import date, datetime

# ── JD-derived constants ─────────────────────────────────────────────────────

# Hard skills the JD explicitly requires (must-haves)
CORE_SKILLS = {
    "embeddings", "sentence transformers", "vector database", "faiss", "pinecone",
    "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "information retrieval",
    "semantic search", "hybrid search", "retrieval", "ranking", "recommendation",
    "nlp", "python", "machine learning", "transformers", "hugging face transformers",
    "huggingface", "bge", "e5", "openai embeddings", "dense retrieval",
    "ndcg", "mrr", "map", "learning to rank", "xgboost", "lightgbm",
}

# Nice-to-have skills (bonus, not required)
BONUS_SKILLS = {
    "lora", "qlora", "peft", "fine-tuning llms", "fine tuning", "mlflow",
    "distributed systems", "kafka", "spark", "a/b testing", "feature engineering",
    "mlops", "pytorch", "tensorflow", "scikit-learn",
}

# Hard disqualifiers from the JD
DISQUALIFIER_TITLES = {
    "marketing manager", "hr manager", "operations manager", "accountant",
    "content writer", "sales", "customer support", "civil engineer",
    "mechanical engineer", "project manager", "business analyst",
    "finance", "graphic designer", "ui designer", "ux designer",
}

DISQUALIFIER_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "tech mahindra",
}

# Location fit — JD says Pune/Noida preferred, open to Hyderabad, Mumbai, Delhi NCR
PREFERRED_LOCATIONS = {
    "pune", "noida", "hyderabad", "mumbai", "delhi", "gurugram", "gurgaon",
    "bengaluru", "bangalore", "chennai",
}

TODAY = date.today()


# ── Individual feature functions ──────────────────────────────────────────────

def skill_match_score(candidate):
    """
    Score 0-1 based on how well skills match JD requirements.
    Weights: proficiency level + endorsements + duration + assessment score.
    """
    skills = candidate.get("skills", [])
    assessment_scores = candidate.get("redrob_signals", {}).get("skill_assessment_scores", {})

    if not skills:
        return 0.0

    core_hits = 0.0
    bonus_hits = 0.0

    for skill in skills:
        name = skill["name"].lower().strip()
        proficiency = skill.get("proficiency", "beginner")
        endorsements = skill.get("endorsements", 0)
        duration = skill.get("duration_months", 0)

        # Proficiency weight
        prof_weight = {"beginner": 0.25, "intermediate": 0.5, "advanced": 0.75, "expert": 1.0}
        pw = prof_weight.get(proficiency, 0.25)

        # Endorsement weight (log-scaled, cap at 50)
        import math
        ew = min(math.log1p(endorsements) / math.log1p(50), 1.0)

        # Duration weight (cap at 60 months = 5 years)
        dw = min(duration / 60.0, 1.0)

        # Assessment score weight (if available)
        aw = assessment_scores.get(skill["name"], -1)
        if aw >= 0:
            aw = aw / 100.0
        else:
            aw = pw  # fall back to proficiency if no assessment

        # Combined skill strength
        strength = 0.35 * pw + 0.20 * ew + 0.20 * dw + 0.25 * aw

        if name in CORE_SKILLS:
            core_hits += strength
        elif name in BONUS_SKILLS:
            bonus_hits += strength * 0.4

    # Normalize: assume 6 core skill matches is a perfect score
    core_score = min(core_hits / 6.0, 1.0)
    bonus_score = min(bonus_hits / 3.0, 1.0)

    return round(0.80 * core_score + 0.20 * bonus_score, 4)


def career_fit_score(candidate):
    """
    Score 0-1 based on career trajectory.
    Rewards: product company experience, ML/AI/search titles, right seniority.
    Penalizes: pure consulting, wrong domain (CV, speech, robotics), title-hopping.
    """
    career = candidate.get("career_history", [])
    profile = candidate.get("profile", {})
    current_title = profile.get("current_title", "").lower()

    if not career:
        return 0.0

    score = 0.0

    # Hard disqualifier: current title is completely wrong domain
    for bad_title in DISQUALIFIER_TITLES:
        if bad_title in current_title:
            return 0.05  # near-zero, not absolute zero (in case of mislabeling)

    # Check if entire career is consulting-only
    all_consulting = all(
        any(dc in job.get("company", "").lower() for dc in DISQUALIFIER_COMPANIES)
        for job in career
    )
    if all_consulting and len(career) > 1:
        score -= 0.3

    # Reward ML/AI/search/ranking titles in career history
    good_title_keywords = {
        "ml", "machine learning", "ai", "nlp", "search", "ranking",
        "recommendation", "retrieval", "data scientist", "applied scientist",
        "research engineer", "applied ml", "applied ai"
    }
    title_score = 0.0
    for job in career:
        title = job.get("title", "").lower()
        if any(kw in title for kw in good_title_keywords):
            # Weight by duration
            months = job.get("duration_months", 0)
            title_score += min(months / 24.0, 1.0)  # cap at 2-year contribution

    score += min(title_score / 3.0, 0.5)  # max 0.5 from title trajectory

    # Reward product company experience (non-consulting, non-services)
    product_months = 0
    for job in career:
        company = job.get("company", "").lower()
        industry = job.get("industry", "").lower()
        is_consulting = any(dc in company for dc in DISQUALIFIER_COMPANIES)
        is_services = "it services" in industry or "consulting" in industry
        if not is_consulting and not is_services:
            product_months += job.get("duration_months", 0)

    score += min(product_months / 60.0, 0.4)  # max 0.4 from product company exp

    # Title-hopping penalty: >3 jobs in under 4 years is a flag
    if len(career) >= 4:
        total_months = sum(j.get("duration_months", 0) for j in career[:4])
        if total_months < 48:
            score -= 0.15

    return round(max(0.0, min(score, 1.0)), 4)


def experience_fit_score(candidate):
    """
    Score 0-1 based on years of experience.
    JD wants 5-9 years; sweet spot is 6-8.
    """
    yoe = candidate.get("profile", {}).get("years_of_experience", 0)

    if yoe < 3:
        return 0.0
    elif yoe < 5:
        return 0.3
    elif 5 <= yoe <= 9:
        # Peak at 6-8, slight penalty toward edges
        if 6 <= yoe <= 8:
            return 1.0
        else:
            return 0.8
    elif yoe <= 12:
        return 0.5  # overqualified but not disqualified
    else:
        return 0.3  # too senior for founding-team dynamics


def availability_score(candidate):
    """
    Score 0-1 based on behavioral signals — is this person actually reachable?
    This is a MULTIPLIER concept: a great candidate who's unreachable is useless.
    """
    signals = candidate.get("redrob_signals", {})
    score = 0.0

    # Open to work flag (strong signal)
    if signals.get("open_to_work_flag", False):
        score += 0.25

    # Recent activity (logged in within last 60 days)
    last_active = signals.get("last_active_date", "")
    if last_active:
        try:
            la = date.fromisoformat(last_active)
            days_inactive = (TODAY - la).days
            if days_inactive <= 14:
                score += 0.25
            elif days_inactive <= 30:
                score += 0.20
            elif days_inactive <= 60:
                score += 0.10
            else:
                score += 0.0  # gone dark
        except Exception:
            pass

    # Recruiter response rate
    rrr = signals.get("recruiter_response_rate", 0)
    score += 0.25 * rrr  # direct linear contribution

    # Notice period (JD wants sub-30 days; can buy out up to 30)
    notice = signals.get("notice_period_days", 90)
    if notice <= 30:
        score += 0.15
    elif notice <= 60:
        score += 0.08
    else:
        score += 0.0

    # Verified contact details
    if signals.get("verified_email", False):
        score += 0.05
    if signals.get("verified_phone", False):
        score += 0.05

    return round(min(score, 1.0), 4)


def location_fit_score(candidate):
    """
    Score 0-1 based on location and relocation willingness.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    location = profile.get("location", "").lower()
    country = profile.get("country", "").lower()
    willing_to_relocate = signals.get("willing_to_relocate", False)

    # Outside India entirely — low fit (JD says India-preferred, no visa sponsorship)
    if country != "india":
        if willing_to_relocate:
            return 0.2
        return 0.05

    # In preferred city
    for city in PREFERRED_LOCATIONS:
        if city in location:
            return 1.0

    # Elsewhere in India + willing to relocate
    if willing_to_relocate:
        return 0.6

    return 0.3


def github_score(candidate):
    """
    Score 0-1 from GitHub activity.
    JD values open-source contributions as a bonus signal.
    """
    signals = candidate.get("redrob_signals", {})
    gh = signals.get("github_activity_score", -1)

    if gh == -1:
        return 0.3  # no GitHub — neutral (not penalized heavily)
    return round(gh / 100.0, 4)


def compute_all_features(candidate):
    """
    Returns a dict of all feature scores for one candidate.
    """
    return {
        "candidate_id": candidate["candidate_id"],
        "skill_match":      skill_match_score(candidate),
        "career_fit":       career_fit_score(candidate),
        "experience_fit":   experience_fit_score(candidate),
        "availability":     availability_score(candidate),
        "location_fit":     location_fit_score(candidate),
        "github":           github_score(candidate),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
    from loader import load_candidates

    candidates = load_candidates("sample_candidates.json")
    print(f"\n{'ID':<15} {'Skill':>7} {'Career':>7} {'Exp':>6} {'Avail':>7} {'Loc':>6} {'GH':>6}")
    print("-" * 60)
    for c in candidates[:10]:
        f = compute_all_features(c)
        print(
            f"{f['candidate_id']:<15} "
            f"{f['skill_match']:>7.3f} "
            f"{f['career_fit']:>7.3f} "
            f"{f['experience_fit']:>6.2f} "
            f"{f['availability']:>7.3f} "
            f"{f['location_fit']:>6.2f} "
            f"{f['github']:>6.3f}"
        )