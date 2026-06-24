# honeypot.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import date
# ... rest stays exactly the same

TODAY = date.today()

# Known fictional companies in the dataset (used as honeypot signals)
FICTIONAL_COMPANIES = {
    "dunder mifflin", "pied piper", "hooli", "acme corp",
    "globex inc", "stark industries", "wayne enterprises",
    "umbrella corp", "initech", "vandelay industries"
}


def check_experience_vs_career(candidate):
    """
    Claimed years_of_experience must roughly match career history length.
    If someone claims 8 years but their earliest job was 3 years ago — honeypot.
    """
    profile = candidate.get("profile", {})
    claimed_yoe = profile.get("years_of_experience", 0)
    career = candidate.get("career_history", [])

    if not career:
        return None

    earliest = None
    for job in career:
        try:
            start = date.fromisoformat(job["start_date"])
            if earliest is None or start < earliest:
                earliest = start
        except Exception:
            continue

    if earliest is None:
        return None

    actual_yoe = (TODAY - earliest).days / 365.25

    # Allow 3 year buffer (gaps, education, unlisted early jobs)
    if claimed_yoe > actual_yoe + 3:
        return (
            f"Claims {claimed_yoe:.1f} yrs experience but "
            f"career history only spans {actual_yoe:.1f} yrs"
        )
    return None


def check_skill_impossibilities(candidate):
    """
    Expert proficiency with 0 months usage is impossible.
    Also catches: more expert skills than years of experience allows.
    """
    skills = candidate.get("skills", [])
    issues = []

    expert_skills = []
    for skill in skills:
        name = skill.get("name", "")
        prof = skill.get("proficiency", "")
        duration = skill.get("duration_months", 0)

        if prof == "expert" and duration == 0:
            issues.append(f"Expert in '{name}' but 0 months used")

        if prof == "expert":
            expert_skills.append((name, duration))

    # Too many expert skills is suspicious
    if len(expert_skills) > 7:
        issues.append(
            f"{len(expert_skills)} expert-level skills — "
            f"statistically improbable"
        )

    return issues if issues else None


def check_tenure_vs_founding(candidate):
    """
    Duration at a company cannot exceed the company's plausible age.
    We catch this via: if someone spent >15 years at a company
    that appears in career history starting after 2010, flag it.
    This is a heuristic — we can't look up every company's founding date.
    """
    career = candidate.get("career_history", [])
    issues = []

    for job in career:
        duration = job.get("duration_months", 0)
        try:
            start = date.fromisoformat(job["start_date"])
        except Exception:
            continue

        # If they claim to have started before 1990 at a modern-sounding company
        if start.year < 1990 and duration > 240:  # 20+ years
            issues.append(
                f"Implausible tenure: {duration} months at "
                f"'{job.get('company', '?')}' starting {start.year}"
            )

    return issues if issues else None


def check_fictional_company(candidate):
    """
    Some honeypots use fictional company names from TV shows / movies.
    These are a strong signal of a synthetic/fake profile.
    """
    career = candidate.get("career_history", [])
    fictional_found = []

    for job in career:
        company = job.get("company", "").lower().strip()
        if company in FICTIONAL_COMPANIES:
            fictional_found.append(job.get("company", ""))

    # Note: fictional companies exist in the real sample data too —
    # the dataset uses them as stand-ins. We flag but don't hard-disqualify
    # on this alone since even real candidates may work at "Dunder Mifflin".
    return fictional_found if fictional_found else None


def check_signal_inconsistencies(candidate):
    """
    Checks for out-of-range signal values only.
    Signup/active date check removed — synthetic data has too much noise here.
    """
    signals = candidate.get("redrob_signals", {})
    issues = []

    # offer_acceptance_rate > 1.0 (out of range)
    oar = signals.get("offer_acceptance_rate", -1)
    if oar > 1.0:
        issues.append(f"offer_acceptance_rate={oar} exceeds maximum of 1.0")

    # interview_completion_rate > 1.0
    icr = signals.get("interview_completion_rate", 0)
    if icr > 1.0:
        issues.append(f"interview_completion_rate={icr} exceeds maximum of 1.0")

    # profile_completeness > 100
    pcs = signals.get("profile_completeness_score", 0)
    if pcs > 100:
        issues.append(f"profile_completeness_score={pcs} exceeds maximum of 100")

    return issues if issues else None


def is_honeypot(candidate):
    """
    Master honeypot check. Returns (is_honeypot: bool, reasons: list).
    Only hard, mathematically impossible flags qualify for removal.
    Fictional company is NOT used — dataset uses fictional names for real candidates too.
    """
    hard_flags = []

    exp_issue = check_experience_vs_career(candidate)
    if exp_issue:
        hard_flags.append(exp_issue)

    skill_issues = check_skill_impossibilities(candidate)
    if skill_issues:
        hard_flags.extend(skill_issues)

    signal_issues = check_signal_inconsistencies(candidate)
    if signal_issues:
        hard_flags.extend(signal_issues)

    tenure_issues = check_tenure_vs_founding(candidate)
    if tenure_issues:
        hard_flags.extend(tenure_issues)

    is_hp = len(hard_flags) > 0
    return is_hp, hard_flags

def filter_honeypots(candidates, verbose=True):
    """
    Runs honeypot detection on all candidates.
    Returns (clean_candidates, honeypot_candidates).
    """
    clean = []
    honeypots = []

    for c in candidates:
        is_hp, reasons = is_honeypot(c)
        if is_hp:
            honeypots.append({
                "candidate": c,
                "reasons": reasons
            })
        else:
            clean.append(c)

    if verbose:
        print(f"\nHoneypot detection complete:")
        print(f"  Clean candidates : {len(clean)}")
        print(f"  Honeypots flagged: {len(honeypots)}")
        if honeypots:
            print(f"\n  Flagged candidates:")
            for h in honeypots:
                cid = h["candidate"]["candidate_id"]
                print(f"    {cid}:")
                for r in h["reasons"]:
                    print(f"      - {r}")

    return clean, honeypots


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from loader import load_candidates

    candidates = load_candidates("sample_candidates.json")
    clean, honeypots = filter_honeypots(candidates, verbose=True)
    print(f"\n{len(clean)} candidates cleared for ranking.")