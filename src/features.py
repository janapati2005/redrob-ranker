# features.py
# Extracts 9 scored signals from each candidate profile.
# Each signal returns a float between 0.0 and 1.0.
# Signals: skill_match, career_fit, experience_fit, availability,
#          location_fit, github, platform_demand, education, profile_quality

from datetime import date
import math
import re

TODAY = date.today()

# ── Skill name normalization ───────────────────────────────────────────────────
_SKILL_NORMALIZE_RE = re.compile(r'[^a-z0-9\s]')

def normalize_skill(name):
    """Lowercase, remove punctuation — sentence-transformers matches sentence transformers."""
    return _SKILL_NORMALIZE_RE.sub('', name.lower()).strip()

# ── JD-derived constants ───────────────────────────────────────────────────────
CORE_SKILLS_RAW = {
    "embeddings", "sentence transformers", "vector database", "faiss", "pinecone",
    "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch",
    "information retrieval", "semantic search", "hybrid search",
    "retrieval", "ranking", "recommendation", "nlp", "python",
    "machine learning", "transformers", "hugging face transformers",
    "huggingface", "bge", "e5", "openai embeddings", "dense retrieval",
    "ndcg", "mrr", "map", "learning to rank", "xgboost", "lightgbm",
}

BONUS_SKILLS_RAW = {
    "lora", "qlora", "peft", "fine-tuning llms", "fine tuning", "mlflow",
    "distributed systems", "kafka", "spark", "ab testing", "feature engineering",
    "mlops", "pytorch", "tensorflow", "scikit-learn",
}

CORE_SKILLS = {normalize_skill(s) for s in CORE_SKILLS_RAW}
BONUS_SKILLS = {normalize_skill(s) for s in BONUS_SKILLS_RAW}

DISQUALIFIER_TITLES = {
    "marketing manager", "hr manager", "operations manager", "accountant",
    "content writer", "sales", "customer support", "civil engineer",
    "mechanical engineer", "project manager", "business analyst",
    "finance", "graphic designer", "ui designer", "ux designer",
}

DISQUALIFIER_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "tech mahindra",
}

PREFERRED_LOCATIONS = {
    "pune", "noida", "hyderabad", "mumbai", "delhi", "gurugram",
    "gurgaon", "bengaluru", "bangalore", "chennai",
}

RELEVANT_FIELDS = {
    "computer science", "computer engineering", "information technology",
    "artificial intelligence", "machine learning", "data science",
    "electronics", "electrical engineering", "mathematics", "statistics"
}


# ── Signal 1: Skill Match ──────────────────────────────────────────────────────
def skill_match_score(candidate):
    """
    Score 0-1 based on how well skills match JD requirements.
    Weights: proficiency level + endorsements + duration + assessment score.
    Not just keyword presence — checks actual depth of each skill.
    """
    skills = candidate.get("skills", [])
    assessment_scores = candidate.get("redrob_signals", {}).get(
        "skill_assessment_scores", {}
    )

    if not skills:
        return 0.0

    core_hits = 0.0
    bonus_hits = 0.0

    for skill in skills:
        name = normalize_skill(skill["name"])
        proficiency = skill.get("proficiency", "beginner")
        endorsements = skill.get("endorsements", 0)
        duration = skill.get("duration_months", 0)

        prof_weight = {
            "beginner": 0.25, "intermediate": 0.50,
            "advanced": 0.75, "expert": 1.0
        }
        pw = prof_weight.get(proficiency, 0.25)
        ew = min(math.log1p(endorsements) / math.log1p(50), 1.0)
        dw = min(duration / 60.0, 1.0)

        aw = assessment_scores.get(skill["name"], -1)
        if aw >= 0:
            aw = aw / 100.0
        else:
            aw = pw

        strength = 0.35 * pw + 0.20 * ew + 0.20 * dw + 0.25 * aw

        if name in CORE_SKILLS:
            core_hits += strength
        elif name in BONUS_SKILLS:
            bonus_hits += strength * 0.4

    core_score = min(core_hits / 6.0, 1.0)
    bonus_score = min(bonus_hits / 3.0, 1.0)

    return round(0.80 * core_score + 0.20 * bonus_score, 4)


