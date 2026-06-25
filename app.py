import streamlit as st
import json
import tempfile
import os
import sys
import gzip
from pathlib import Path

# Handle both src/ and root structure
_root = Path(__file__).parent
for _p in [_root / "src", _root]:
    if (_p / "loader.py").exists():
        sys.path.insert(0, str(_p))
        break

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
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #f5f4f7; color: #1a1a2e; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
header {visibility: hidden;}

.hero {
    background: linear-gradient(135deg, #6d28d9 0%, #9333ea 50%, #db2777 100%);
    border-radius: 20px;
    padding: 52px 48px 44px;
    margin-bottom: 28px;
    text-align: center;
    box-shadow: 0 8px 40px rgba(109,40,217,0.22);
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.28);
    border-radius: 30px;
    padding: 5px 18px;
    font-size: 0.78rem;
    font-weight: 600;
    color: #fff;
    letter-spacing: 0.5px;
    margin-bottom: 18px;
    text-transform: uppercase;
}
.hero h1 {
    font-size: 2.6rem;
    font-weight: 800;
    color: #fff;
    margin: 0 0 10px 0;
    letter-spacing: -0.5px;
    line-height: 1.15;
}
.hero p {
    color: rgba(255,255,255,0.82);
    font-size: 0.97rem;
    margin: 0;
    line-height: 1.7;
}
.step-card {
    background: #fff;
    border-radius: 14px;
    padding: 26px 22px;
    text-align: center;
    box-shadow: 0 2px 16px rgba(0,0,0,0.06);
    border: 1px solid #ede9fe;
    height: 100%;
}
.step-icon { font-size: 1.9rem; margin-bottom: 10px; }
.step-title { font-size: 0.92rem; font-weight: 700; color: #1a1a2e; margin-bottom: 6px; }
.step-desc { font-size: 0.78rem; color: #6b7280; line-height: 1.55; }
.metric-card {
    background: #fff;
    border-radius: 14px;
    padding: 20px 14px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    border: 1px solid #ede9fe;
}
.metric-value {
    font-size: 1.9rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6d28d9, #db2777);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.1;
}
.metric-label {
    font-size: 0.68rem;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-top: 5px;
    font-weight: 600;
}
.section-header {
    font-size: 1.2rem;
    font-weight: 700;
    color: #1a1a2e;
    margin: 28px 0 14px 0;
    letter-spacing: -0.2px;
}
.signal-row-wrap { margin-bottom: 11px; }
.signal-top {
    display: flex;
    justify-content: space-between;
    font-size: 0.77rem;
    color: #6b7280;
    margin-bottom: 4px;
    font-weight: 500;
}
.signal-pct { font-weight: 700; color: #1a1a2e; }
.bar-track {
    background: #f0ebff;
    border-radius: 6px;
    height: 7px;
    overflow: hidden;
}
.bar-fill { height: 7px; border-radius: 6px; }
.reasoning-box {
    background: #faf5ff;
    border-left: 4px solid #9333ea;
    border-radius: 0 10px 10px 0;
    padding: 14px 16px;
    font-size: 0.84rem;
    color: #374151;
    line-height: 1.65;
    margin-bottom: 16px;
}
.reasoning-label {
    font-size: 0.66rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #9ca3af;
    margin-bottom: 8px;
}
.stat-box {
    background: #fff;
    border-radius: 12px;
    padding: 14px 16px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    border: 1px solid #ede9fe;
    margin-bottom: 12px;
}
.stat-box-title {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #9ca3af;
    margin-bottom: 10px;
}
.stat-row {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid #f9f5ff;
    font-size: 0.81rem;
}
.stat-row:last-child { border-bottom: none; }
.stat-key { color: #6b7280; }
.stat-val { font-weight: 600; color: #1a1a2e; }
.skill-pill {
    display: inline-block;
    border-radius: 20px;
    padding: 3px 11px;
    font-size: 0.73rem;
    font-weight: 500;
    margin: 3px 3px 3px 0;
}
.skill-section-title {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #9ca3af;
    margin: 12px 0 8px 0;
}
.cand-id-block {
    background: #faf5ff;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 16px;
    border: 1px solid #ede9fe;
}
.cand-id-label {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #9ca3af;
    margin-bottom: 4px;
}
.cand-id-val {
    font-weight: 800;
    color: #6d28d9;
    font-size: 0.95rem;
    font-family: monospace;
}
.cand-headline {
    color: #6b7280;
    font-size: 0.8rem;
    margin-top: 4px;
    line-height: 1.4;
}
.signal-table {
    background: #fff;
    border-radius: 16px;
    padding: 26px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.05);
    border: 1px solid #ede9fe;
}
.signal-table-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 11px 0;
    border-bottom: 1px solid #f5f0ff;
}
.signal-table-row:last-child { border-bottom: none; }
.signal-table-name { color: #374151; font-size: 0.87rem; }
.signal-table-wt {
    font-weight: 700;
    font-size: 0.87rem;
    background: linear-gradient(135deg, #6d28d9, #db2777);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    min-width: 60px;
    text-align: right;
}
.sem-note {
    background: #fff;
    border: 1px solid #ede9fe;
    border-left: 4px solid #9333ea;
    border-radius: 0 10px 10px 0;
    padding: 12px 16px;
    font-size: 0.81rem;
    color: #6b7280;
    line-height: 1.6;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">Team CrossSense &nbsp;·&nbsp; Redrob AI Hackathon 2026</div>
    <h1>Intelligent Candidate Ranker</h1>
    <p>
        Upload any candidate pool and receive ranked shortlists in seconds.<br>
        9-signal scoring &nbsp;·&nbsp; BM25 retrieval &nbsp;·&nbsp;
        Honeypot detection &nbsp;·&nbsp; Per-candidate reasoning
    </p>
</div>
""", unsafe_allow_html=True)

# ── Step cards ────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    st.markdown("""<div class="step-card">
        <div class="step-icon">📂</div>
        <div class="step-title">Upload</div>
        <div class="step-desc">Accepts .json, .jsonl, or .gz candidate pool files</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown("""<div class="step-card">
        <div class="step-icon">🧠</div>
        <div class="step-title">Analyze</div>
        <div class="step-desc">BM25 text retrieval followed by 9-signal weighted behavioral scoring</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown("""<div class="step-card">
        <div class="step-icon">🏆</div>
        <div class="step-title">Shortlist</div>
        <div class="step-desc">Top candidates with signal breakdown, reasoning, and downloadable CSV</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload candidates file",
    type=["json", "jsonl", "gz"],
    label_visibility="collapsed"
)

if not uploaded_file:
    col_l, col_r = st.columns([3, 2], gap="large")
    with col_l:
        st.markdown("""
        <div class="signal-table">
            <div style="font-size:0.95rem;font-weight:700;color:#1a1a2e;
                        margin-bottom:16px;letter-spacing:-0.2px">
                Scoring System — 9 Signals + Availability Multiplier
            </div>
            <div class="signal-table-row">
                <span class="signal-table-name">🎯 Skill Match — proficiency, endorsements, duration, assessments</span>
                <span class="signal-table-wt">27%</span>
            </div>
            <div class="signal-table-row">
                <span class="signal-table-name">💼 Career Trajectory — title, domain, product company, consulting penalty</span>
                <span class="signal-table-wt">24%</span>
            </div>
            <div class="signal-table-row">
                <span class="signal-table-name">🔗 Semantic JD Match — sentence-transformer cosine similarity</span>
                <span class="signal-table-wt">15%</span>
            </div>
            <div class="signal-table-row">
                <span class="signal-table-name">📅 Experience Fit — JD requires 5–9 years, sweet spot 6–8</span>
                <span class="signal-table-wt">10%</span>
            </div>
            <div class="signal-table-row">
                <span class="signal-table-name">📍 Location Fit — India preferred, Pune and Noida ideal</span>
                <span class="signal-table-wt">8%</span>
            </div>
            <div class="signal-table-row">
                <span class="signal-table-name">📈 Platform Demand — recruiter saves, search appearances</span>
                <span class="signal-table-wt">6%</span>
            </div>
            <div class="signal-table-row">
                <span class="signal-table-name">💻 GitHub Activity — open source contribution score</span>
                <span class="signal-table-wt">5%</span>
            </div>
            <div class="signal-table-row">
                <span class="signal-table-name">🎓 Education Quality — institution tier and field relevance</span>
                <span class="signal-table-wt">3%</span>
            </div>
            <div class="signal-table-row">
                <span class="signal-table-name">✅ Profile Quality — connections, LinkedIn, interview rate</span>
                <span class="signal-table-wt">2%</span>
            </div>
            <div class="signal-table-row">
                <span class="signal-table-name">⚡ Availability — last active, response rate, notice period</span>
                <span class="signal-table-wt">× multiplier</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_r:
        st.markdown("""
        <div class="stat-box" style="margin-bottom:14px">
            <div class="stat-box-title">Availability Multiplier</div>
            <p style="font-size:0.81rem;color:#6b7280;line-height:1.65;margin:0">
                Availability is not a direct signal weight — it scales the entire
                base score up or down.<br><br>
                <strong style="color:#1a1a2e">Formula:</strong><br>
                Final = Base × (0.40 + 0.60 × availability)<br><br>
                A technically perfect candidate who never responds to recruiters
                scores 40% of their potential. The 0.40 floor ensures they are
                never completely zeroed out.
            </p>
        </div>
        <div class="stat-box" style="margin-bottom:14px">
            <div class="stat-box-title">Semantic JD Match</div>
            <p style="font-size:0.81rem;color:#6b7280;line-height:1.65;margin:0">
                Uses <strong style="color:#1a1a2e">sentence-transformers
                all-MiniLM-L6-v2</strong> to encode the full JD and each
                candidate profile into 384-dimensional vectors. Cosine similarity
                captures meaning-level alignment — "Information Retrieval
                Engineer" and "Search Systems Engineer" score high similarity
                even without shared keywords.
            </p>
        </div>
        <div class="stat-box">
            <div class="stat-box-title">Honeypot Detection</div>
            <p style="font-size:0.81rem;color:#6b7280;line-height:1.65;margin:0">
                Profiles with impossible data are removed before scoring.
                Expert skill with zero months of usage, claimed experience
                exceeding career history by 3+ years, or signal values outside
                valid ranges.
            </p>
        </div>
        <p style="color:#9ca3af;font-size:0.77rem;text-align:center;
                   margin-top:14px">
            Upload <code>sample_candidates.json</code> to get started
        </p>
        """, unsafe_allow_html=True)

else:
    try:
        fname = uploaded_file.name.lower()
        suffix = (".gz" if fname.endswith(".gz") else
                  ".jsonl" if fname.endswith(".jsonl") else ".json")

        with tempfile.NamedTemporaryFile(
                mode='wb', suffix=suffix, delete=False) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

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

        BM25_K = 200

        progress = st.progress(0, text="Scanning and filtering candidates...")
        clean, honeypots = filter_honeypots(candidates, verbose=False)

        progress.progress(30, text="Stage 1 — BM25 text retrieval...")
        try:
            from bm25_retriever import get_bm25_shortlist
            if len(clean) > BM25_K:
                bm25_results = get_bm25_shortlist(clean, top_k=BM25_K)
                shortlisted = [r["candidate"] for r in bm25_results]
            else:
                shortlisted = clean
        except Exception:
            shortlisted = clean

        progress.progress(70, text="Stage 2 — Scoring all 9 signals...")
        # On cloud, semantic=0 but scorer redistributes weights to keep total=100%
        ranked = score_all(shortlisted, semantic_scores={})

        TOP_N = min(10, len(ranked))
        top = ranked[:TOP_N]
        lookup = {c["candidate_id"]: c for c in shortlisted}

        progress.progress(90, text="Generating reasoning...")
        reasonings = {}
        for i, r in enumerate(ranked[:100], 1):
            cid = r["candidate_id"]
            if cid in lookup:
                reasonings[cid] = generate_reasoning(
                    lookup[cid], rank=i, score=r["score"]
                )

        progress.progress(100, text="Complete.")
        progress.empty()

        # Semantic note
        st.markdown("""
        <div class="sem-note">
            <strong style="color:#6d28d9">Sandbox mode:</strong>
            Semantic JD matching (15% weight, sentence-transformers) requires
            a local environment with PyTorch. On this cloud sandbox, that weight
            is redistributed proportionally across the remaining 8 signals so
            scores remain comparable. For full 9-signal rankings run
            <code>python src/rank.py --candidates candidates.jsonl</code> locally.
        </div>
        """, unsafe_allow_html=True)

        # Metrics
        m1, m2, m3, m4, m5 = st.columns(5, gap="small")
        for col, val, label in [
            (m1, len(candidates),  "Total Candidates"),
            (m2, len(honeypots),   "Honeypots Removed"),
            (m3, len(shortlisted), "BM25 Shortlist"),
            (m4, len(ranked),      "Ranked"),
            (m5, f"{top[0]['score']:.3f}" if top else "—", "Top Score"),
        ]:
            with col:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-value">{val}</div>
                    <div class="metric-label">{label}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown(
            f'<div class="section-header">Top {TOP_N} Candidates</div>',
            unsafe_allow_html=True
        )

        # Candidate cards — NOT auto-expanded
        for i, r in enumerate(top, 1):
            cid  = r["candidate_id"]
            c    = lookup[cid]
            p    = c["profile"]
            f    = r["features"]
            rs   = c.get("redrob_signals", {})
            rsn  = reasonings.get(cid, "")
            avail_pct = int(f.get("availability", 0) * 100)

            with st.expander(
                f"#{i}  ·  {p['current_title']} @ {p['current_company']}"
                f"  ·  {p['years_of_experience']}y exp"
                f"  ·  {p['location']}, {p['country']}"
                f"  ·  Score: {r['score']:.4f}"
            ):
                left, right = st.columns([11, 10], gap="large")

                with left:
                    st.markdown(f"""
                    <div class="cand-id-block">
                        <div class="cand-id-label">Candidate ID</div>
                        <div class="cand-id-val">{cid}</div>
                        <div class="cand-headline">{p.get('headline','')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 8 signal bars (semantic excluded in cloud mode)
                    signals = [
                        ("🎯 Skill Match",
                         f.get("skill_match",0),
                         "linear-gradient(90deg,#6d28d9,#9333ea)"),
                        ("💼 Career Trajectory",
                         f.get("career_fit",0),
                         "linear-gradient(90deg,#9333ea,#db2777)"),
                        ("📅 Experience Fit",
                         f.get("experience_fit",0),
                         "linear-gradient(90deg,#059669,#34d399)"),
                        ("📍 Location Fit",
                         f.get("location_fit",0),
                         "linear-gradient(90deg,#2563eb,#60a5fa)"),
                        ("📈 Platform Demand",
                         f.get("platform_demand",0),
                         "linear-gradient(90deg,#ea580c,#fb923c)"),
                        ("💻 GitHub Activity",
                         f.get("github",0),
                         "linear-gradient(90deg,#334155,#64748b)"),
                        ("🎓 Education Quality",
                         f.get("education",0),
                         "linear-gradient(90deg,#0284c7,#38bdf8)"),
                        ("✅ Profile Quality",
                         f.get("profile_quality",0),
                         "linear-gradient(90deg,#0d9488,#2dd4bf)"),
                        ("⚡ Availability",
                         f.get("availability",0),
                         "linear-gradient(90deg,#d97706,#fbbf24)"),
                    ]

                    bars_html = ""
                    for label, val, grad in signals:
                        pct = int(val * 100)
                        bars_html += f"""
                        <div class="signal-row-wrap">
                            <div class="signal-top">
                                <span>{label}</span>
                                <span class="signal-pct">{pct}%</span>
                            </div>
                            <div class="bar-track">
                                <div class="bar-fill"
                                     style="width:{pct}%;background:{grad}">
                                </div>
                            </div>
                        </div>"""
                    st.markdown(bars_html, unsafe_allow_html=True)

                with right:
                    st.markdown(f"""
                    <div class="reasoning-label">Recruiter Reasoning</div>
                    <div class="reasoning-box">{rsn}</div>
                    """, unsafe_allow_html=True)

                    notice  = rs.get("notice_period_days", "—")
                    rrr     = rs.get("recruiter_response_rate", None)
                    saved   = rs.get("saved_by_recruiters_30d", "—")
                    la      = rs.get("last_active_date", "—")
                    otw     = rs.get("open_to_work_flag", False)
                    gh      = rs.get("github_activity_score", -1)
                    conns   = rs.get("connection_count", "—")
                    icr     = rs.get("interview_completion_rate", "—")

                    rrr_s    = f"{int(rrr*100)}%" if rrr is not None else "—"
                    notice_s = f"{notice} days" if notice != "—" else "—"
                    gh_s     = str(int(gh)) if gh != -1 else "Not linked"
                    otw_s    = "Open to work" if otw else "Not seeking"
                    icr_s    = f"{int(icr*100)}%" if isinstance(icr,float) else "—"

                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-box-title">Candidate Profile</div>
                        <div class="stat-row">
                            <span class="stat-key">Status</span>
                            <span class="stat-val">{otw_s}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Notice Period</span>
                            <span class="stat-val">{notice_s}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Last Active</span>
                            <span class="stat-val">{la}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Recruiter Response Rate</span>
                            <span class="stat-val">{rrr_s}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Saved by Recruiters (30d)</span>
                            <span class="stat-val">{saved}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Connections</span>
                            <span class="stat-val">{conns}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Interview Completion</span>
                            <span class="stat-val">{icr_s}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">GitHub Score</span>
                            <span class="stat-val">{gh_s}</span>
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-box-title">Score Breakdown</div>
                        <div class="stat-row">
                            <span class="stat-key">Availability %</span>
                            <span class="stat-val">{avail_pct}%</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Availability Multiplier</span>
                            <span class="stat-val">{r.get('multiplier',0):.3f}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-key">Final Score</span>
                            <span class="stat-val"
                                  style="color:#6d28d9;font-size:0.95rem;
                                         font-weight:800">
                                {r['score']:.4f}
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(
                        '<div class="skill-section-title">Top Skills</div>',
                        unsafe_allow_html=True
                    )
                    skills = sorted(
                        c.get("skills", []),
                        key=lambda s: s.get("endorsements", 0),
                        reverse=True
                    )[:9]
                    pills = ""
                    for s in skills:
                        clr = {
                            "expert":       ("ede9fe","6d28d9"),
                            "advanced":     ("fce7f3","be185d"),
                            "intermediate": ("d1fae5","065f46"),
                            "beginner":     ("f3f4f6","6b7280")
                        }.get(s.get("proficiency","beginner"),
                              ("f3f4f6","6b7280"))
                        pills += (
                            f'<span class="skill-pill" '
                            f'style="background:#{clr[0]};color:#{clr[1]}">'
                            f'{s["name"]}</span>'
                        )
                    st.markdown(pills, unsafe_allow_html=True)

        # Download
        import csv, io as _io
        out = _io.StringIO()
        writer = csv.DictWriter(
            out, fieldnames=["candidate_id","rank","score","reasoning"]
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
            label="Download submission.csv",
            data=out.getvalue(),
            file_name="submission.csv",
            mime="text/csv",
            use_container_width=True
        )
        os.unlink(tmp_path)

    except Exception as e:
        st.error(f"Error: {e}")
        st.exception(e)