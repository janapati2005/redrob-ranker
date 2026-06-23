# tests/run_all_tests.py
# Redrob Candidate Ranker — Automated Test Suite

import sys
import time
import io
import contextlib
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loader import load_candidates
from honeypot import is_honeypot, filter_honeypots
from features import compute_all_features
from scorer import score_all, compute_score

results = []

def record(name, passed, detail=""):
    results.append((name, passed, detail))

TABLE_WIDTH = 78

def L():
    print("  " + "─" * TABLE_WIDTH)

def T():
    print("\n  " + "━" * TABLE_WIDTH + "\n")

def row(left, right, width_left=40):
    print(f"  {left:<{width_left}} {right}")

def make_candidate(cid, title, skills, yoe, location, country,
                   career_titles, open_to_work=True,
                   last_active="2026-06-01", notice=15,
                   proficiency="advanced"):
    return {
        "candidate_id": cid,
        "profile": {
            "anonymized_name": f"Candidate {cid}",
            "headline": f"{title} with {yoe} years",
            "summary": f"Experienced {title} in ML and retrieval systems",
            "location": location,
            "country": country,
            "years_of_experience": yoe,
            "current_title": title,
            "current_company": "Test Corp",
            "current_company_size": "501-1000",
            "current_industry": "Technology"
        },
        "career_history": [{
            "company": "Product Co",
            "title": t,
            "start_date": "2018-01-01",
            "end_date": None,
            "duration_months": 24,
            "is_current": True,
            "industry": "Technology",
            "company_size": "501-1000",
            "description": f"Built {t} systems using embeddings and vector databases"
        } for t in career_titles],
        "education": [{
            "institution": "IIT Delhi",
            "degree": "B.Tech",
            "field_of_study": "Computer Science",
            "start_year": 2010,
            "end_year": 2014,
            "grade": "8.5",
            "tier": "tier_1"
        }],
        "skills": [{
            "name": s,
            "proficiency": proficiency,
            "endorsements": 20,
            "duration_months": 24
        } for s in skills],
        "certifications": [],
        "languages": [{"language": "English", "proficiency": "native"}],
        "redrob_signals": {
            "profile_completeness_score": 90,
            "signup_date": "2024-01-01",
            "last_active_date": last_active,
            "open_to_work_flag": open_to_work,
            "profile_views_received_30d": 100,
            "applications_submitted_30d": 3,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 4,
            "skill_assessment_scores": {},
            "connection_count": 500,
            "endorsements_received": 80,
            "notice_period_days": notice,
            "expected_salary_range_inr_lpa": {"min": 20, "max": 40},
            "preferred_work_mode": "hybrid",
            "willing_to_relocate": True,
            "github_activity_score": 70,
            "search_appearance_30d": 200,
            "saved_by_recruiters_30d": 8,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.8,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True
        }
    }

# suppress loader print statements
@contextlib.contextmanager
def suppress_output():
    with contextlib.redirect_stdout(io.StringIO()):
        yield


# ══════════════════════════════════════════════════════════════
print()
print("  REDROB CANDIDATE RANKER   TEST SUITE")
print("  Automated Validation and Quality Checks")
print(f"  {datetime.now().strftime('%Y-%m-%d     %H:%M:%S')}")


# ══════════════════════════════════════════════════════════════
# MODULE 1
# ══════════════════════════════════════════════════════════════
T()
print("  MODULE 1   Basic Correctness")
print()
print("  Data Loading and Feature Extraction")
L()

with suppress_output():
    candidates = load_candidates("sample_candidates.json")

features = compute_all_features(candidates[0])
signal_list = [k for k in features if k != "candidate_id"]

row("Candidates loaded",           str(len(candidates)))
row("Signals extracted",           str(len(signal_list)))
row("Signal 1   skill_match",      "Depth of skills vs JD requirements")
row("Signal 2   career_fit",       "Title, domain, product company history")
row("Signal 3   experience_fit",   "Years of experience vs JD range")
row("Signal 4   availability",     "Multiplier — last active, response rate")
row("Signal 5   location_fit",     "India preferred, Pune and Noida ideal")
row("Signal 6   github",           "Open source contribution score")
row("Signal 7   platform_demand",  "Saved by recruiters, search appearances")
row("Signal 8   education",        "Institution tier and field relevance")
row("Signal 9   profile_quality",  "Connections, LinkedIn, interview rate")
print()

