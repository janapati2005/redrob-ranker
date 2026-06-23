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

/* Hide streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
header {visibility: hidden;}

/* Hero */
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

/* Step cards */
.step-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 1px solid rgba(124,58,237,0.08);
    height: 100%;
    transition: transform 0.2s, box-shadow 0.2s;
}
.step-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(124,58,237,0.12);
}
.step-icon {
    font-size: 2.2rem;
    margin-bottom: 12px;
}
.step-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1a1a2e;
    margin-bottom: 8px;
}
.step-desc {
    font-size: 0.83rem;
    color: #6b7280;
    line-height: 1.5;
}

/* Metric cards */
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

/* Section header */
.section-header {
    font-size: 1.4rem;
    font-weight: 700;
    color: #1a1a2e;
    margin: 32px 0 16px 0;
}

/* Candidate card */
.cand-header {
    display: flex;
    align-items: center;
    gap: 12px;
}
.rank-circle {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.9rem;
    flex-shrink: 0;
}
.rank-1 { background: linear-gradient(135deg, #f59e0b, #f97316); color: #fff; }
.rank-2 { background: linear-gradient(135deg, #94a3b8, #64748b); color: #fff; }
.rank-3 { background: linear-gradient(135deg, #b45309, #92400e); color: #fff; }
.rank-n { background: linear-gradient(135deg, #ede9fe, #ddd6fe); color: #7c3aed; }

/* Signal bars */
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
.bar-fill {
    height: 7px;
    border-radius: 6px;
}

/* Reasoning */
.reasoning-box {
    background: linear-gradient(135deg, #faf5ff, #fdf2f8);
    border-left: 4px solid #a855f7;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    font-size: 0.88rem;
    color: #374151;
    line-height: 1.6;
}

/* Skill pill */
.skill-pill {
    display: inline-block;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.76rem;
    font-weight: 500;
    margin: 3px 3px 3px 0;
}

/* Signal table */
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
    9-signal scoring · Honeypot detection · Behavioral availability analysis</p>
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
        <div class="step-desc">9-signal scoring across skills, career, experience, GitHub, platform demand, education & more</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown("""<div class="step-card">
        <div class="step-icon">🏆</div>
        <div class="step-title">Rank</div>
        <div class="step-desc">Get your shortlist with per-candidate reasoning — ready to submit</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── File Upload ───────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload candidates JSON file",
    type=["json"],
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
            <span class="signal-name">🔗 Semantic Similarity — embedding match against JD</span>
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

        with open(tmp_path, 'r', encoding='utf-8') as f:
            candidates = json.load(f)

        progress = st.progress(0, text="🔍 Loading candidates...")
        clean, honeypots = filter_honeypots(candidates, verbose=False)
        progress.progress(40, text="⚡ Scoring candidates...")
        ranked = score_all(clean)
        progress.progress(80, text="✍️ Generating reasoning...")
        top_n = min(len(ranked), 20)
        top = ranked[:top_n]
        lookup = {c["candidate_id"]: c for c in clean}
        progress.progress(100, text="✅ Done!")
        progress.empty()

        # ── Metrics ────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
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
                <div class="metric-value">{len(ranked)}</div>
                <div class="metric-label">Candidates Ranked</div>
            </div>""", unsafe_allow_html=True)
        with m4:
            top_score = top[0]["score"] if top else 0
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{top_score:.3f}</div>
                <div class="metric-label">Top Score</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="section-header">🏆 Top {top_n} Candidates</div>
        """, unsafe_allow_html=True)

        # ── Candidate cards ────────────────────────────────────────────────
        for i, r in enumerate(top, 1):
            cid = r["candidate_id"]
            c = lookup[cid]
            p = c["profile"]
            f = r["features"]
            reasoning = generate_reasoning(c, rank=i, score=r["score"])

            rank_class = (
                "rank-1" if i == 1 else
                "rank-2" if i == 2 else
                "rank-3" if i == 3 else
                "rank-n"
            )

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

                    # All 9 signals + availability multiplier
                    signals = [
                        ("🎯 Skill Match",       f.get("skill_match", 0),       "linear-gradient(90deg,#7c3aed,#a855f7)"),
                        ("💼 Career Fit",         f.get("career_fit", 0),         "linear-gradient(90deg,#a855f7,#ec4899)"),
                        ("🔗 Semantic",           f.get("semantic", 0),           "linear-gradient(90deg,#8b5cf6,#7c3aed)"),
                        ("📅 Experience",         f.get("experience_fit", 0),     "linear-gradient(90deg,#10b981,#34d399)"),
                        ("📍 Location",           f.get("location_fit", 0),       "linear-gradient(90deg,#3b82f6,#60a5fa)"),
                        ("📈 Platform Demand",    f.get("platform_demand", 0),    "linear-gradient(90deg,#f97316,#fb923c)"),
                        ("💻 GitHub",             f.get("github", 0),             "linear-gradient(90deg,#0f172a,#334155)"),
                        ("🎓 Education",          f.get("education", 0),          "linear-gradient(90deg,#0ea5e9,#38bdf8)"),
                        ("✅ Profile Quality",    f.get("profile_quality", 0),    "linear-gradient(90deg,#14b8a6,#2dd4bf)"),
                        ("⚡ Availability",       f.get("availability", 0),       "linear-gradient(90deg,#f59e0b,#fbbf24)"),
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
                    st.markdown("""
                    <div style="font-size:0.75rem;color:#9ca3af;
                                text-transform:uppercase;letter-spacing:1px;
                                margin-bottom:8px">
                        Why this candidate
                    </div>""", unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="reasoning-box">{reasoning}</div>',
                        unsafe_allow_html=True
                    )

                    st.markdown("""
                    <div style="font-size:0.75rem;color:#9ca3af;
                                text-transform:uppercase;letter-spacing:1px;
                                margin:16px 0 8px 0">
                        Top Skills
                    </div>""", unsafe_allow_html=True)

                    skills = sorted(
                        c.get("skills", []),
                        key=lambda s: s.get("endorsements", 0),
                        reverse=True
                    )[:6]

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

        # ── Download ───────────────────────────────────────────────────────
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
                c = lookup[cid]
                reasoning = generate_reasoning(c, rank=i, score=r["score"])
                writer.writerow({
                    "candidate_id": cid,
                    "rank": i,
                    "score": round(r["score"], 6),
                    "reasoning": reasoning
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