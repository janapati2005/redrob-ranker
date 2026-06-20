# Redrob Candidate Ranker

**Team CrossSense** · Redrob Data and AI Hackathon 2026

An AI-powered pipeline that ranks 100,000 job candidates for a Senior AI Engineer role and returns the top 100 best fits in under 15 seconds on CPU, with zero GPU and zero network calls during ranking.

---

## The Problem

Recruiters go through hundreds of profiles and still miss the right person because keyword filters cannot see what actually matters. This system ranks candidates the way a great recruiter would — by understanding career trajectory, skill depth, behavioral availability, and domain fit — not just keyword presence.

---

## How It Works

```
100,000 candidates (475 MB)
         |
         v
    loader.py        Reads .json / .jsonl / .jsonl.gz files
         |
         v
    honeypot.py      Removes fake and impossible profiles (108 removed)
         |
         v
    features.py      Scores each candidate on 6 signals
         |
         v
    scorer.py        Combines signals into one final score, ranks all
         |
         v
    reasoner.py      Writes specific per-candidate reasoning
         |
         v
    rank.py          Main entry point, outputs submission.csv
         |
         v
    Top 100 candidates saved to submission.csv
```

---

## Scoring Formula

```
Base Score  =  (skill x 0.35) + (career x 0.30) + (experience x 0.15)
            +  (location x 0.10) + (github x 0.10)

Multiplier  =  0.40 + (0.60 x availability_score)

Final Score =  Base Score x Multiplier
```

Availability is applied as a multiplier and not as a feature weight because a candidate who never responds to recruiters has zero hiring value regardless of technical fit. The floor of 0.40 means even inactive candidates are not completely zeroed out.

---

## Signal Breakdown

| Signal | Weight | What It Measures |
|--------|--------|-----------------|
| Skill Match | 35% | Proficiency level, endorsements, usage duration, platform assessment scores |
| Career Trajectory | 30% | Job titles, product company experience, domain alignment, consulting penalty |
| Experience Fit | 15% | Years of experience vs JD requirement of 5 to 9 years, sweet spot 6 to 8 |
| Location Fit | 10% | India preferred, Pune and Noida ideal, Hyderabad and Bangalore also accepted |
| GitHub Activity | 10% | Open source contribution score from the Redrob platform |
| Availability | Multiplier | Last active date, recruiter response rate, notice period, open to work flag |

---

## Why These Weights

| Signal | Reason |
|--------|--------|
| Skill 35% | The JD names exact tools: FAISS, Pinecone, Weaviate, sentence-transformers, NDCG. Technical fit is the primary gate. |
| Career 30% | The JD explicitly warns against keyword stuffers and consulting-only backgrounds. Career fit is the trap-killer. |
| Experience 15% | Years matter but what you did in those years matters more. Secondary to actual work done. |
| Location 10% | Important but solvable. A great candidate willing to relocate from Bangalore to Pune still qualifies. |
| GitHub 10% | The JD calls it a strong positive signal, not a hard requirement. Bonus, not a dealbreaker. |

---

## Honeypot Detection

The dataset contains approximately 80 fake profiles designed to fool naive rankers. We detect and remove them before scoring.

| Check | What It Catches |
|-------|----------------|
| Expert skill with 0 months usage | Impossible — you cannot be an expert in something you never used |
| Claimed experience more than 3 years beyond career history | Mathematically impossible |
| Signal values out of valid range | Acceptance rate above 1.0, completion rate above 1.0, profile score above 100 |

Result: 108 honeypots removed, zero honeypots in top 100, well within the 10 percent disqualification limit.

---

## Performance

| Metric | Our Result | Competition Requirement |
|--------|-----------|------------------------|
| Candidates processed | 100,000 | 100,000 |
| Honeypots removed | 108 | Around 80 expected |
| Runtime | 13 seconds | Under 5 minutes |
| GPU used | None | CPU only |
| Network calls during ranking | None | Not allowed |
| Memory usage | Under 4 GB RAM | Under 16 GB |
| Validator result | Submission is valid | Must pass |

---

## Top 10 Results on Full 100k Dataset

| Rank | Candidate ID | Score | Title |
|------|-------------|-------|-------|
| 1 | CAND_0000031 | 0.7580 | Recommendation Systems Engineer at Swiggy |
| 2 | CAND_0046525 | 0.7194 | Senior Machine Learning Engineer |
| 3 | CAND_0036184 | 0.7169 | Recommendation Systems Engineer |
| 4 | CAND_0064326 | 0.6983 | Search Engineer |
| 5 | CAND_0011687 | 0.6902 | Senior NLP Engineer |
| 6 | CAND_0096142 | 0.6776 | Applied ML Engineer |
| 7 | CAND_0017960 | 0.6751 | Recommendation Systems Engineer |
| 8 | CAND_0041669 | 0.6735 | Recommendation Systems Engineer |
| 9 | CAND_0006418 | 0.6715 | Machine Learning Engineer |
| 10 | CAND_0014440 | 0.6631 | Recommendation Systems Engineer |

All top 10 are Recommendation Systems Engineers, Senior ML Engineers, or NLP Engineers — exactly what the JD requires. Zero keyword stuffers. Zero wrong-domain candidates.

---

## Setup

```bash
git clone https://github.com/janapati2005/redrob-ranker
cd redrob-ranker
pip install -r requirements.txt
```

Place candidates.jsonl in the data folder. The file is not included in this repo because it is 475 MB.

---

## Usage

Run on full dataset:
```bash
python src/rank.py --candidates candidates.jsonl --top 100
```

Run on sample of 50 candidates:
```bash
python src/rank.py
```

Validate output format:
```bash
python validate_submission.py output/submission.csv
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
│   └── sample_candidates.json     50-candidate test file
├── src/
│   ├── loader.py                  Reads .json, .jsonl, .jsonl.gz files
│   ├── features.py                6-signal feature extraction per candidate
│   ├── scorer.py                  Weighted scoring and availability multiplier
│   ├── honeypot.py                Fake profile detection and removal
│   ├── reasoner.py                Per-candidate reasoning text generation
│   └── rank.py                    Main pipeline entry point
├── output/
│   └── submission.csv             100 ranked candidates ready to submit
├── app.py                         Streamlit sandbox web application
├── requirements.txt               Python dependencies
├── submission_metadata.yaml       Team information and approach summary
├── validate_submission.py         Competition format validator
└── README.md                      This file
```

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11 | Core pipeline language |
| sentence-transformers | 3.0.1 | Semantic embeddings for upgrade phase |
| scikit-learn | 1.5.0 | Cosine similarity computation |
| numpy | 1.26.4 | Numerical operations |
| pandas | 2.2.2 | Data handling and CSV output |
| streamlit | 1.58.0 | Live web sandbox application |
| rank-bm25 | latest | BM25 text retrieval for upgrade phase |

---

## Live Sandbox

Try the ranker live. Upload sample_candidates.json to see it in action.

https://redrob-ranker-hg7bjpsw4c6dzf6wixkbg8.streamlit.app

---

## Team

| Name | Role | Email |
|------|------|-------|
| Hari Aditya Janapati | Team Lead | jhariaditya@gmail.com |
| Vurinindi Navadeep Kumar Reddy | ML Engineer | navadeepv2005@gmail.com |

GitHub: https://github.com/janapati2005/redrob-ranker

AI tools declared: Claude was used for architecture discussion and code review. No candidate data was fed to any LLM during ranking.