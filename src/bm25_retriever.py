# bm25_retriever.py
# Stage 1 of the two-stage pipeline.
# Uses BM25 to search career descriptions, summaries, and headlines
# for candidates whose actual WORK matches the JD — not just their title.
#
# Why BM25 and not simple keyword search?
# BM25 accounts for term frequency (how often a word appears)
# and document length (a short profile mentioning FAISS once
# scores higher than a long profile mentioning it briefly).
# This is the same algorithm used inside Elasticsearch internally.

from rank_bm25 import BM25Okapi
import re

# ── JD text — what we're searching for ────────────────────────────────────────
# These are the key concepts from the job description.
# BM25 will find candidates whose career descriptions contain these ideas.

JD_QUERY = """
embeddings vector database semantic search information retrieval ranking
faiss pinecone weaviate qdrant milvus opensearch elasticsearch
sentence transformers dense retrieval hybrid search
recommendation system search ranking nlp machine learning
python production deployment retrieval augmented generation
ndcg mrr map evaluation learning to rank
xgboost lightgbm feature engineering
""".strip()


def _tokenize(text):
    """
    Convert text to lowercase tokens.
    Removes punctuation, splits on whitespace.
    """
    if not text:
        return []
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return [t for t in text.split() if len(t) > 1]


def _build_candidate_document(candidate):
    """
    Combines all text fields from a candidate into one searchable document.
    This is what the founder meant by 'go through the dataset carefully' —
    the real signal is in the text, not just the skill tags.
    """
    parts = []

    profile = candidate.get("profile", {})

    # Headline and summary — candidate's own description of themselves
    parts.append(profile.get("headline", ""))
    parts.append(profile.get("summary", ""))
    parts.append(profile.get("current_title", ""))
    parts.append(profile.get("current_industry", ""))

    # Career history descriptions — what they actually DID in each job
    # This is the most important text field in the entire dataset
    for job in candidate.get("career_history", []):
        parts.append(job.get("title", ""))
        parts.append(job.get("description", ""))
        parts.append(job.get("industry", ""))
        parts.append(job.get("company", ""))

    # Skills — name only (proficiency handled in features.py)
    for skill in candidate.get("skills", []):
        parts.append(skill.get("name", ""))

    # Certifications — relevant certs are strong signals
    for cert in candidate.get("certifications", []):
        parts.append(cert.get("name", ""))
        parts.append(cert.get("issuer", ""))

    # Education field of study
    for edu in candidate.get("education", []):
        parts.append(edu.get("field_of_study", ""))
        parts.append(edu.get("degree", ""))

    return " ".join(p for p in parts if p)


def build_bm25_index(candidates):
    """
    Builds a BM25 index over all candidate documents.
    Returns (bm25_model, tokenized_query, documents_list).
    """
    print(f"  Building BM25 index over {len(candidates)} candidates...")

    # Build one document per candidate
    documents = [_build_candidate_document(c) for c in candidates]

    # Tokenize all documents
    tokenized_docs = [_tokenize(doc) for doc in documents]

    # Build BM25 index
    bm25 = BM25Okapi(tokenized_docs)

    # Tokenize the JD query
    query_tokens = _tokenize(JD_QUERY)

    print(f"  BM25 index built. Query has {len(query_tokens)} tokens.")
    return bm25, query_tokens, documents


def get_bm25_shortlist(candidates, top_k=3000):
    """
    Returns top_k candidates most relevant to the JD based on BM25 scores.
    This is Stage 1 — fast retrieval before expensive semantic scoring.

    Why top_k=3000?
    - We need top 100 final candidates
    - Some will be filtered by honeypot detection
    - Some will score low on behavioral signals
    - 3000 gives us a safe buffer while keeping semantic step fast
    """
    bm25, query_tokens, documents = build_bm25_index(candidates)

    # Get BM25 scores for all candidates
    scores = bm25.get_scores(query_tokens)

    # Pair each candidate with their BM25 score
    scored = list(zip(candidates, scores))

    # Sort by BM25 score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Return top_k candidates and their normalized BM25 scores
    top_candidates = []
    max_score = scored[0][1] if scored[0][1] > 0 else 1.0

    for candidate, score in scored[:top_k]:
        top_candidates.append({
            "candidate": candidate,
            "bm25_score": round(float(score) / max_score, 6)
        })

    print(f"  BM25 shortlisted {len(top_candidates)} candidates from {len(candidates)}.")
    return top_candidates


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from loader import load_candidates

    candidates = load_candidates("sample_candidates.json")
    shortlist = get_bm25_shortlist(candidates, top_k=20)

    print(f"\nTop 20 by BM25 (text relevance to JD):\n")
    print(f"{'Rank':<5} {'ID':<15} {'BM25':>7}  Title")
    print("-" * 65)
    for i, item in enumerate(shortlist, 1):
        c = item["candidate"]
        p = c["profile"]
        print(
            f"{i:<5} "
            f"{c['candidate_id']:<15} "
            f"{item['bm25_score']:>7.4f}  "
            f"{p['current_title']} @ {p['current_company']}"
        )