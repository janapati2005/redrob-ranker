# Redrob Candidate Ranker

**Team CrossSense** · Redrob Data and AI Hackathon 2026

An AI-powered hybrid pipeline that ranks 100,000 job candidates for a Senior AI Engineer role and returns the top 100 best fits in under 2 minutes on CPU, with zero GPU and zero network calls during ranking.

---

## The Problem

Recruiters go through hundreds of profiles and still miss the right person because keyword filters cannot see what actually matters. This system ranks candidates the way a great recruiter would — by understanding career trajectory, skill depth, semantic JD alignment, and behavioral availability — not just keyword presence.

---

## How It Works

```
100,000 candidates (.json / .jsonl / .jsonl.gz)
         |
         v
    loader.py          Reads all three file formats
         |
         v
    honeypot.py        Removes fake and impossible profiles (108 removed)
         |
         v
    bm25_retriever.py  Stage 1 — BM25 text retrieval, shortlists top 1500
         |
         v
    embedder.py        Stage 2 — Semantic scoring via sentence-transformers
         |
         v
    features.py        Extracts 9 signals per candidate
         |
         v
    scorer.py          Combines signals into final score with availability multiplier
         |
         v
    reasoner.py        Generates per-candidate reasoning text
         |
         v
    rank.py            Main entry point, outputs submission.csv
         |
         v
    Top 100 candidates saved to output/submission.csv
```

---

## Scoring Formula

```
Base Score  =  (skill_match x 0.27) + (career_fit x 0.24) + (semantic x 0.15)
            +  (experience_fit x 0.10) + (location_fit x 0.08)
            +  (platform_demand x 0.06) + (github x 0.05)
            +  (education x 0.03) + (profile_quality x 0.02)

Multiplier  =  0.40 + (0.60 x availability_score)

Final Score =  Base Score x Multiplier
```

Availability is a multiplier and not a direct weight because a candidate who never responds has zero hiring value regardless of technical fit. The 0.40 floor means inactive candidates are not completely zeroed out.

---

## Signal Breakdown

| Signal | Weight | What It Measures |
|--------|--------|-----------------|
| Skill Match | 27% | Proficiency level, endorsements, usage duration, platform assessment scores |
| Career Fit | 24% | Job titles, product company experience, domain alignment, consulting penalty |
| Semantic Similarity | 15% | Sentence-transformer cosine similarity between candidate profile and JD |
| Experience Fit | 10% | Years of experience vs JD requirement of 5 to 9 years, sweet spot 6 to 8 |
| Location Fit | 8% | India preferred, Pune and Noida ideal, Hyderabad and Bangalore also accepted |
| Platform Demand | 6% | Recruiter saves, search appearances, profile completeness score |
| GitHub Activity | 5% | Open source contribution score from the Redrob platform |
| Education | 3% | Institution tier (IIT/NIT/etc.) and field of study relevance |
| Profile Quality | 2% | Connection count, LinkedIn linked, interview and offer acceptance rates |
| Availability | Multiplier | Last active date, recruiter response rate, notice period, open to work flag |

---

## Why These Weights

| Signal | Reason |
|--------|--------|
| Skill 27% | JD names exact tools: FAISS, Pinecone, Weaviate, sentence-transformers, NDCG. Technical fit is the primary gate. |
| Career 24% | JD explicitly warns against keyword stuffers and consulting-only backgrounds. Career fit is the trap-killer. |
| Semantic 15% | Captures meaning-level alignment — "Information Retrieval Engineer" and "Search Systems Engineer" are the same even without shared keywords. |
| Experience 10% | Years matter but what you did in those years matters more. |
| Location 8% | Important but solvable. A great candidate willing to relocate still qualifies. |
| Platform Demand 6% | Crowd-sourced recruiter validation — real hiring professionals already saved these profiles. |
| GitHub 5% | JD calls it a strong positive signal, not a hard requirement. |
| Education 3% | IIT/IISc tier-1 education is a differentiator for a founding-team AI role. |
| Profile Quality 2% | Engagement and platform credibility. Tie-breaker level signal. |

---

## Honeypot Detection

The dataset contains ~108 fake profiles. We detect and remove them before scoring.

| Check | What It Catches |
|-------|----------------|
| Expert skill with 0 months usage | Impossible — you cannot be expert in something you never used |
| Claimed experience > 3 years beyond career history | Mathematically impossible |
| Signal values out of valid range | Acceptance rate > 1.0, completion rate > 1.0, profile score > 100 |
| Implausible tenure | 20+ years at a company started after 1990 |