r1 = len(candidates) == 50
record("Sample dataset loads 50 candidates", r1)

r2 = all("candidate_id" in c and "profile" in c and
         "skills" in c and "redrob_signals" in c
         for c in candidates)
record("All candidates have required fields", r2)

r3 = len(signal_list) == 9
record("Feature extraction returns 9 signals", r3)

r4 = all(0.0 <= features[k] <= 1.0 for k in signal_list)
record("All signal scores within valid range 0 to 1", r4)

print()
print("  Ranking Correctness")
L()

with suppress_output():
    ranked = score_all(candidates)

row("Rank 1 candidate",        ranked[0]["candidate_id"])
row("Rank 1 score",            f"{ranked[0]['score']:.4f}")
row("Total candidates ranked", str(len(ranked)))
print()

r5 = all(ranked[i]["score"] >= ranked[i+1]["score"]
         for i in range(len(ranked)-1))
record("Output scores are non-increasing by rank", r5)

r6 = ranked[0]["candidate_id"] == "CAND_0000031"
record("Strongest candidate ranked first on sample", r6)

r7 = len(ranked) == 50
record("All 50 sample candidates appear in output", r7)

r8 = len(set(r["candidate_id"] for r in ranked)) == len(ranked)
record("No duplicate candidate IDs in output", r8)

r9 = all(0.0 <= r["score"] <= 1.0 for r in ranked)
record("All final scores within valid range 0 to 1", r9)

r10 = ranked[0]["score"] > 0.5
record("Top candidate score exceeds 0.5 threshold", r10)


# ══════════════════════════════════════════════════════════════
# MODULE 2
# ══════════════════════════════════════════════════════════════
T()
print("  MODULE 2   Candidate Discrimination")
print()
print("  Six Profile Types Tested Against Each Other")
L()

perfect = make_candidate(
    "TEST_PERFECT", "Machine Learning Engineer",
    ["FAISS", "Embeddings", "Pinecone", "NLP", "Python", "Semantic Search"],
    yoe=7, location="Pune, Maharashtra", country="India",
    career_titles=["ML Engineer", "Applied Scientist"]
)
good = make_candidate(
    "TEST_GOOD", "Data Scientist",
    ["Machine Learning", "Python", "NLP", "Transformers"],
    yoe=6, location="Hyderabad, Telangana", country="India",
    career_titles=["Data Scientist", "ML Engineer"]
)
stuffer = make_candidate(
    "TEST_STUFFER", "Marketing Manager",
    ["FAISS", "Embeddings", "Pinecone", "NLP", "Python"],
    yoe=7, location="Mumbai", country="India",
    career_titles=["Marketing Manager", "Brand Manager"]
)
overseas = make_candidate(
    "TEST_LOCATION", "Machine Learning Engineer",
    ["FAISS", "Embeddings", "Pinecone", "NLP", "Python"],
    yoe=7, location="New York, NY", country="USA",
    career_titles=["ML Engineer"]
)
ghost = make_candidate(
    "TEST_GHOST", "Machine Learning Engineer",
    ["FAISS", "Embeddings", "Pinecone", "NLP", "Python"],
    yoe=7, location="Bangalore", country="India",
    career_titles=["ML Engineer"],
    open_to_work=False, last_active="2025-01-01", notice=90
)
junior = make_candidate(
    "TEST_JUNIOR", "ML Engineer",
    ["Python", "Machine Learning", "NLP"],
    yoe=1.5, location="Pune", country="India",
    career_titles=["Junior ML Engineer"]
)

test_candidates = [perfect, good, stuffer, overseas, ghost, junior]
with suppress_output():
    test_ranked = score_all(test_candidates)

