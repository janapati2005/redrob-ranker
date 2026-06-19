import json
import gzip
from pathlib import Path
from datetime import date

DATA_DIR = Path(__file__).parent.parent / "data"

def load_candidates(filename="sample_candidates.json"):
    """
    Loads candidates from either:
    - sample_candidates.json (for development)
    - candidates.jsonl or candidates.jsonl.gz (for full run)
    """
    filepath = DATA_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Cannot find {filepath}")

    suffix = filepath.suffix.lower()

    # Plain JSON array (sample file)
    if suffix == ".json":
        with open(filepath, "r", encoding="utf-8") as f:
            candidates = json.load(f)

    # Gzipped JSONL (full 100k file)
    elif suffix == ".gz":
        candidates = []
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    candidates.append(json.loads(line))

    # Plain JSONL
    elif suffix == ".jsonl":
        candidates = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    candidates.append(json.loads(line))

    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    print(f"Loaded {len(candidates)} candidates from {filename}")
    return candidates


def validate_candidate(c):
    """
    Basic sanity checks on a single candidate record.
    Returns a list of issues found (empty list = clean).
    """
    issues = []
    cid = c.get("candidate_id", "UNKNOWN")

    # Required top-level keys
    for key in ["candidate_id", "profile", "career_history", "skills", "redrob_signals"]:
        if key not in c:
            issues.append(f"{cid}: missing field '{key}'")

    if "profile" not in c:
        return issues  # can't go deeper

    p = c["profile"]
    yoe = p.get("years_of_experience", 0)

    # Honeypot check 1: experience predating career history
    career = c.get("career_history", [])
    if career:
        earliest_start = None
        for job in career:
            try:
                start = date.fromisoformat(job["start_date"])
                if earliest_start is None or start < earliest_start:
                    earliest_start = start
            except Exception:
                pass

        if earliest_start:
            today = date.today()
            actual_yoe = (today - earliest_start).days / 365.25
            if yoe > actual_yoe + 3:
                issues.append(
                    f"{cid}: claimed {yoe} yrs experience but career history "
                    f"only goes back {actual_yoe:.1f} yrs [HONEYPOT FLAG]"
                )

    # Honeypot check 2: expert skill with 0 months duration
    for skill in c.get("skills", []):
        if skill.get("proficiency") == "expert" and skill.get("duration_months", 1) == 0:
            issues.append(
                f"{cid}: expert proficiency in '{skill['name']}' but 0 months used [HONEYPOT FLAG]"
            )

    # Honeypot check 3: too many expert skills (>6 is suspicious)
    expert_count = sum(1 for s in c.get("skills", []) if s.get("proficiency") == "expert")
    if expert_count > 6:
        issues.append(f"{cid}: {expert_count} expert-level skills [HONEYPOT FLAG]")

    return issues


def load_and_validate(filename="sample_candidates.json"):
    """
    Load candidates and run validation on all of them.
    Prints a summary of any issues found.
    """
    candidates = load_candidates(filename)

    all_issues = []
    for c in candidates:
        issues = validate_candidate(c)
        all_issues.extend(issues)

    if all_issues:
        print(f"\nValidation found {len(all_issues)} issue(s):")
        for issue in all_issues[:20]:  # show first 20
            print(f"  {issue}")
        if len(all_issues) > 20:
            print(f"  ... and {len(all_issues) - 20} more")
    else:
        print("All candidates passed validation.")

    return candidates


if __name__ == "__main__":
    candidates = load_and_validate("sample_candidates.json")
    print(f"\nFirst candidate: {candidates[0]['candidate_id']} — {candidates[0]['profile']['current_title']}")