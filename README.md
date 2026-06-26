# Redrob Candidate Ranker

**Team CrossSense** · Redrob Data and AI Hackathon 2026

An AI-powered hybrid pipeline that ranks 100,000 job candidates for a Senior AI Engineer role and returns the top 100 best fits in under 2 minutes on CPU — zero GPU, zero network calls during ranking.

---

## The Problem

Recruiters go through hundreds of profiles and still miss the right person because keyword filters cannot see what actually matters. This system ranks candidates the way a great recruiter would — by understanding career trajectory, skill depth, semantic JD alignment, and behavioral availability — not just keyword presence.

---

## Live Sandbox

**https://redrob-ranker-hg7bjpsw4c6dzf6wixkbg8.streamlit.app**

Upload `sample_candidates.json` from the hackathon bundle to see the full 9-signal pipeline with real semantic scores.

---

## How It Works

```
100,000 candidates (.json / .jsonl / .jsonl.gz)
         │
         ▼
    loader.py             Reads all three file formats
         │
         ▼
    honeypot.py           Removes 108 fake and impossible profiles
         │
         ▼
    bm25_retriever.py     Stage 1 — BM25 shortlists top 1500 from 99,892
         │
         ▼
    embedder.py           Stage 2 — Semantic scoring via sentence-transformers
         │
         ▼
    features.py           Extracts 9 signals per candidate
         │
         ▼
    scorer.py             Weighted score + availability multiplier
         │
         ▼
    reasoner.py           Per-candidate reasoning text
         │
         ▼
    rank.py               Main entry point → output/submission.csv
```

---

## Scoring Formula

```
Base Score  =  (skill_match × 0.27) + (career_fit × 0.24) + (semantic × 0.15)
            +  (experience_fit × 0.10) + (location_fit × 0.08)
            +  (platform_demand × 0.06) + (github × 0.05)
            +  (education × 0.03) + (profile_quality × 0.02)

Multiplier  =  0.40 + (0.60 × availability_score)

Final Score =  Base Score × Multiplier
```

Availability is a **multiplier**, not a weight, because a candidate who never responds has zero hiring value regardless of technical fit. The 0.40 floor means inactive candidates are never completely zeroed out.

---

## Signal Breakdown

| Signal | Weight | What It Measures |
|--------|--------|-----------------|
| Skill Match | 27% | Proficiency level, endorsements, usage duration, platform assessment scores |
| Career Fit | 24% | Job titles, product company experience, domain alignment, consulting penalty |
| Semantic Similarity | 15% | all-MiniLM-L6-v2 cosine similarity between candidate profile and JD |
| Experience Fit | 10% | Years of experience vs JD requirement of 5–9 years, sweet spot 6–8 |
| Location Fit | 8% | India preferred, Pune and Noida ideal, Hyderabad and Bangalore accepted |
| Platform Demand | 6% | Recruiter saves, search appearances, profile completeness score |
| GitHub Activity | 5% | Open source contribution score from the Redrob platform |
| Education | 3% | Institution tier (IIT/NIT/etc.) and field of study relevance |
| Profile Quality | 2% | Connection count, LinkedIn linked, interview and offer acceptance rates |
| Availability | × multiplier | Last active date, recruiter response rate, notice period, open to work flag |

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

The dataset contains 108 fake profiles. We detect and remove all of them before scoring.

| Check | What It Catches |
|-------|----------------|
| Expert skill with 0 months usage | Impossible — you cannot be expert in something you never used |
| Claimed experience > 3 years beyond career history | Mathematically impossible |
| Signal values out of valid range | Acceptance rate > 1.0, completion rate > 1.0, profile score > 100 |
| Implausible tenure | 20+ years at a company starting after 1990 |

**Result: 108 honeypots removed. Zero honeypots in top 100.**

---

## Top 10 Results on Full 100k Dataset