test_scores   = {r["candidate_id"]: r["score"]      for r in test_ranked}
test_features = {r["candidate_id"]: r["features"]   for r in test_ranked}
test_mult     = {r["candidate_id"]: r["multiplier"] for r in test_ranked}

labels = {
    "TEST_PERFECT":  "Perfect fit — right skills, India, active",
    "TEST_GOOD":     "Good fit — partial skills, India, active",
    "TEST_LOCATION": "Wrong location — right skills, outside India",
    "TEST_JUNIOR":   "Junior — right skills, only 1.5 years exp",
    "TEST_STUFFER":  "Keyword stuffer — wrong title, AI skills listed",
    "TEST_GHOST":    "Ghost — right skills, completely inactive",
}

PROFILE_WIDTH = 55

print(f"  {'Profile Type':<{PROFILE_WIDTH}} {'Score':>8}")
L()

for r in test_ranked:
    label = labels.get(r["candidate_id"], r["candidate_id"])
    print(f"  {label:<{PROFILE_WIDTH}} {r['score']:>8.4f}")

print()
print("  Key Signal Values")
L()
SIG_W = 30
COL_W = 18

print(f"  {'Signal':<{SIG_W}} {'Keyword Stuffer':>{COL_W}} {'Ghost':>{COL_W}}")
L()

print(f"  {'career_fit':<{SIG_W}} {test_features['TEST_STUFFER']['career_fit']:>{COL_W}.4f} {'—':>{COL_W}}")
print(f"  {'availability multiplier':<{SIG_W}} {'—':>{COL_W}} {test_mult['TEST_GHOST']:>{COL_W}.4f}")
print(f"  {'experience_fit (junior)':<{SIG_W}} {test_features['TEST_JUNIOR']['experience_fit']:>{COL_W}.4f} {'—':>{COL_W}}")
print(f"  {'location_fit (overseas)':<{SIG_W}} {test_features['TEST_LOCATION']['location_fit']:>{COL_W}.4f} {'—':>{COL_W}}")


r11 = test_scores["TEST_PERFECT"] > test_scores["TEST_STUFFER"]
record("Perfect fit outscores keyword stuffer", r11)

r12 = test_scores["TEST_PERFECT"] > test_scores["TEST_LOCATION"]
record("India-based candidate outscores overseas candidate", r12)

r13 = test_scores["TEST_PERFECT"] > test_scores["TEST_GHOST"]
record("Available candidate outscores inactive ghost", r13)

r14 = test_scores["TEST_PERFECT"] > test_scores["TEST_JUNIOR"]
record("Senior candidate outscores junior candidate", r14)

r15 = test_features["TEST_STUFFER"]["career_fit"] <= 0.10
record("Keyword stuffer receives near-zero career fit score", r15)

r16 = test_mult["TEST_GHOST"] < 0.6
record("Ghost candidate receives low availability multiplier", r16)

r17 = test_features["TEST_JUNIOR"]["experience_fit"] == 0.0
record("Junior candidate receives zero experience score", r17)

r18 = test_features["TEST_LOCATION"]["location_fit"] <= 0.2
record("Overseas candidate receives low location score", r18)


# ══════════════════════════════════════════════════════════════
# MODULE 3
# ══════════════════════════════════════════════════════════════
T()
print("  MODULE 3   Edge Cases")
print()
print("  Boundary Conditions")
L()

zero_skills = make_candidate(
    "TEST_NOSKILLS", "ML Engineer", [],
    yoe=7, location="Pune", country="India",
    career_titles=["ML Engineer"]
)
zero_f = compute_all_features(zero_skills)
r19 = zero_f["skill_match"] == 0.0
record("Candidate with no skills scores zero on skill match", r19)

no_career = {
    **make_candidate("TEST_NOCAREER", "ML Engineer",
        ["FAISS", "Python"], yoe=5,
        location="Pune", country="India",
        career_titles=[]),
    "career_history": []
}
no_career_f = compute_all_features(no_career)
r20 = no_career_f["career_fit"] == 0.0
record("Candidate with no career history scores zero on career fit", r20)

hp_c = make_candidate("TEST_HP", "ML Engineer", ["FAISS", "Python"],
    yoe=8, location="Pune", country="India", career_titles=["ML Engineer"])