Result: 108 honeypots removed, zero honeypots in top 100.

---

## Performance

| Metric | Result | Requirement |
|--------|--------|-------------|
| Candidates processed | 100,000 | 100,000 |
| Honeypots removed | 108 | ~80 expected |
| Runtime | 90–120 seconds (CPU, varies by machine) | Under 5 minutes |
| GPU used | None | CPU only |
| Network calls during ranking | None | Not allowed |
| Memory usage | Under 4 GB RAM | Under 16 GB |
| Test suite | 37/37 passing | Must pass |

---

## Top 10 Results on Full 100k Dataset

| Rank | Candidate ID | Score | Title |
|------|-------------|-------|-------|
| 1 | CAND_0000031 | 0.7780 | Recommendation Systems Engineer @ Swiggy |
| 2 | CAND_0036184 | 0.7646 | Recommendation Systems Engineer |
| 3 | CAND_0046525 | 0.7466 | Senior ML Engineer |
| 4 | CAND_0011687 | 0.6909 | Senior NLP Engineer |
| 5 | CAND_0062247 | 0.6803 | AI Engineer @ Pinecone |
| 6 | CAND_0017960 | 0.6789 | Recommendation Systems Engineer |
| 7 | CAND_0014440 | 0.6616 | Recommendation Systems Engineer |
| 8 | CAND_0064326 | 0.6611 | Search Engineer |
| 9 | CAND_0046064 | 0.6535 | Senior NLP Engineer |
| 10 | CAND_0041669 | 0.6532 | Recommendation Systems Engineer |

All top 10 are Recommendation Systems Engineers, Senior ML/NLP Engineers, or Search Engineers — exactly what the JD requires. Zero keyword stuffers. Zero wrong-domain candidates.

---

## Setup

```bash
git clone https://github.com/janapati2005/redrob-ranker
cd redrob-ranker
pip install -r requirements.txt
```

Place `candidates.jsonl` in the `data/` folder (not included — 475 MB).

---

## Usage

Run on full dataset:
```bash
python src/rank.py --candidates candidates.jsonl --top 100
```

Run on sample (50 candidates):
```bash
python src/rank.py
```

Skip semantic embeddings (faster baseline):
```bash
python src/rank.py --no-semantic
```

Validate output:
```bash
python validate_submission.py output/submission.csv
```

Run test suite:
```bash
python tests/run_all_tests.py
```

Run sandbox locally:
```bash
streamlit run app.py
```

---

## Project Structure

```
redrob-ranker/
├── data/
│   └── sample_candidates.json      50-candidate test file
├── src/
│   ├── loader.py                   Reads .json, .jsonl, .jsonl.gz
│   ├── honeypot.py                 Fake profile detection
│   ├── bm25_retriever.py           Stage 1 — BM25 text retrieval
│   ├── embedder.py                 Stage 2 — Semantic scoring
│   ├── features.py                 9-signal feature extraction
│   ├── scorer.py                   Weighted scoring + availability multiplier
│   ├── reasoner.py                 Per-candidate reasoning text
│   └── rank.py                     Main pipeline entry point
├── tests/
│   └── run_all_tests.py            37-check test suite
├── output/
│   └── submission.csv              100 ranked candidates
├── .streamlit/
│   └── config.toml                 Upload limit config
├── app.py                          Streamlit sandbox
├── requirements.txt                Python dependencies
├── packages.txt                    System dependencies for Streamlit Cloud
├── submission_metadata.yaml        Team info and approach summary
├── validate_submission.py          Competition format validator
└── README.md                       This file
```

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11 | Core pipeline |
| sentence-transformers | 3.0.1 | Semantic embeddings |
| scikit-learn | 1.5.0 | Cosine similarity |
| numpy | 1.26.4 | Numerical operations |
| pandas | 2.2.2 | Data handling |
| streamlit | 1.58.0 | Web sandbox |
| rank-bm25 | 0.2.2 | BM25 text retrieval |

---

## Live Sandbox

https://redrob-ranker-hg7bjpsw4c6dzf6wixkbg8.streamlit.app

Upload `sample_candidates.json` to see the full pipeline in action.

---

## Team

| Name | Role | Email |
|------|------|-------|
| Hari Aditya Janapati | Team Lead | jhariaditya@gmail.com |
| Vurinindi Navadeep Kumar Reddy | ML Engineer | navadeepv2005@gmail.com |

GitHub: https://github.com/janapati2005/redrob-ranker

AI tools declared: Claude was used for architecture discussion and code review. No candidate data was fed to any LLM during ranking. All scoring is done locally with no API calls.