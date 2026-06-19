# rank.py
# Main entry point. Runs the full pipeline and outputs submission CSV.
# Usage:
#   python src/rank.py                                    (uses sample)
#   python src/rank.py --candidates candidates.jsonl.gz  (uses full file)
#   python src/rank.py --candidates candidates.jsonl.gz --top 100

import csv
import sys
import argparse
import time
from pathlib import Path

# Make sure src/ modules are importable
sys.path.insert(0, str(Path(__file__).parent))

from loader import load_candidates
from honeypot import filter_honeypots
from scorer import score_all
from reasoner import generate_reasoning

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def parse_args():
    parser = argparse.ArgumentParser(description="Redrob Candidate Ranker")
    parser.add_argument(
        "--candidates",
        default="sample_candidates.json",
        help="Candidate file in data/ folder (default: sample_candidates.json)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="How many top candidates to output (default: 100 for full file, all for sample)"
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output CSV filename (default: submission.csv)"
    )
    return parser.parse_args()


def build_candidate_lookup(candidates):
    """Fast ID → candidate dict for reasoner lookups."""
    return {c["candidate_id"]: c for c in candidates}


def run_pipeline(candidates_file, top_n, out_file):
    start_time = time.time()

    print("=" * 60)
    print("REDROB CANDIDATE RANKER")
    print("=" * 60)

    # ── Step 1: Load ──────────────────────────────────────────────
    print(f"\n[1/4] Loading candidates from '{candidates_file}'...")
    candidates = load_candidates(candidates_file)
    print(f"      {len(candidates)} candidates loaded.")

    # ── Step 2: Honeypot filter ───────────────────────────────────
    print(f"\n[2/4] Running honeypot detection...")
    clean, honeypots = filter_honeypots(candidates, verbose=False)
    print(f"      {len(honeypots)} honeypots removed.")
    print(f"      {len(clean)} candidates proceeding to scoring.")

    # ── Step 3: Score and rank ────────────────────────────────────
    print(f"\n[3/4] Scoring and ranking candidates...")
    ranked = score_all(clean)

    # Determine how many to output
    if top_n is None:
        top_n = min(100, len(ranked))
    top_candidates = ranked[:top_n]
    print(f"      Ranked {len(ranked)} candidates. Taking top {top_n}.")

    # ── Step 4: Generate reasoning and write CSV ──────────────────
    print(f"\n[4/4] Generating reasoning and writing CSV...")
    lookup = build_candidate_lookup(clean)

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / out_file

    rows = []
    for rank_pos, r in enumerate(top_candidates, 1):
        cid = r["candidate_id"]
        score = r["score"]
        candidate = lookup[cid]
        reasoning = generate_reasoning(candidate, rank=rank_pos, score=score)

        rows.append({
            "candidate_id": cid,
            "rank":         rank_pos,
            "score":        round(score, 6),
            "reasoning":    reasoning
        })

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["candidate_id", "rank", "score", "reasoning"]
        )
        writer.writeheader()
        writer.writerows(rows)

    elapsed = time.time() - start_time

    print(f"      CSV written to: {out_path}")
    print(f"\n{'=' * 60}")
    print(f"DONE in {elapsed:.1f} seconds")
    print(f"{'=' * 60}")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\nTop 10 candidates:")
    print(f"{'Rank':<5} {'ID':<15} {'Score':>7}  Reasoning preview")
    print("-" * 70)
    for row in rows[:10]:
        preview = row["reasoning"][:55] + "..."
        print(f"{row['rank']:<5} {row['candidate_id']:<15} {row['score']:>7.4f}  {preview}")

    print(f"\nHoneypots removed  : {len(honeypots)}")
    print(f"Candidates scored  : {len(ranked)}")
    print(f"Output rows        : {len(rows)}")
    print(f"Runtime            : {elapsed:.1f}s")

    if elapsed > 280:
        print("\nWARNING: Runtime approaching 5-minute limit.")
    else:
        print(f"Runtime is within the 5-minute competition limit.")

    return out_path


def main():
    args = parse_args()
    out_file = args.out if args.out else "submission.csv"
    run_pipeline(
        candidates_file=args.candidates,
        top_n=args.top,
        out_file=out_file
    )


if __name__ == "__main__":
    main()