# rank.py — UPGRADED
# Two-stage pipeline:
# Stage 1: BM25 retrieval over all 100k candidates
# Stage 2: Semantic scoring on BM25 shortlist
# Stage 3: Full feature scoring + availability multiplier
# Output: Top 100 candidates with reasoning

import csv
import sys
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loader import load_candidates
from honeypot import filter_honeypots
from scorer import score_all
from reasoner import generate_reasoning
from bm25_retriever import get_bm25_shortlist
from embedder import SemanticScorer

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def parse_args():
    parser = argparse.ArgumentParser(description="Redrob Candidate Ranker")
    parser.add_argument(
        "--candidates",
        default="sample_candidates.json",
        help="Candidate file in data/ folder"
    )
    parser.add_argument(
        "--top", type=int, default=None,
        help="How many top candidates to output (default: 100)"
    )
    parser.add_argument(
        "--out", default=None,
        help="Output CSV filename (default: submission.csv)"
    )
    parser.add_argument(
        "--bm25-k", type=int, default=1500,
        help="BM25 shortlist size (default: 3000)"
    )
    parser.add_argument(
        "--no-semantic", action="store_true",
        help="Skip semantic embeddings (faster, baseline mode)"
    )
    return parser.parse_args()


def run_pipeline(candidates_file, top_n, out_file, bm25_k=3000, use_semantic=True):
    start_time = time.time()

    print("=" * 60)
    print("REDROB CANDIDATE RANKER — HYBRID TWO-STAGE PIPELINE")
    print("=" * 60)

    # ── Step 1: Load ──────────────────────────────────────────
    print(f"\n[1/5] Loading candidates from '{candidates_file}'...")
    candidates = load_candidates(candidates_file)
    print(f"      {len(candidates)} candidates loaded.")
    t1 = time.time()

    # ── Step 2: Honeypot filter ───────────────────────────────
    print(f"\n[2/5] Running honeypot detection...")
    clean, honeypots = filter_honeypots(candidates, verbose=False)
    print(f"      {len(honeypots)} honeypots removed.")
    print(f"      {len(clean)} candidates proceeding to ranking.")
    t2 = time.time()
    print(f"      Time: {t2-t1:.1f}s")

    # ── Step 3: BM25 shortlist ────────────────────────────────
    print(f"\n[3/5] Stage 1 — BM25 retrieval...")
    if len(clean) > bm25_k:
        bm25_results = get_bm25_shortlist(clean, top_k=bm25_k)
        shortlisted = [r["candidate"] for r in bm25_results]
        bm25_score_map = {
            r["candidate"]["candidate_id"]: r["bm25_score"]
            for r in bm25_results
        }
        print(f"      Shortlisted {len(shortlisted)} from {len(clean)} candidates.")
    else:
        # For small datasets (sample), skip BM25 shortlisting
        shortlisted = clean
        bm25_score_map = {}
        print(f"      Small dataset — skipping BM25 shortlist.")
    t3 = time.time()
    print(f"      Time: {t3-t2:.1f}s")

    # ── Step 4: Semantic scoring ──────────────────────────────
    semantic_scores = {}
    if use_semantic:
        print(f"\n[4/5] Stage 2 — Semantic embedding scoring...")
        scorer = SemanticScorer()
        sem_results = scorer.score_candidates(shortlisted)
        semantic_scores = {
            r["candidate"]["candidate_id"]: r["semantic_score"]
            for r in sem_results
        }
        print(f"      Scored {len(semantic_scores)} candidates semantically.")
        t4 = time.time()
        print(f"      Time: {t4-t3:.1f}s")
    else:
        print(f"\n[4/5] Semantic scoring skipped (--no-semantic flag).")
        t4 = time.time()

    # ── Step 5: Full feature scoring + rank ──────────────────
    print(f"\n[5/5] Stage 3 — Full feature scoring and ranking...")
    ranked = score_all(shortlisted, semantic_scores=semantic_scores)

    if top_n is None:
        top_n = min(100, len(ranked))
    top_candidates = ranked[:top_n]
    print(f"      Ranked {len(ranked)} candidates. Taking top {top_n}.")
    t5 = time.time()
    print(f"      Time: {t5-t4:.1f}s")

    # ── Output: Generate reasoning and write CSV ──────────────
    lookup = {c["candidate_id"]: c for c in shortlisted}
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
            f, fieldnames=["candidate_id", "rank", "score", "reasoning"]
        )
        writer.writeheader()
        writer.writerows(rows)

    elapsed = time.time() - start_time

    print(f"\n{'=' * 60}")
    print(f"DONE in {elapsed:.1f} seconds")
    print(f"{'=' * 60}")

    print(f"\nTop 10 candidates:")
    print(f"{'Rank':<5} {'ID':<15} {'Score':>7}  {'Sem':>6}  Reasoning preview")
    print("-" * 75)
    for row in rows[:10]:
        cid = row["candidate_id"]
        sem = semantic_scores.get(cid, 0.0)
        preview = row["reasoning"][:45] + "..."
        print(
            f"{row['rank']:<5} "
            f"{cid:<15} "
            f"{row['score']:>7.4f}  "
            f"{sem:>6.3f}  "
            f"{preview}"
        )

    print(f"\nHoneypots removed  : {len(honeypots)}")
    print(f"BM25 shortlist     : {len(shortlisted)}")
    print(f"Candidates scored  : {len(ranked)}")
    print(f"Output rows        : {len(rows)}")
    print(f"Runtime            : {elapsed:.1f}s")
    print(f"CSV written to     : {out_path}")

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
        out_file=out_file,
        bm25_k=args.bm25_k,
        use_semantic=not args.no_semantic
    )


if __name__ == "__main__":
    main()