| Rank | Candidate ID | Score | Semantic | Title |
|------|-------------|-------|----------|-------|
| 1 | CAND_0000031 | 0.7780 | 0.910 | Recommendation Systems Engineer @ Swiggy |
| 2 | CAND_0036184 | 0.7646 | 0.904 | Recommendation Systems Engineer |
| 3 | CAND_0046525 | 0.7466 | 0.821 | Senior ML Engineer |
| 4 | CAND_0011687 | 0.6909 | 0.706 | Senior NLP Engineer |
| 5 | CAND_0062247 | 0.6803 | 0.918 | AI Engineer @ Pinecone |
| 6 | CAND_0017960 | 0.6789 | 0.813 | Recommendation Systems Engineer |
| 7 | CAND_0014440 | 0.6616 | 0.735 | Recommendation Systems Engineer |
| 8 | CAND_0064326 | 0.6611 | 0.732 | Search Engineer |
| 9 | CAND_0046064 | 0.6535 | 0.800 | Senior NLP Engineer |
| 10 | CAND_0041669 | 0.6532 | 0.684 | Recommendation Systems Engineer |

All top 10 are Recommendation Systems Engineers, Senior ML/NLP Engineers, or Search Engineers — exactly what the JD requires. Zero keyword stuffers. Zero wrong-domain candidates.

---

## Performance

| Metric | Result | Requirement |
|--------|--------|-------------|
| Candidates processed | 100,000 | 100,000 |
| Honeypots removed | 108 | — |
| Runtime | 105 seconds on CPU | Under 5 minutes |
| GPU used | None | CPU only |
| Network calls during ranking | None | Not allowed |
| Memory usage | Under 4 GB RAM | — |
| Test suite | 37/37 passing | — |

---

## Setup

```bash
git clone https://github.com/janapati2005/redrob-ranker
cd redrob-ranker
pip install sentence-transformers scikit-learn numpy pandas tqdm rank-bm25 streamlit
```

Place `candidates.jsonl` in the `data/` folder (not included in repo — 475 MB).

---

## Usage

**Run on full 100k dataset:**
```bash
python src/rank.py --candidates candidates.jsonl --top 100
```

**Run on sample (50 candidates):**
```bash
python src/rank.py
```

**Skip semantic embeddings (faster baseline):**
```bash
python src/rank.py --no-semantic
```

**Regenerate semantic scores for sandbox:**
```bash
python src/precompute_semantics.py
```

**Validate output CSV:**
```bash
python validate_submission.py output/submission.csv
```

**Run test suite:**
```bash
python tests/run_all_tests.py
```

**Run sandbox locally:**
```bash
streamlit run app.py
```

---

## Project Structure

```
redrob-ranker/
├── data/
│   ├── sample_candidates.json        50-candidate test file
│   └── semantic_scores.json          Precomputed semantic scores (committed)
├── src/
│   ├── loader.py                     Reads .json, .jsonl, .jsonl.gz
│   ├── honeypot.py                   Fake profile detection
│   ├── bm25_retriever.py             Stage 1 — BM25 text retrieval
│   ├── embedder.py                   Stage 2 — Semantic scoring
│   ├── features.py                   9-signal feature extraction
│   ├── scorer.py                     Weighted scoring + availability multiplier
│   ├── reasoner.py                   Per-candidate reasoning text
│   ├── rank.py                       Main pipeline entry point
│   └── precompute_semantics.py       Generates semantic_scores.json
├── tests/
│   └── run_all_tests.py              37-check automated test suite
├── output/
│   └── submission.csv                Top 100 ranked candidates
├── .streamlit/
│   └── config.toml                   Upload size config
├── app.py                            Streamlit live sandbox
├── requirements.txt                  Cloud dependencies
├── packages.txt                      System dependencies for Streamlit Cloud
├── submission_metadata.yaml          Team info and methodology summary
├── validate_submission.py            Competition format validator
└── README.md                         This file
```

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11 | Core pipeline |
| sentence-transformers | 3.0.1 | Semantic JD embeddings (all-MiniLM-L6-v2) |
| scikit-learn | latest | Cosine similarity |
| numpy | latest | Numerical operations |
| pandas | latest | Data handling |
| rank-bm25 | 0.2.2 | Stage 1 BM25 text retrieval |
| streamlit | latest | Live sandbox |

---

## Team

| Name | Role | Email |
|------|------|-------|
| Hari Aditya Janapati | Team Lead | jhariaditya@gmail.com |
| Vurinindi Navadeep Kumar Reddy | ML Engineer | navadeepv2005@gmail.com |

**GitHub:** https://github.com/janapati2005/redrob-ranker

**AI tools declared:** Claude was used for architecture discussion and code review. No candidate data was fed to any LLM during ranking. All scoring is done locally with no API calls.