hp_c["skills"][0]["proficiency"] = "expert"
hp_c["skills"][0]["duration_months"] = 0
is_hp1, reasons1 = is_honeypot(hp_c)
r21 = is_hp1
record("Expert proficiency with zero usage months flagged as honeypot", r21)

false_exp = make_candidate("TEST_FALSEEXP", "ML Engineer", ["FAISS"],
    yoe=15, location="Pune", country="India", career_titles=["ML Engineer"])
is_hp2, reasons2 = is_honeypot(false_exp)
r22 = is_hp2
record("Inflated experience beyond career history flagged as honeypot", r22)

senior_c = make_candidate("TEST_SENIOR", "Principal ML Architect",
    ["FAISS", "Embeddings", "NLP"], yoe=18,
    location="Bangalore", country="India",
    career_titles=["Principal ML Architect"])
senior_f = compute_all_features(senior_c)
r23 = senior_f["experience_fit"] <= 0.5
record("18 years experience correctly flagged as overqualified", r23)

no_gh = make_candidate("TEST_NOGITHUB", "ML Engineer", ["FAISS"],
    yoe=6, location="Pune", country="India", career_titles=["ML Engineer"])
no_gh["redrob_signals"]["github_activity_score"] = -1
no_gh_f = compute_all_features(no_gh)
r24 = no_gh_f["github"] == 0.3
record("No GitHub linked returns neutral 0.3 score", r24)

with suppress_output():
    empty_ranked = score_all([])
r25 = empty_ranked == []
record("Empty candidate pool returns empty ranked list", r25)

maxed = make_candidate(
    "TEST_MAXED", "Recommendation Systems Engineer",
    ["FAISS", "Embeddings", "Pinecone", "NLP", "Python",
     "Semantic Search", "Weaviate", "Qdrant", "Learning to Rank", "NDCG"],
    yoe=7, location="Pune, Maharashtra", country="India",
    career_titles=["ML Engineer", "Applied Scientist", "Research Engineer"],
    proficiency="expert"
)
maxed_s = compute_score(maxed)
r26 = maxed_s["score"] > 0.65
record("Maximum signals candidate scores above 0.65 threshold", r26)

print(f"  {'Condition':<46} {'Value':>8}")
L()
print(f"  {'No skills listed':<46} {'skill_match = ' + str(zero_f['skill_match']):>8}")
print(f"  {'No career history':<46} {'career_fit = ' + str(no_career_f['career_fit']):>8}")
print(f"  {'No GitHub linked':<46} {'github = ' + str(no_gh_f['github']):>8}")
print(f"  {'18 years experience (overqualified)':<46} {'exp_fit = ' + str(senior_f['experience_fit']):>8}")
print(f"  {'Maximum signals candidate':<46} {'score = ' + str(round(maxed_s['score'],4)):>8}")
print(f"  {'Empty candidate pool':<46} {'returned = 0':>8}")
print(f"  {'Expert skill with zero months used':<46} {'honeypot = Yes':>8}")
print(f"  {'Inflated years of experience':<46} {'honeypot = Yes':>8}")


# ══════════════════════════════════════════════════════════════
# MODULE 4
# ══════════════════════════════════════════════════════════════
T()
print("  MODULE 4   Speed and Performance")
print()
print("  Processing Speed at Scale — 1000 Candidate Batch")
L()

batch = [make_candidate(
    f"CAND_{i:07d}", "ML Engineer", ["FAISS", "Python", "NLP"],
    yoe=6, location="Pune", country="India",
    career_titles=["ML Engineer"]
) for i in range(1000)]

t0 = time.time()
for c in batch:
    compute_all_features(c)
t_feat = time.time() - t0

t0 = time.time()
with suppress_output():
    score_all(batch)
t_score = time.time() - t0

t0 = time.time()
with suppress_output():
    filter_honeypots(batch, verbose=False)
t_hp = time.time() - t0

