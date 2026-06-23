# embedder.py
# Stage 2 of the two-stage pipeline.
# Uses sentence-transformers to encode the JD and candidate profiles
# into vectors, then computes cosine similarity.
#
# Why sentence-transformers and not TF-IDF?
# TF-IDF matches exact words. sentence-transformers understand MEANING.
# "Search Systems Engineer who built retrieval pipelines" and
# "Information Retrieval Engineer with FAISS experience" will score
# high similarity even though they share almost no exact words.
#
# Why cosine similarity and not dot product?
# Cosine similarity is normalized — it measures the ANGLE between
# vectors, not their magnitude. This means a short profile and a long
# profile are compared fairly. Dot product would unfairly favor
# candidates with longer profiles.
#
# Model: all-MiniLM-L6-v2
# Why this model?
# - Fast: encodes 2000 candidates in ~5 seconds on CPU
# - Small: 90MB download, runs on any machine
# - Good quality: trained on 1 billion sentence pairs
# - Offline: once downloaded, works with no internet

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# ── JD text for embedding ──────────────────────────────────────────────────────
# This is the full job description condensed into key concepts.
# The model will encode this into a 384-dimensional vector.

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
    """
    Builds a rich text representation of the candidate for embedding.
    Uses the same fields as BM25 but keeps them as natural sentences
    so the transformer model can understand context properly.
    """
    parts = []

    profile = candidate.get("profile", {})

    # Professional identity
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

    # Career history — most important text
    for job in candidate.get("career_history", []):
        job_title = job.get("title", "")
        job_company = job.get("company", "")
        description = job.get("description", "")
        if job_title and description:
            parts.append(
                f"Worked as {job_title} at {job_company}. {description}"
            )

    # Top skills as a sentence
    skills = candidate.get("skills", [])
    if skills:
        skill_names = [s["name"] for s in skills[:10]]
        parts.append(f"Skills include: {', '.join(skill_names)}.")

    # Certifications
    certs = candidate.get("certifications", [])
    if certs:
        cert_names = [c["name"] for c in certs[:5]]
        parts.append(f"Certifications: {', '.join(cert_names)}.")

    return " ".join(parts)


class SemanticScorer:
    """
    Loads the sentence-transformer model once and reuses it.
    Loading the model takes ~3 seconds — we do it once, not per candidate.
    """

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        print(f"  Loading sentence-transformer model: {model_name}")
        print(f"  (First run downloads ~90MB — subsequent runs use cache)")
        self.model = SentenceTransformer(model_name)
        self.jd_embedding = None
        print(f"  Model loaded.")

    def encode_jd(self):
        """Encode the JD text into a vector. Done once."""
        self.jd_embedding = self.model.encode(
            [JD_TEXT],
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return self.jd_embedding

    def score_candidates(self, candidates):
        """
        Encodes all candidate texts and computes cosine similarity with JD.
        Returns list of (candidate, semantic_score) tuples.
        """
        if self.jd_embedding is None:
            self.encode_jd()

        print(f"  Encoding {len(candidates)} candidate profiles...")

        # Build candidate texts
        texts = [_build_candidate_text(c) for c in candidates]

        # Encode all candidates in one batch (faster than one by one)
        candidate_embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=64
        )

        # Compute cosine similarity between JD and each candidate
        similarities = cosine_similarity(
            self.jd_embedding,
            candidate_embeddings
        )[0]

        # Normalize to 0-1 range
        # cosine similarity is already -1 to 1, but for job descriptions
        # all scores will be positive (0 to 1) since content is related
        results = []
        for candidate, sim in zip(candidates, similarities):
            # Raw cosine similarity is already 0-1 for related text
            # Clamp to [0, 1] instead of min-max normalizing against the batch
            normalized = float(max(0.0, min(1.0, sim)))
            results.append({
                "candidate": candidate,
                "semantic_score": round(normalized, 6),
                "raw_similarity": round(float(sim), 6)
            })


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

    # Sort by semantic score
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