# embedder.py
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

JD_TEXT = """
Senior AI Engineer at a Series A startup building intelligent candidate
discovery and ranking systems. The role requires hands-on experience
building production-grade embeddings-based retrieval systems using
FAISS, Pinecone, Weaviate, Qdrant, or similar vector databases.
Must have designed hybrid search systems combining dense retrieval
with sparse methods. Strong background in NLP, sentence transformers,
semantic search, and information retrieval. Experience with ranking
evaluation metrics NDCG, MRR, MAP. Python expertise required.
Learning to rank with XGBoost or LightGBM is a plus.
5 to 9 years of experience. Based in India, Pune or Noida preferred.
Product company experience preferred over consulting background.
"""


def _build_candidate_text(candidate):
    parts = []
    profile = candidate.get("profile", {})

    title = profile.get("current_title", "")
    company = profile.get("current_company", "")
    headline = profile.get("headline", "")
    summary = profile.get("summary", "")

    if title:
        parts.append(f"Current role: {title} at {company}.")
    if headline:
        parts.append(headline)
    if summary:
        parts.append(summary)

    for job in candidate.get("career_history", []):
        job_title = job.get("title", "")
        job_company = job.get("company", "")
        description = job.get("description", "")
        if job_title and description:
            parts.append(f"Worked as {job_title} at {job_company}. {description}")

    skills = candidate.get("skills", [])
    if skills:
        skill_names = [s["name"] for s in skills[:10]]
        parts.append(f"Skills include: {', '.join(skill_names)}.")

    certs = candidate.get("certifications", [])
    if certs:
        cert_names = [c["name"] for c in certs[:5]]
        parts.append(f"Certifications: {', '.join(cert_names)}.")

    return " ".join(parts)


class SemanticScorer:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        print(f"  Loading sentence-transformer model: {model_name}")
        print(f"  (First run downloads ~90MB — subsequent runs use cache)")
        self.model = SentenceTransformer(model_name)
        self.jd_embedding = None
        print(f"  Model loaded.")

    def encode_jd(self):
        self.jd_embedding = self.model.encode(
            [JD_TEXT],
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return self.jd_embedding

    def score_candidates(self, candidates):
        if self.jd_embedding is None:
            self.encode_jd()

        print(f"  Encoding {len(candidates)} candidate profiles...")

        texts = [_build_candidate_text(c) for c in candidates]

        candidate_embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=64
        )

        similarities = cosine_similarity(
            self.jd_embedding,
            candidate_embeddings
        )[0]

        results = []
        for candidate, sim in zip(candidates, similarities):
            normalized = float(max(0.0, min(1.0, sim)))
            results.append({
                "candidate": candidate,
                "semantic_score": round(normalized, 6),
                "raw_similarity": round(float(sim), 6)
            })

        return results


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from loader import load_candidates

    candidates = load_candidates("sample_candidates.json")
    scorer = SemanticScorer()
    results = scorer.score_candidates(candidates)
    results.sort(key=lambda x: x["semantic_score"], reverse=True)

    print(f"\nTop 15 by Semantic Similarity to JD:\n")
    print(f"{'Rank':<5} {'ID':<15} {'Semantic':>9} {'Raw Sim':>9}  Title")
    print("-" * 75)
    for i, r in enumerate(results[:15], 1):
        c = r["candidate"]
        p = c["profile"]
        print(
            f"{i:<5} "
            f"{c['candidate_id']:<15} "
            f"{r['semantic_score']:>9.4f} "
            f"{r['raw_similarity']:>9.4f}  "
            f"{p['current_title']} @ {p['current_company']}"
        )