# ── Signal 2: Career Fit ───────────────────────────────────────────────────────
def career_fit_score(candidate):
    """
    Score 0-1 based on career trajectory.
    Rewards: product company experience, ML/AI/search titles, right seniority.
    Penalizes: pure consulting, wrong domain, title-hopping.
    """
    career = candidate.get("career_history", [])
    profile = candidate.get("profile", {})
    current_title = profile.get("current_title", "").lower()

    if not career:
        return 0.0

    score = 0.0

    for bad_title in DISQUALIFIER_TITLES:
        if bad_title in current_title:
            return 0.05

    all_consulting = all(
        any(dc in job.get("company", "").lower() for dc in DISQUALIFIER_COMPANIES)
        for job in career
    )
    if all_consulting and len(career) > 1:
        score -= 0.3

    good_title_keywords = {
        "ml", "machine learning", "ai", "nlp", "search", "ranking",
        "recommendation", "retrieval", "data scientist", "applied scientist",
        "research engineer", "applied ml", "applied ai"
    }
    title_score = 0.0
    for job in career:
        title = job.get("title", "").lower()
        if any(kw in title for kw in good_title_keywords):
            months = job.get("duration_months", 0)
            title_score += min(months / 24.0, 1.0)

    score += min(title_score / 3.0, 0.5)

    product_months = 0
    for job in career:
        company = job.get("company", "").lower()
        industry = job.get("industry", "").lower()
        is_consulting = any(dc in company for dc in DISQUALIFIER_COMPANIES)
        is_services = "it services" in industry or "consulting" in industry
        if not is_consulting and not is_services:
            product_months += job.get("duration_months", 0)

    score += min(product_months / 60.0, 0.4)

    if len(career) >= 4:
        total_months = sum(j.get("duration_months", 0) for j in career[:4])
        if total_months < 48:
            score -= 0.15

    return round(max(0.0, min(score, 1.0)), 4)


# ── Signal 3: Experience Fit ───────────────────────────────────────────────────
def experience_fit_score(candidate):
    """
    Score 0-1 based on years of experience.
    JD wants 5-9 years. Sweet spot is 6-8.
    """
    yoe = candidate.get("profile", {}).get("years_of_experience", 0)

    if yoe < 3:
        return 0.0
    elif yoe < 5:
        return 0.3
    elif 5 <= yoe <= 9:
        return 1.0 if 6 <= yoe <= 8 else 0.8
    elif yoe <= 12:
        return 0.5
    else:
        return 0.3


# ── Signal 4: Availability ─────────────────────────────────────────────────────
def availability_score(candidate):
    """
    Score 0-1 based on behavioral signals.
    Used as a MULTIPLIER — unreachable candidates get downweighted.
    Formula: Final Score = Base Score x (0.40 + 0.60 x availability)
    """
    signals = candidate.get("redrob_signals", {})
    score = 0.0

    if signals.get("open_to_work_flag", False):
        score += 0.25

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
        except Exception:
            pass

    rrr = signals.get("recruiter_response_rate", 0)
    score += 0.25 * rrr

    notice = signals.get("notice_period_days", 90)
    if notice <= 30:
        score += 0.15
    elif notice <= 60:
        score += 0.08

    if signals.get("verified_email", False):
        score += 0.05
    if signals.get("verified_phone", False):
        score += 0.05

    return round(min(score, 1.0), 4)


