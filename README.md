# Redrob Candidate Ranker

AI-powered candidate ranking system for the Redrob Intelligent Candidate Discovery Challenge.

## What it does

Ranks 100,000 candidates for a Senior AI Engineer role by combining:
- Skill depth scoring (proficiency + endorsements + duration + assessment scores)
- Career trajectory analysis (title, company type, domain fit)
- Experience fit (JD wants 5-9 years)
- Behavioral availability (last active, response rate, notice period)
- Location fit (India preferred, Pune/Noida/Hyderabad/Bangalore)
- GitHub activity as bonus signal

Honeypot detection removes ~108 impossible/fabricated profiles before scoring.

## Setup

```bash
pip install -r requirements.txt
```

## Run on full dataset

```bash
python src/rank.py --candidates candidates.jsonl --top 100
```

## Run on sample

```bash
python src/rank.py
```

## Validate output

```bash
python validate_submission.py output/submission.csv
```

## Runtime

- 100,000 candidates ranked in ~12 seconds on CPU
- No GPU required
- No network calls during ranking
- Memory: well under 16GB

## Project Structure

```
src/
├── loader.py       # Reads candidate files (.json, .jsonl, .jsonl.gz)
├── features.py     # Extracts 6 scored signals per candidate
├── scorer.py       # Combines features into final score, ranks all
├── honeypot.py     # Detects and removes impossible profiles
├── reasoner.py     # Generates per-candidate reasoning text
└── rank.py         # Main pipeline, outputs submission CSV
```