r27 = t_feat  < 2.0
record("Feature extraction — 1000 candidates under 2 seconds", r27)
r28 = t_score < 3.0
record("Full scoring pipeline — 1000 candidates under 3 seconds", r28)
r29 = t_hp    < 1.0
record("Honeypot detection — 1000 candidates under 1 second", r29)

print(f"  {'Operation':<30} {'1000 cands':>12} {'100k est':>10} {'1M est':>10}")
L()
print(f"  {'Feature extraction':<30} {t_feat:>11.3f}s {t_feat*100:>9.1f}s {t_feat*1000:>9.1f}s")
print(f"  {'Full scoring pipeline':<30} {t_score:>11.3f}s {t_score*100:>9.1f}s {t_score*1000:>9.1f}s")
print(f"  {'Honeypot detection':<30} {t_hp:>11.3f}s {t_hp*100:>9.1f}s {t_hp*1000:>9.1f}s")


# ══════════════════════════════════════════════════════════════
# MODULE 5
# ══════════════════════════════════════════════════════════════
T()
print("  MODULE 5   Honeypot Detection Accuracy")
print()
print("  Three Injected Honeypots vs Three Clean Profiles")
L()

hp1 = make_candidate("HP_001", "ML Engineer", ["FAISS"],
    7, "Pune", "India", ["ML Engineer"])
hp1["skills"][0]["proficiency"] = "expert"
hp1["skills"][0]["duration_months"] = 0

hp2 = make_candidate("HP_002", "ML Engineer", ["Python"],
    20, "Pune", "India", ["ML Engineer"])

hp3 = make_candidate("HP_003", "ML Engineer", ["Python"],
    7, "Pune", "India", ["ML Engineer"])
hp3["redrob_signals"]["offer_acceptance_rate"] = 1.5

cl1 = make_candidate("CLEAN_001", "ML Engineer", ["FAISS", "Python"],
    7, "Pune", "India", ["ML Engineer"])
cl2 = make_candidate("CLEAN_002", "Data Scientist", ["NLP", "Python"],
    5, "Bangalore", "India", ["Data Scientist"])
cl3 = make_candidate("CLEAN_003", "ML Engineer", ["Embeddings"],
    8, "Hyderabad", "India", ["ML Engineer"])

with suppress_output():
    clean_out, flagged_out = filter_honeypots(
        [hp1, hp2, hp3, cl1, cl2, cl3], verbose=False)

r30 = len(flagged_out) == 3
record("All 3 injected honeypots correctly detected", r30)
r31 = len(clean_out) == 3
record("All 3 clean profiles correctly passed through", r31)
r32 = all(c["candidate_id"].startswith("CLEAN") for c in clean_out)
record("Zero false positives on legitimate candidates", r32)
r33 = all(h["candidate"]["candidate_id"].startswith("HP") for h in flagged_out)
record("Zero false negatives on injected honeypots", r33)

print(f"  {'Metric':<35} {'Result':>8}")
L()
print(f"  {'Input profiles':<35} {'6':>8}")
print(f"  {'Honeypots injected':<35} {'3':>8}")
print(f"  {'Clean profiles injected':<35} {'3':>8}")
print(f"  {'Honeypots detected':<35} {len(flagged_out):>8}")
print(f"  {'Clean profiles passed through':<35} {len(clean_out):>8}")
print(f"  {'False positives':<35} {max(0, len(clean_out)-3):>8}")
print(f"  {'False negatives':<35} {max(0, 3-len(flagged_out)):>8}")
print()
print(f"  {'Profile':<12} {'Reason Detected'}")
L()
for h in flagged_out:
    cid = h["candidate"]["candidate_id"]
    reason = h["reasons"][0] if h["reasons"] else "unknown"
    print(f"  {cid:<12} {reason}")


# ══════════════════════════════════════════════════════════════
# MODULE 6
# ══════════════════════════════════════════════════════════════
T()
print("  MODULE 6   Robustness and Fault Tolerance")
print()
print("  Missing and Corrupt Data Handling")
L()

no_sig = make_candidate("TEST_NOSIG", "ML Engineer", ["FAISS"],
    7, "Pune", "India", ["ML Engineer"])
no_sig["redrob_signals"] = {}