# ── Signal 5: Location Fit ─────────────────────────────────────────────────────
def location_fit_score(candidate):
    """
    Score 0-1 based on location and relocation willingness.
    JD says India only. Pune/Noida preferred.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    location = profile.get("location", "").lower()
    country = profile.get("country", "").lower()
    willing_to_relocate = signals.get("willing_to_relocate", False)

    if country != "india":
        return 0.2 if willing_to_relocate else 0.05

    for city in PREFERRED_LOCATIONS:
        if city in location:
            return 1.0

    return 0.6 if willing_to_relocate else 0.3


# ── Signal 6: GitHub ───────────────────────────────────────────────────────────
def github_score(candidate):
    """
    Score 0-1 from GitHub activity.
    JD calls open source contributions a strong positive signal.
    -1 means no GitHub linked — treated as neutral (0.3), not penalized.
    """
    signals = candidate.get("redrob_signals", {})
    gh = signals.get("github_activity_score", -1)
    if gh == -1:
        return 0.3
    return round(gh / 100.0, 4)


# ── Signal 7: Platform Demand ──────────────────────────────────────────────────
def platform_demand_score(candidate):
    """
    How much is the Redrob platform itself validating this candidate?

    saved_by_recruiters_30d: real recruiters actively saved this profile.
    This is crowd-sourced validation from actual hiring professionals.

    search_appearance_30d: how often this profile appears in recruiter searches.
    High appearance = the platform algorithm thinks they are relevant.

    profile_completeness: serious candidates fill their profiles completely.
    """
    signals = candidate.get("redrob_signals", {})

    saved = signals.get("saved_by_recruiters_30d", 0)
    appearances = signals.get("search_appearance_30d", 0)
    completeness = signals.get("profile_completeness_score", 0)

    saved_score = min(math.log1p(saved) / math.log1p(20), 1.0)
    appearance_score = min(appearances / 500.0, 1.0)
    completeness_score = completeness / 100.0

    return round(
        0.50 * saved_score +
        0.30 * appearance_score +
        0.20 * completeness_score,
        4
    )


# ── Signal 8: Education ────────────────────────────────────────────────────────
def education_score(candidate):
    """
    Score 0-1 based on education tier and field relevance.
    For a founding-team AI role, education quality is a differentiator.

    tier_1 = IITs, IISc, top global universities (1.0)
    tier_2 = NITs, good private universities (0.75)
    tier_3 = average colleges (0.50)
    tier_4 = unranked (0.25)
    """
    education = candidate.get("education", [])
    if not education:
        return 0.3

    tier_scores = {
        "tier_1": 1.0, "tier_2": 0.75,
        "tier_3": 0.50, "tier_4": 0.25, "unknown": 0.35
    }

    best_score = 0.0
    for edu in education:
        tier = edu.get("tier", "unknown")
        field = edu.get("field_of_study", "").lower()
        degree = edu.get("degree", "").lower()

        tier_val = tier_scores.get(tier, 0.35)

        field_bonus = 0.15 if any(f in field for f in RELEVANT_FIELDS) else 0.0

        degree_bonus = 0.0
        if any(d in degree for d in ["m.tech", "mtech", "m.e", "ms ", "m.s", "phd", "ph.d"]):
            degree_bonus = 0.10

        score = min(tier_val + field_bonus + degree_bonus, 1.0)
        best_score = max(best_score, score)

    return round(best_score, 4)


# ── Signal 9: Profile Quality ──────────────────────────────────────────────────
def profile_quality_score(candidate):
    """
    How engaged and credible is this candidate on the platform?

    connection_count: strong network = established in the industry.
    linkedin_connected: professional credibility signal.
    interview_completion_rate: shows they follow through on commitments.
    offer_acceptance_rate: shows they are serious about switching.
    """
    signals = candidate.get("redrob_signals", {})

    connections = signals.get("connection_count", 0)
    connection_score = min(math.log1p(connections) / math.log1p(500), 1.0)

    linkedin = 1.0 if signals.get("linkedin_connected", False) else 0.3

    icr = min(signals.get("interview_completion_rate", 0.5), 1.0)

    oar = signals.get("offer_acceptance_rate", -1)
    oar_score = oar if oar >= 0 else 0.5

    return round(
        0.30 * connection_score +
        0.25 * linkedin +
        0.25 * icr +
        0.20 * oar_score,
        4
    )


# ── Master function ────────────────────────────────────────────────────────────
def compute_all_features(candidate):
    """
    Returns a dict of all 9 feature scores for one candidate.
    availability is computed here but used as a multiplier in scorer.py,
    not as a direct weight.
    """
    return {
        "candidate_id":    candidate["candidate_id"],
        "skill_match":     skill_match_score(candidate),
        "career_fit":      career_fit_score(candidate),
        "experience_fit":  experience_fit_score(candidate),
        "availability":    availability_score(candidate),
        "location_fit":    location_fit_score(candidate),
        "github":          github_score(candidate),
        "platform_demand": platform_demand_score(candidate),
        "education":       education_score(candidate),
        "profile_quality": profile_quality_score(candidate),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
    from loader import load_candidates

    candidates = load_candidates("sample_candidates.json")
    print(f"\n{'ID':<15} {'Skill':>6} {'Career':>7} {'Exp':>5} {'Avail':>6} {'Loc':>5} {'GH':>5} {'Plat':>6} {'Edu':>5} {'Prof':>5}")
    print("-" * 80)
    for c in candidates[:10]:
        f = compute_all_features(c)
        print(
            f"{f['candidate_id']:<15} "
            f"{f['skill_match']:>6.3f} "
            f"{f['career_fit']:>7.3f} "
            f"{f['experience_fit']:>5.2f} "
            f"{f['availability']:>6.3f} "
            f"{f['location_fit']:>5.2f} "
            f"{f['github']:>5.3f} "
            f"{f['platform_demand']:>6.3f} "
            f"{f['education']:>5.3f} "
            f"{f['profile_quality']:>5.3f}"
        )