import streamlit as st
import json
import tempfile
import os
import sys
import gzip
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from loader import load_candidates
from honeypot import filter_honeypots
from scorer import score_all
from reasoner import generate_reasoning

st.set_page_config(
    page_title="CrossSense — Candidate Ranker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp {
    background: linear-gradient(135deg, #f8f4ff 0%, #fef9f0 50%, #f0f7ff 100%);
    color: #1a1a2e;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
header {visibility: hidden;}
.hero {
    background: linear-gradient(135deg, #7c3aed 0%, #a855f7 40%, #ec4899 100%);
    border-radius: 24px;
    padding: 56px 48px;
    margin-bottom: 32px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(124,58,237,0.25);
    position: relative;
    overflow: hidden;
}
.hero h1 {
    font-size: 3rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0 0 12px 0;
    line-height: 1.1;
}
.hero p {
    color: rgba(255,255,255,0.85);
    font-size: 1.05rem;
    margin: 0;
    line-height: 1.6;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 30px;
    padding: 6px 20px;
    font-size: 0.82rem;
    color: #fff;
    margin-bottom: 20px;
}
.step-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 1px solid rgba(124,58,237,0.08);
    height: 100%;
}
.step-icon { font-size: 2.2rem; margin-bottom: 12px; }
.step-title { font-size: 1rem; font-weight: 700; color: #1a1a2e; margin-bottom: 8px; }
.step-desc { font-size: 0.83rem; color: #6b7280; line-height: 1.5; }
.metric-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 1px solid rgba(124,58,237,0.08);
}
.metric-value {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #7c3aed, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-label {
    font-size: 0.75rem;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}
.section-header {
    font-size: 1.4rem;
    font-weight: 700;
    color: #1a1a2e;
    margin: 32px 0 16px 0;
}
.signal-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: #6b7280;
    margin-bottom: 3px;
}
.signal-val { font-weight: 600; color: #1a1a2e; }
.bar-track {
    background: #f3f4f6;
    border-radius: 6px;
    height: 7px;
    margin-bottom: 10px;
    overflow: hidden;
}
.bar-fill { height: 7px; border-radius: 6px; }
.reasoning-box {
    background: linear-gradient(135deg, #faf5ff, #fdf2f8);
    border-left: 4px solid #a855f7;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    font-size: 0.88rem;
    color: #374151;
    line-height: 1.6;
    margin-bottom: 16px;
}
.skill-pill {
    display: inline-block;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.76rem;
    font-weight: 500;
    margin: 3px 3px 3px 0;
}
.stat-box {
    background: #ffffff;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    border: 1px solid rgba(124,58,237,0.08);
    margin-bottom: 12px;
}
.stat-box-title {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #9ca3af;
    margin-bottom: 10px;
    font-weight: 600;
}
.stat-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #f3f4f6;
    font-size: 0.84rem;
}
.stat-row:last-child { border-bottom: none; }
.stat-key { color: #6b7280; }
.stat-val { font-weight: 600; color: #1a1a2e; }
.signal-table {
    background: #ffffff;
    border-radius: 16px;
    padding: 28px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 1px solid rgba(124,58,237,0.08);
}
.signal-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #f3f4f6;
}
.signal-row:last-child { border-bottom: none; }
.signal-name { color: #374151; font-size: 0.9rem; }
.signal-weight {
    font-weight: 700;
    font-size: 0.9rem;
    background: linear-gradient(135deg, #7c3aed, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">⚡ Team CrossSense · Redrob AI Hackathon 2026</div>
    <h1>Intelligent Candidate Ranker</h1>
    <p>Upload any candidate pool and get AI-powered rankings in seconds.<br>
    BM25 retrieval · Semantic embeddings · 9-signal behavioral scoring</p>
</div>
""", unsafe_allow_html=True)

# ── Step cards ────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""<div class="step-card">
        <div class="step-icon">📂</div>
        <div class="step-title">Upload</div>
        <div class="step-desc">Drop any candidates JSON file — sample or full 100k pool</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown("""<div class="step-card">
        <div class="step-icon">🧠</div>
        <div class="step-title">Analyze</div>
        <div class="step-desc">BM25 retrieval then semantic embeddings then 9-signal weighted scoring</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown("""<div class="step-card">
        <div class="step-icon">🏆</div>
        <div class="step-title">Rank</div>
        <div class="step-desc">Top candidates with full signal breakdown, reasoning, and download</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload candidates file",
    type=["json", "jsonl", "gz"],
    label_visibility="collapsed"
)

if not uploaded_file:
    st.markdown("""
    <div class="signal-table" style="margin-top:8px">
        <div style="font-size:1.05rem;font-weight:700;color:#1a1a2e;margin-bottom:16px">
            📊 Scoring system — 9 signals + availability multiplier
        </div>
        <div class="signal-row">
            <span class="signal-name">🎯 Skill Match — proficiency, endorsements, duration, assessment</span>
            <span class="signal-weight">27%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">💼 Career Fit — title, domain, product company, consulting penalty</span>
            <span class="signal-weight">24%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">🔗 Semantic Similarity — sentence-transformer JD embedding match</span>
            <span class="signal-weight">15%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">📅 Experience Fit — JD wants 5 to 9 years, sweet spot 6 to 8</span>
            <span class="signal-weight">10%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">📍 Location Fit — India preferred, Pune and Noida ideal</span>
            <span class="signal-weight">8%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">📈 Platform Demand — recruiter saves, search appearances</span>
            <span class="signal-weight">6%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">💻 GitHub Activity — open source contribution score</span>
            <span class="signal-weight">5%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">🎓 Education — institution tier and field relevance</span>
            <span class="signal-weight">3%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">✅ Profile Quality — connections, LinkedIn, interview rate</span>
            <span class="signal-weight">2%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">⚡ Availability — last active, response rate, notice period</span>
            <span class="signal-weight">× multiplier</span>
        </div>
    </div>
    <p style="color:#9ca3af;font-size:0.82rem;text-align:center;margin-top:16px">
        Upload <code>sample_candidates.json</code> from the hackathon bundle to get started
    </p>
    """, unsafe_allow_html=True)

else:
    try:
        # Save uploaded file
        suffix = ".json"
        fname = uploaded_file.name.lower()
        if fname.endswith(".gz"):
            suffix = ".gz"
        elif fname.endswith(".jsonl"):
            suffix = ".jsonl"

        with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        # Load candidates
        if suffix == ".gz":
            candidates = []
            with gzip.open(tmp_path, 'rt', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        candidates.append(json.loads(line))
        elif suffix == ".jsonl":
            candidates = []
            with open(tmp_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        candidates.append(json.loads(line))
        else:
            with open(tmp_path, 'r', encoding='utf-8') as f:
                candidates = json.load(f)

        BM25_K = 1500

        # Pipeline
        progress = st.progress(0, text="Filtering candidates...")
        clean, honeypots = filter_honeypots(candidates, verbose=False)

        progress.progress(15, text="Stage 1 — BM25 retrieval...")
        try:
            from bm25_retriever import get_bm25_shortlist
            if len(clean) > BM25_K:
                bm25_results = get_bm25_shortlist(clean, top_k=BM25_K)
                shortlisted = [r["candidate"] for r in bm25_results]
            else:
                shortlisted = clean
        except Exception:
            shortlisted = clean

        progress.progress(35, text="Stage 2 — Semantic embedding scoring (loads ~90MB model on first run)...")
        from embedder import SemanticScorer
        scorer_obj = SemanticScorer()
        sem_results = scorer_obj.score_candidates(shortlisted)
        semantic_scores = {
            r["candidate"]["candidate_id"]: r["semantic_score"]
            for r in sem_results
        }

        progress.progress(80, text="Stage 3 — Full feature scoring and ranking...")
        ranked = score_all(shortlisted, semantic_scores=semantic_scores)

        TOP_N = 10
        top = ranked[:TOP_N]
        lookup = {c["candidate_id"]: c for c in shortlisted}

        progress.progress(95, text="Generating reasoning...")
        reasonings = {}
        for i, r in enumerate(ranked[:100], 1):
            cid = r["candidate_id"]
            if cid in lookup:
                reasonings[cid] = generate_reasoning(
                    lookup[cid], rank=i, score=r["score"]
                )

        progress.progress(100, text="Done!")
        progress.empty()

        # Metrics
        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{len(candidates)}</div>
                <div class="metric-label">Total Candidates</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{len(honeypots)}</div>
                <div class="metric-label">Honeypots Removed</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{len(shortlisted)}</div>
                <div class="metric-label">After BM25</div>
            </div>""", unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{len(ranked)}</div>
                <div class="metric-label">Candidates Ranked</div>
            </div>""", unsafe_allow_html=True)
        with m5:
            top_score = top[0]["score"] if top else 0
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{top_score:.3f}</div>
                <div class="metric-label">Top Score</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(
            f'<div class="section-header">🏆 Top {TOP_N} Candidates</div>',
            unsafe_allow_html=True
        )

        # Candidate cards
        for i, r in enumerate(top, 1):
            cid = r["candidate_id"]
            c = lookup[cid]
            p = c["profile"]
            f = r["features"]
            reasoning = reasonings.get(cid, "")
            sem_score = semantic_scores.get(cid, 0.0)
            rs = c.get("redrob_signals", {})

            with st.expander(
                f"#{i}  ·  {p['current_title']} @ {p['current_company']}"
                f"  ·  {p['years_of_experience']}y exp"
                f"  ·  {p['location']}, {p['country']}"
                f"  ·  Score: {r['score']:.4f}"
            ):
                left, right = st.columns([1, 1])

                with left:
                    st.markdown(f"""
                    <div style="margin-bottom:16px">
                        <div style="font-size:0.75rem;color:#9ca3af;
                                    text-transform:uppercase;letter-spacing:1px">
                            Candidate ID
                        </div>
                        <div style="font-weight:700;color:#1a1a2e;font-size:1rem">
                            {cid}
                        </div>
                        <div style="color:#6b7280;font-size:0.85rem;margin-top:4px">
                            {p.get('headline', '')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    signals = [
                        ("🎯 Skill Match",     f.get("skill_match", 0),    "linear-gradient(90deg,#7c3aed,#a855f7)"),
                        ("💼 Career Fit",       f.get("career_fit", 0),     "linear-gradient(90deg,#a855f7,#ec4899)"),
                        ("🔗 Semantic",         sem_score,                  "linear-gradient(90deg,#8b5cf6,#7c3aed)"),
                        ("📅 Experience",       f.get("experience_fit", 0), "linear-gradient(90deg,#10b981,#34d399)"),
                        ("📍 Location",         f.get("location_fit", 0),   "linear-gradient(90deg,#3b82f6,#60a5fa)"),
                        ("📈 Platform Demand",  f.get("platform_demand", 0),"linear-gradient(90deg,#f97316,#fb923c)"),
                        ("💻 GitHub",           f.get("github", 0),         "linear-gradient(90deg,#0f172a,#334155)"),
                        ("🎓 Education",        f.get("education", 0),      "linear-gradient(90deg,#0ea5e9,#38bdf8)"),
                        ("✅ Profile Quality",  f.get("profile_quality", 0),"linear-gradient(90deg,#14b8a6,#2dd4bf)"),
                        ("⚡ Availability",     f.get("availability", 0),   "linear-gradient(90deg,#f59e0b,#fbbf24)"),
                    ]
                    for label, val, grad in signals:
                        pct = int(val * 100)
                        st.markdown(f"""
                        <div class="signal-label">
                            <span>{label}</span>
                            <span class="signal-val">{pct}%</span>
                        </div>
                        <div class="bar-track">
                            <div class="bar-fill"
                                 style="width:{pct}%;background:{grad}"></div>
                        </div>
                        """, unsafe_allow_html=True)

                with right:
                    # Reasoning
                    st.markdown("""
                    <div style="font-size:0.7rem;color:#9ca3af;text-transform:uppercase;
                                letter-spacing:1px;margin-bottom:8px">
                        Why this candidate
                    </div>""", unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="reasoning-box">{reasoning}</div>',
                        unsafe_allow_html=True
                    )

                    # Candidate stats — using correct field names
                    notice = rs.get("notice_period_days", "—")
                    rrr = rs.get("recruiter_response_rate", None)
                    saved = rs.get("saved_by_recruiters_30d", "—")
                    last_active = rs.get("last_active_date", "—")
                    open_to_work = rs.get("open_to_work_flag", False)
                    gh_score = rs.get("github_activity_score", -1)
                    interviews = rs.get("interview_completion_rate", "—")
                    connections = rs.get("connection_count", "—")

                    rrr_display = f"{int(rrr*100)}%" if rrr is not None else "—"
                    notice_display = f"{notice} days" if notice != "—" else "—"
                    gh_display = str(gh_score) if gh_score != -1 else "Not linked"
                    otw_display = "Yes" if open_to_work else "No"

                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-box-title">Candidate Stats</div>
                        <div class="stat-row">
                            <span class="stat-key">Notice Period</span>
                            <span class="stat-val">{notice_display}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Open to Work</span>
                            <span class="stat-val">{otw_display}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Last Active</span>
                            <span class="stat-val">{last_active}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Recruiter Response Rate</span>
                            <span class="stat-val">{rrr_display}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Saved by Recruiters (30d)</span>
                            <span class="stat-val">{saved}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Connections</span>
                            <span class="stat-val">{connections}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">GitHub Score</span>
                            <span class="stat-val">{gh_display}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Interview Completion</span>
                            <span class="stat-val">{interviews}</span>
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-box-title">Pipeline Scores</div>
                        <div class="stat-row">
                            <span class="stat-key">Semantic Score</span>
                            <span class="stat-val">{sem_score:.4f}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Availability Multiplier</span>
                            <span class="stat-val">{r.get('multiplier', 0):.4f}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Final Score</span>
                            <span class="stat-val">{r['score']:.4f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Top skills
                    st.markdown("""
                    <div style="font-size:0.7rem;color:#9ca3af;text-transform:uppercase;
                                letter-spacing:1px;margin:4px 0 8px 0">
                        Top Skills
                    </div>""", unsafe_allow_html=True)

                    skills = sorted(
                        c.get("skills", []),
                        key=lambda s: s.get("endorsements", 0),
                        reverse=True
                    )[:8]
                    pills_html = ""
                    for s in skills:
                        colors = {
                            "expert":       ("ede9fe", "7c3aed"),
                            "advanced":     ("fce7f3", "be185d"),
                            "intermediate": ("d1fae5", "065f46"),
                            "beginner":     ("f3f4f6", "6b7280")
                        }
                        bg, fg = colors.get(
                            s.get("proficiency", "beginner"),
                            ("f3f4f6", "6b7280")
                        )
                        pills_html += (
                            f'<span class="skill-pill" '
                            f'style="background:#{bg};color:#{fg}">'
                            f'{s["name"]}</span>'
                        )
                    st.markdown(pills_html, unsafe_allow_html=True)

        # Download
        import csv, io
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["candidate_id", "rank", "score", "reasoning"]
        )
        writer.writeheader()
        for i, r in enumerate(ranked[:100], 1):
            cid = r["candidate_id"]
            if cid in lookup:
                writer.writerow({
                    "candidate_id": cid,
                    "rank":         i,
                    "score":        round(r["score"], 6),
                    "reasoning":    reasonings.get(cid, "")
                })

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="⬇️  Download submission.csv",
            data=output.getvalue(),
            file_name="submission.csv",
            mime="text/csv",
            use_container_width=True
        )
        os.unlink(tmp_path)

    except Exception as e:
        st.error(f"Error: {e}")
        raise e