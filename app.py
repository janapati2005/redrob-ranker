import streamlit as st
import json
import tempfile
import os
import sys
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
    box-shadow: 0 20px 60px rgba(124, 58, 237, 0.25);
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -20%;
    width: 60%;
    height: 200%;
    background: rgba(255,255,255,0.06);
    border-radius: 50%;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -30%;
    right: -10%;
    width: 40%;
    height: 150%;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 30px;
    padding: 6px 20px;
    font-size: 0.82rem;
    color: #fff;
    margin-bottom: 20px;
    letter-spacing: 0.5px;
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
.stat-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #f3f4f6;
    font-size: 0.85rem;
}
.stat-row:last-child { border-bottom: none; }
.stat-key { color: #6b7280; }
.stat-val { font-weight: 600; color: #1a1a2e; }
.info-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    border: 1px solid rgba(124,58,237,0.08);
    margin-bottom: 14px;
}
.info-card-title {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #9ca3af;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="hero-badge">⚡ Team CrossSense · Redrob AI Hackathon 2026</div>
    <h1>Intelligent Candidate Ranker</h1>
    <p>Upload any candidate pool and get AI-powered rankings in seconds.<br>
    9-signal scoring · BM25 + Semantic retrieval · Honeypot detection</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""<div class="step-card">
        <div class="step-icon">📂</div>
        <div class="step-title">Upload</div>
        <div class="step-desc">Drop any candidates JSON file — sample or full 100k pool (up to 2 GB)</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown("""<div class="step-card">
        <div class="step-icon">🧠</div>
        <div class="step-title">Analyze</div>
        <div class="step-desc">BM25 retrieval → semantic embeddings → 9-signal weighted scoring</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown("""<div class="step-card">
        <div class="step-icon">🏆</div>
        <div class="step-title">Rank</div>
        <div class="step-desc">Top 10 shortlist with per-candidate signal breakdown and reasoning</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload candidates file",
    type=["json", "jsonl", "gz"],
    label_visibility="collapsed"
)

if not uploaded_file:
    st.markdown("""
    <div class="signal-table" style="margin-top:8px">
        <div style="font-size:1.05rem;font-weight:700;color:#1a1a2e;margin-bottom:16px">
            📊 How candidates are scored — 9 signals
        </div>
        <div class="signal-row">
            <span class="signal-name">🎯 Skill Match — depth and relevance of skills vs JD</span>
            <span class="signal-weight">27%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">💼 Career Fit — title, domain, product company history</span>
            <span class="signal-weight">24%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">🔗 Semantic Similarity — sentence-transformer embedding match</span>
            <span class="signal-weight">15%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">📅 Experience Fit — JD wants 5–9 years</span>
            <span class="signal-weight">10%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">📍 Location Fit — India preferred, Pune/Noida/Hyderabad ideal</span>
            <span class="signal-weight">8%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">📈 Platform Demand — recruiter saves, search appearances</span>
            <span class="signal-weight">6%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">💻 GitHub Activity — open source contributions</span>
            <span class="signal-weight">5%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">🎓 Education — institution tier and field relevance</span>
            <span class="signal-weight">3%</span>
        </div>
        <div class="signal-row">
            <span class="signal-name">✅ Profile Quality — completeness, connections, acceptance rate</span>
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
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        import gzip
        fname = uploaded_file.name.lower()
        if fname.endswith('.gz'):
            candidates = []
            with gzip.open(tmp_path, 'rt', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        candidates.append(json.loads(line))
        elif fname.endswith('.jsonl'):
            candidates = []
            with open(tmp_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        candidates.append(json.loads(line))
        else:
            with open(tmp_path, 'r', encoding='utf-8') as f:
                candidates = json.load(f)
        from embedder import SemanticScorer

        BM25_K = 1500

        progress = st.progress(0, text="🔍 Loading and filtering candidates...")
        clean, honeypots = filter_honeypots(candidates, verbose=False)

        progress.progress(20, text="⚡ Stage 1 — BM25 retrieval...")
        try:
            from bm25_retriever import get_bm25_shortlist
            if len(clean) > BM25_K:
                bm25_results = get_bm25_shortlist(clean, top_k=BM25_K)
                shortlisted = [r["candidate"] for r in bm25_results]
            else:
                shortlisted = clean
        except ImportError:
            shortlisted = clean

        progress.progress(45, text="🧠 Stage 2 — Semantic embedding scoring (first run downloads ~90MB model)...")
        scorer_obj = SemanticScorer()
        sem_results = scorer_obj.score_candidates(shortlisted)
        semantic_scores = {
            r["candidate"]["candidate_id"]: r["semantic_score"]
            for r in sem_results
        }

        progress.progress(80, text="🏆 Stage 3 — Full feature scoring and ranking...")
        ranked = score_all(shortlisted, semantic_scores=semantic_scores)

        TOP_N = 10
        top = ranked[:TOP_N]
        lookup = {c["candidate_id"]: c for c in shortlisted}

        progress.progress(95, text="✍️ Generating reasoning...")
        reasonings = {}
        for i, r in enumerate(ranked[:100], 1):
            cid = r["candidate_id"]
            if cid in lookup:
                reasonings[cid] = generate_reasoning(lookup[cid], rank=i, score=r["score"])

        progress.progress(100, text="✅ Done!")
        progress.empty()

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
                <div class="metric-label">After BM25 Filter</div>
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

        st.markdown(f'<div class="section-header">🏆 Top {TOP_N} Candidates</div>', unsafe_allow_html=True)

        for i, r in enumerate(top, 1):
            cid = r["candidate_id"]
            c = lookup[cid]
            p = c["profile"]
            f = r["features"]
            reasoning = reasonings.get(cid, "")
            sem_score = semantic_scores.get(cid, 0.0)

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
                        <div style="font-size:0.75rem;color:#9ca3af;text-transform:uppercase;letter-spacing:1px">
                            Candidate ID
                        </div>
                        <div style="font-weight:700;color:#1a1a2e;font-size:1rem">{cid}</div>
                        <div style="color:#6b7280;font-size:0.85rem;margin-top:4px">{p.get('headline', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    signals = [
                        ("🎯 Skill Match",    f.get("skill_match", 0),    "linear-gradient(90deg,#7c3aed,#a855f7)"),
                        ("💼 Career Fit",      f.get("career_fit", 0),      "linear-gradient(90deg,#a855f7,#ec4899)"),
                        ("🔗 Semantic",        sem_score,                   "linear-gradient(90deg,#8b5cf6,#7c3aed)"),
                        ("📅 Experience",      f.get("experience_fit", 0),  "linear-gradient(90deg,#10b981,#34d399)"),
                        ("📍 Location",        f.get("location_fit", 0),    "linear-gradient(90deg,#3b82f6,#60a5fa)"),
                        ("📈 Platform Demand", f.get("platform_demand", 0), "linear-gradient(90deg,#f97316,#fb923c)"),
                        ("💻 GitHub",          f.get("github", 0),          "linear-gradient(90deg,#0f172a,#334155)"),
                        ("🎓 Education",       f.get("education", 0),       "linear-gradient(90deg,#0ea5e9,#38bdf8)"),
                        ("✅ Profile Quality", f.get("profile_quality", 0), "linear-gradient(90deg,#14b8a6,#2dd4bf)"),
                        ("⚡ Availability",    f.get("availability", 0),    "linear-gradient(90deg,#f59e0b,#fbbf24)"),
                    ]
                    for label, val, grad in signals:
                        pct = int(val * 100)
                        st.markdown(f"""
                        <div class="signal-label">
                            <span>{label}</span><span class="signal-val">{pct}%</span>
                        </div>
                        <div class="bar-track">
                            <div class="bar-fill" style="width:{pct}%;background:{grad}"></div>
                        </div>
                        """, unsafe_allow_html=True)

                with right:
                    st.markdown('<div class="info-card-title" style="margin-top:0">WHY THIS CANDIDATE</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="reasoning-box">{reasoning}</div>', unsafe_allow_html=True)

                    # Candidate stats
                    rs = c.get("redrob_signals", {})
                    yoe = p.get("years_of_experience", "—")
                    notice = rs.get("notice_period_days", "—")
                    last_active = rs.get("last_active_days", "—")
                    response_rate = rs.get("response_rate", None)
                    saved_30d = rs.get("saved_by_recruiters_30d", "—")
                    gh = c.get("github", {})
                    gh_stars = gh.get("total_stars", "—") if gh else "—"
                    gh_contribs = gh.get("contributions_last_year", "—") if gh else "—"
                    multiplier = r.get("multiplier", "—")
                    rr_display = f"{int(response_rate*100)}%" if response_rate is not None else "—"
                    notice_display = f"{notice}d" if notice != "—" else "—"
                    last_active_display = f"{last_active}d ago" if last_active != "—" else "—"

                    st.markdown(f"""
                    <div class="info-card">
                        <div class="info-card-title">CANDIDATE STATS</div>
                        <div class="stat-row"><span class="stat-key">Experience</span><span class="stat-val">{yoe} years</span></div>
                        <div class="stat-row"><span class="stat-key">Notice Period</span><span class="stat-val">{notice_display}</span></div>
                        <div class="stat-row"><span class="stat-key">Last Active</span><span class="stat-val">{last_active_display}</span></div>
                        <div class="stat-row"><span class="stat-key">Response Rate</span><span class="stat-val">{rr_display}</span></div>
                        <div class="stat-row"><span class="stat-key">Saved by Recruiters (30d)</span><span class="stat-val">{saved_30d}</span></div>
                    </div>
                    <div class="info-card">
                        <div class="info-card-title">GITHUB</div>
                        <div class="stat-row"><span class="stat-key">Stars</span><span class="stat-val">{gh_stars}</span></div>
                        <div class="stat-row"><span class="stat-key">Contributions (last year)</span><span class="stat-val">{gh_contribs}</span></div>
                    </div>
                    <div class="info-card">
                        <div class="info-card-title">PIPELINE SCORES</div>
                        <div class="stat-row"><span class="stat-key">Semantic Score</span><span class="stat-val">{sem_score:.3f}</span></div>
                        <div class="stat-row"><span class="stat-key">Availability Multiplier</span><span class="stat-val">{multiplier}</span></div>
                        <div class="stat-row"><span class="stat-key">Final Score</span><span class="stat-val">{r['score']:.4f}</span></div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="info-card-title" style="margin-top:4px">TOP SKILLS</div>', unsafe_allow_html=True)
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
                        bg, fg = colors.get(s.get("proficiency", "beginner"), ("f3f4f6", "6b7280"))
                        pills_html += (
                            f'<span class="skill-pill" style="background:#{bg};color:#{fg}">'
                            f'{s["name"]}</span>'
                        )
                    st.markdown(pills_html, unsafe_allow_html=True)

        import csv, io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        for i, r in enumerate(ranked[:100], 1):
            cid = r["candidate_id"]
            if cid in lookup:
                writer.writerow({
                    "candidate_id": cid,
                    "rank": i,
                    "score": round(r["score"], 6),
                    "reasoning": reasonings.get(cid, "")
                })

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="⬇️ Download submission.csv",
            data=output.getvalue(),
            file_name="submission.csv",
            mime="text/csv",
            use_container_width=True
        )
        os.unlink(tmp_path)

    except Exception as e:
        st.error(f"Error: {e}")
        raise e