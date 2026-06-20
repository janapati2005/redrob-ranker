# loader.py
import json
import gzip
from pathlib import Path
from datetime import date

DATA_DIR = Path(__file__).parent.parent / "data"


def load_candidates(filename="sample_candidates.json"):
    filepath = DATA_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Cannot find {filepath}")

    suffix = filepath.suffix.lower()

    if suffix == ".json":
        with open(filepath, "r", encoding="utf-8") as f:
            candidates = json.load(f)

    elif suffix == ".gz":
        candidates = []
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    candidates.append(json.loads(line))

    elif suffix == ".jsonl":
        candidates = []
        with open(filepath, "rb") as f:
            raw = f.read()
        lines = raw.split(b'\n')
        for line in lines:
            line = line.strip()
            if line:
                candidates.append(json.loads(line))

    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    print(f"Loaded {len(candidates)} candidates from {filename}")
    return candidates


def validate_candidate(c):
    issues = []
    cid = c.get("candidate_id", "UNKNOWN")

    for key in ["candidate_id", "profile", "career_history", "skills", "redrob_signals"]:
        if key not in c:
            issues.append(f"{cid}: missing field '{key}'")

    if "profile" not in c:
        return issues

    p = c["profile"]
    yoe = p.get("years_of_experience", 0)
    career = c.get("career_history", [])

    if career:
        earliest = None
        for job in career:
            try:
                start = date.fromisoformat(job["start_date"])
                if earliest is None or start < earliest:
                    earliest = start
            except Exception:
                pass

        if earliest:
            today = date.today()
            actual_yoe = (today - earliest).days / 365.25
            if yoe > actual_yoe + 3:
                issues.append(
                    f"{cid}: claimed {yoe} yrs but career spans {actual_yoe:.1f} yrs"
                )

    for skill in c.get("skills", []):
        if skill.get("proficiency") == "expert" and skill.get("duration_months", 1) == 0:
            issues.append(f"{cid}: expert in '{skill['name']}' but 0 months")

    return issues


def load_and_validate(filename="sample_candidates.json"):
    candidates = load_candidates(filename)
    all_issues = []
    for c in candidates:
        issues = validate_candidate(c)
        all_issues.extend(issues)

    if all_issues:
        print(f"\nValidation found {len(all_issues)} issue(s):")
        for issue in all_issues[:20]:
            print(f"  {issue}")
    else:
        print("All candidates passed validation.")

    return candidates


if __name__ == "__main__":
    candidates = load_and_validate("sample_candidates.json")
    print(f"\nFirst candidate: {candidates[0]['candidate_id']} — {candidates[0]['profile']['current_title']}")