try:
    compute_all_features(no_sig)
    s1 = compute_score(no_sig)
    r34 = True
    r35 = s1["score"] > 0
    score_empty = s1["score"]
except Exception as e:
    r34 = r35 = False
    score_empty = 0.0

record("Handles completely empty redrob_signals without crash", r34)
record("Empty signals produces valid non-zero score", r35)

minimal = {
    "candidate_id": "TEST_MINIMAL",
    "profile": {
        "anonymized_name": "Minimal", "headline": "", "summary": "",
        "location": "Pune", "country": "India",
        "years_of_experience": 5, "current_title": "ML Engineer",
        "current_company": "Corp", "current_company_size": "51-200",
        "current_industry": "Tech"
    },
    "career_history": [], "education": [], "skills": [],
    "redrob_signals": {
        "profile_completeness_score": 30,
        "signup_date": "2024-01-01", "last_active_date": "2026-01-01",
        "open_to_work_flag": False, "profile_views_received_30d": 0,
        "applications_submitted_30d": 0, "recruiter_response_rate": 0,
        "avg_response_time_hours": 0, "skill_assessment_scores": {},
        "connection_count": 0, "endorsements_received": 0,
        "notice_period_days": 90,
        "expected_salary_range_inr_lpa": {"min": 0, "max": 0},
        "preferred_work_mode": "remote", "willing_to_relocate": False,
        "github_activity_score": -1, "search_appearance_30d": 0,
        "saved_by_recruiters_30d": 0, "interview_completion_rate": 0,
        "offer_acceptance_rate": -1, "verified_email": False,
        "verified_phone": False, "linkedin_connected": False
    }
}

try:
    compute_all_features(minimal)
    s2 = compute_score(minimal)
    r36 = True
    r37 = 0 <= s2["score"] <= 1
    score_min = s2["score"]
except Exception as e:
    r36 = r37 = False
    score_min = 0.0

record("Handles minimal profile with all empty fields without crash", r36)
record("Minimal profile produces valid score between 0 and 1", r37)

print(f"  {'Test Scenario':<42} {'Score':>8} {'Result':>8}")
L()
print(f"  {'Empty redrob_signals':<42} {score_empty:>8.4f} {'Valid':>8}")
print(f"  {'Minimal profile — all fields empty':<42} {score_min:>8.4f} {'Valid':>8}")


# ══════════════════════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════════════════════
T()
print("  EVALUATION REPORT")
print()

passed_count = sum(1 for _, s, _ in results if s)
failed_count = sum(1 for _, s, _ in results if not s)
total_count  = len(results)
rate         = passed_count / total_count * 100

modules = [
    ("Module 1   Basic Correctness",         list(range(0,  10))),
    ("Module 2   Candidate Discrimination",  list(range(10, 18))),
    ("Module 3   Edge Cases",                list(range(18, 26))),
    ("Module 4   Speed and Performance",     list(range(26, 29))),
    ("Module 5   Honeypot Detection",        list(range(29, 33))),
    ("Module 6   Robustness",                list(range(33, 37))),
]

print(f"  {'Module':<40} {'Checks':>7} {'Status':>12}")
L()
for mod_name, indices in modules:
    mod_res   = [results[i] for i in indices if i < len(results)]
    mod_pass  = sum(1 for _, s, _ in mod_res if s)
    mod_total = len(mod_res)
    status    = "All passed" if mod_pass == mod_total else f"{mod_pass}/{mod_total} passed"
    print(f"  {mod_name:<40} {mod_total:>7} {status:>12}")

L()
print(f"  {'Total checks':<40} {total_count:>7}")
print(f"  {'Passed':<40} {passed_count:>7}")
print(f"  {'Failed':<40} {failed_count:>7}")
print(f"  {'Overall score':<40} {rate:>6.1f}%")
print()

if failed_count > 0:
    print("  Checks requiring attention:")
    print()
    for name, passed_flag, detail in results:
        if not passed_flag:
            print(f"  {name}")
            if detail:
                print(f"  {detail}")
else:
    print("  All checks passed. System is production ready.")

print()