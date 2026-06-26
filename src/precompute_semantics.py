# precompute_semantics.py
# Run this once locally to generate semantic scores for sample_candidates.json
# The output data/semantic_scores.json is committed to GitHub so Streamlit
# can load real semantic scores without needing sentence-transformers at runtime.

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loader import load_candidates
from embedder import SemanticScorer

candidates = load_candidates("sample_candidates.json")
scorer = SemanticScorer()
results = scorer.score_candidates(candidates)

scores = {
    r["candidate"]["candidate_id"]: r["semantic_score"]
    for r in results
}

out_path = Path(__file__).parent.parent / "data" / "semantic_scores.json"
with open(out_path, "w") as f:
    json.dump(scores, f, indent=2)

print(f"Saved {len(scores)} semantic scores to {out_path}")
for cid, score in sorted(scores.items(), key=lambda x: -x[1])[:10]:
    print(f"  {cid}: {score:.4f}")