import streamlit as st
import pandas as pd
from datetime import date

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Geiger Performance Pulse",
    page_icon="⚡",
    layout="wide",
)

# ── GPP Custom CSS (ESPN-style) ───────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;700&family=Open+Sans:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Open Sans', sans-serif;
}

/* ── Header banner ── */
.gpp-header {
    background: #cc0000;
    padding: 14px 24px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
}
.gpp-logo {
    background: white;
    color: #cc0000;
    font-family: 'Oswald', sans-serif;
    font-size: 26px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 4px;
    letter-spacing: 1px;
}
.gpp-title {
    color: white;
    font-family: 'Oswald', sans-serif;
    font-size: 18px;
    font-weight: 500;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.gpp-sub {
    color: rgba(255,255,255,0.75);
    font-size: 12px;
    margin-top: 2px;
}

/* ── Summary metric cards ── */
.metric-card {
    padding: 16px 20px;
    border-radius: 8px;
    border-top: 4px solid;
    background: white;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.metric-card.green  { border-color: #00c853; }
.metric-card.yellow { border-color: #ffd600; }
.metric-card.red    { border-color: #ff1744; }
.metric-card.blue   { border-color: #2979ff; }
.metric-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 4px; }
.metric-value { font-family: 'Oswald', sans-serif; font-size: 42px; font-weight: 700; line-height: 1; }
.metric-value.green  { color: #00c853; }
.metric-value.yellow { color: #e6b800; }
.metric-value.red    { color: #ff1744; }
.metric-value.blue   { color: #2979ff; }
.metric-sub { font-size: 12px; color: #aaa; margin-top: 4px; }

/* ── Injury alert banner ── */
.injury-alert {
    background: #fff0f0;
    border: 1px solid #ffcccc;
    border-left: 5px solid #ff1744;
    border-radius: 6px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 700;
    color: #cc0000;
    margin-bottom: 16px;
}

/* ── Status chips ── */
.chip {
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.chip-ready    { background: #e6f9ee; color: #007a30; }
.chip-moderate { background: #fff9e0; color: #7a6000; }
.chip-notready { background: #fff0f0; color: #cc0000; }
.chip-highrisk { background: #fff0f0; color: #cc0000; }
.chip-lowrisk  { background: #e6f9ee; color: #007a30; }
.chip-train    { background: #e6f9ee; color: #007a30; border-radius: 12px; }
.chip-rest     { background: #fff9e0; color: #7a6000; border-radius: 12px; }
.chip-bench    { background: #fff0f0; color: #cc0000; border-radius: 12px; }

/* ── Section headers ── */
.section-header {
    font-family: 'Oswald', sans-serif;
    font-size: 13px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #888;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 6px;
    margin: 24px 0 14px 0;
}

/* ── Alert cards ── */
.alert-card {
    background: white;
    border-radius: 8px;
    border: 1px solid #eee;
    border-left: 4px solid;
    padding: 12px 16px;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.alert-card.high { border-left-color: #ff1744; }
.alert-card.mod  { border-left-color: #ffd600; }
.alert-card.low  { border-left-color: #00c853; }
.alert-name  { font-family: 'Oswald', sans-serif; font-size: 16px; font-weight: 700; }
.alert-meta  { font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }
.alert-score { font-family: 'Oswald', sans-serif; font-size: 32px; font-weight: 700; }
.score-ready { color: #00c853; }
.score-mod   { color: #e6b800; }
.score-not   { color: #ff1744; }

/* ── Streamlit overrides ── */
div[data-testid="stExpander"] { border: 1px solid #eee !important; border-radius: 8px !important; }
.stDataFrame { border-radius: 8px; overflow: hidden; }
div[data-testid="metric-container"] { background: white; border-radius: 8px; padding: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.07); }
</style>
""", unsafe_allow_html=True)


# ── Helper functions ──────────────────────────────────────────────────────────
def calc_readiness(sleep, soreness, fatigue):
    return round((10 - fatigue) + (10 - soreness) + sleep, 1)

def get_status(score):
    if score >= 19: return "Ready"
    if score >= 11: return "Moderate"
    return "Not Ready"

def get_risk(sleep, soreness, fatigue):
    return "High Risk" if (fatigue >= 7 or soreness >= 7 or sleep < 6) else "Low Risk"

def get_recommendation(status, risk):
    if status == "Not Ready" or risk == "High Risk": return "Bench"
    if status == "Moderate": return "Rest"
    return "Train"

def status_chip(status):
    mapping = {
        "Ready":     '<span class="chip chip-ready">Ready</span>',
        "Moderate":  '<span class="chip chip-moderate">Moderate</span>',
        "Not Ready": '<span class="chip chip-notready">Not Ready</span>',
    }
    return mapping.get(status, status)

def risk_chip(risk):
    if risk == "High Risk":
        return '<span class="chip chip-highrisk">⚠ High Risk</span>'
    return '<span class="chip chip-lowrisk">✓ Low Risk</span>'

def rec_chip(rec):
    mapping = {
        "Train": '<span class="chip chip-train">▶ Train</span>',
        "Rest":  '<span class="chip chip-rest">◎ Rest</span>',
        "Bench": '<span class="chip chip-bench">✕ Bench</span>',
    }
    return mapping.get(rec, rec)

def score_color(status):
    return {"Ready": "#00c853", "Moderate": "#e6b800", "Not Ready": "#ff1744"}.get(status, "#888")

def bar_html(value, max_val=10, invert=False):
    pct = int((value / max_val) * 100)
    if invert:
        color = "#ff1744" if pct >= 70 else "#ffd600" if pct >= 40 else "#00c853"
    else:
        color = "#00c853" if pct >= 70 else "#ffd600" if pct >= 40 else "#ff1744"
    return f"""
    <div style="display:flex;align-items:center;gap:8px;">
        <div style="flex:1;height:8px;background:#f0f0f0;border-radius:4px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:{color};border-radius:4px;"></div>
        </div>
        <span style="font-size:12px;font-weight:700;min-width:28px;">{value}</span>
    </div>"""


# ── Session state for player data ─────────────────────────────────────────────
if "player_data" not in st.session_state:
    st.session_state.player_data = pd.DataFrame([
        {"Date": "3/1/2026", "Name": "Mike Smith",      "Hours Slept": 7, "Soreness": 5, "Fatigue": 6, "Position": "Guard",   "Starter": "Y"},
        {"Date": "3/1/2026", "Name": "Chris Johnson",   "Hours Slept": 8, "Soreness": 4, "Fatigue": 5, "Position": "Guard",   "Starter": "Y"},
        {"Date": "3/1/2026", "Name": "David Brown",     "Hours Slept": 5, "Soreness": 8, "Fatigue": 7, "Position": "Forward", "Starter": "Y"},
        {"Date": "3/1/2026", "Name": "James Wilson",    "Hours Slept": 6, "Soreness": 6, "Fatigue": 6, "Position": "Forward", "Starter": "Y"},
        {"Date": "3/1/2026", "Name": "Alex Martinez",   "Hours Slept": 9, "Soreness": 3, "Fatigue": 4, "Position": "Center",  "Starter": "Y"},
        {"Date": "3/1/2026", "Name": "Jordan Davis",    "Hours Slept": 4, "Soreness": 9, "Fatigue": 8, "Position": "Guard",   "Starter": "N"},
        {"Date": "3/1/2026", "Name": "Kevin White",     "Hours Slept": 7, "Soreness": 5, "Fatigue": 5, "Position": "Guard",   "Starter": "N"},
        {"Date": "3/1/2026", "Name": "Brian Taylor",    "Hours Slept": 6, "Soreness": 7, "Fatigue": 7, "Position": "Forward", "Starter": "N"},
        {"Date": "3/1/2026", "Name": "Eric Anderson",   "Hours Slept": 8, "Soreness": 4, "Fatigue": 5, "Position": "Forward", "Starter": "N"},
        {"Date": "3/1/2026", "Name": "Marcus Thomas",   "Hours Slept": 5, "Soreness": 8, "Fatigue": 9, "Position": "Center",  "Starter": "N"},
        {"Date": "3/1/2026", "Name": "Anthony Jackson", "Hours Slept": 7, "Soreness": 6, "Fatigue": 6, "Position": "Guard",   "Starter": "N"},
        {"Date": "3/1/2026", "Name": "Tyler Harris",    "Hours Slept": 6, "Soreness": 7, "Fatigue": 7, "Position": "Forward", "Starter": "N"},
        {"Date": "3/1/2026", "Name": "Brandon Clark",   "Hours Slept": 8, "Soreness": 3, "Fatigue": 4, "Position": "Guard",   "Starter": "N"},
        {"Date": "3/1/2026", "Name": "Justin Lewis",    "Hours Slept": 5, "Soreness": 9, "Fatigue": 8, "Position": "Forward", "Starter": "N"},
        {"Date": "3/1/2026", "Name": "Ryan Walker",     "Hours Slept": 7, "Soreness": 5, "Fatigue": 6, "Position": "Center",  "Starter": "N"},
    ])


# ── Compute derived columns ───────────────────────────────────────────────────
df = st.session_state.player_data.copy()
df["Readiness Score"] = df.apply(lambda r: calc_readiness(r["Hours Slept"], r["Soreness"], r["Fatigue"]), axis=1)
df["Status"]          = df["Readiness Score"].apply(get_status)
df["Injury Risk"]     = df.apply(lambda r: get_risk(r["Hours Slept"], r["Soreness"], r["Fatigue"]), axis=1)
df["Recommendation"]  = df.apply(lambda r: get_recommendation(r["Status"], r["Injury Risk"]), axis=1)


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="gpp-header">
    <div class="gpp-logo">GPP</div>
    <div>
        <div class="gpp-title">Geiger Performance Pulse</div>
        <div class="gpp-sub">Team Recovery Dashboard — Live Status</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY CARDS
# ══════════════════════════════════════════════════════════════════════════════
ready_n    = len(df[df["Status"] == "Ready"])
mod_n      = len(df[df["Status"] == "Moderate"])
not_n      = len(df[df["Status"] == "Not Ready"])
highrisk_n = len(df[df["Injury Risk"] == "High Risk"])

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card green">
        <div class="metric-label">Ready to Train</div>
        <div class="metric-value green">{ready_n}</div>
        <div class="metric-sub">players cleared</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card yellow">
        <div class="metric-label">Moderate Status</div>
        <div class="metric-value yellow">{mod_n}</div>
        <div class="metric-sub">limited activity</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card red">
        <div class="metric-label">Not Ready</div>
        <div class="metric-value red">{not_n}</div>
        <div class="metric-sub">do not play</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card blue">
        <div class="metric-label">High Injury Risk</div>
        <div class="metric-value blue">{highrisk_n}</div>
        <div class="metric-sub">need attention</div>
    </div>""", unsafe_allow_html=True)


# ── Injury alert banner ───────────────────────────────────────────────────────
flagged_starters = df[(df["Injury Risk"] == "High Risk") & (df["Starter"] == "Y")]
if not flagged_starters.empty:
    names = ", ".join(flagged_starters["Name"].tolist())
    st.markdown(f"""<div class="injury-alert">
        ⚠ INJURY ALERT: {len(flagged_starters)} starter(s) flagged as High Risk — {names}
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DAILY DATA ENTRY FORM
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">➕ Add / Update Daily Entry</div>', unsafe_allow_html=True)

with st.expander("Open Data Entry Form", expanded=False):
    with st.form("entry_form", clear_on_submit=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            entry_date = st.date_input("Date", value=date.today())
            entry_name = st.text_input("Player Name", placeholder="e.g. Mike Smith")
            entry_pos  = st.selectbox("Position", ["Guard", "Forward", "Center"])
        with fc2:
            entry_sleep    = st.slider("Hours Slept", 0.0, 12.0, 7.0, 0.5)
            entry_soreness = st.slider("Soreness (0–10)", 0, 10, 5)
            entry_fatigue  = st.slider("Fatigue (0–10)", 0, 10, 5)
        with fc3:
            entry_starter = st.radio("Starter?", ["Y", "N"])
            preview_score = calc_readiness(entry_sleep, entry_soreness, entry_fatigue)
            preview_status = get_status(preview_score)
            preview_risk   = get_risk(entry_sleep, entry_soreness, entry_fatigue)
            preview_rec    = get_recommendation(preview_status, preview_risk)
            st.markdown(f"""
            **Live Preview**
            - Readiness Score: **{preview_score}**
            - Status: **{preview_status}**
            - Injury Risk: **{preview_risk}**
            - Recommendation: **{preview_rec}**
            """)

        submitted = st.form_submit_button("✅ Add Player Entry", use_container_width=True)
        if submitted and entry_name.strip():
            new_row = pd.DataFrame([{
                "Date": entry_date.strftime("%-m/%-d/%Y"),
                "Name": entry_name.strip(),
                "Hours Slept": entry_sleep,
                "Soreness": entry_soreness,
                "Fatigue": entry_fatigue,
                "Position": entry_pos,
                "Starter": entry_starter,
            }])
            st.session_state.player_data = pd.concat(
                [st.session_state.player_data, new_row], ignore_index=True
            )
            st.success(f"✅ {entry_name} added! Readiness: {preview_score} — {preview_status}")
            st.rerun()
        elif submitted:
            st.warning("Please enter a player name.")


# ══════════════════════════════════════════════════════════════════════════════
# PLAYER STATUS BOARD (TABLE)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📋 Player Status Board</div>', unsafe_allow_html=True)

filter_col1, filter_col2 = st.columns([3, 1])
with filter_col1:
    filter_status = st.multiselect(
        "Filter by Status",
        options=["Ready", "Moderate", "Not Ready"],
        default=["Ready", "Moderate", "Not Ready"],
    )
with filter_col2:
    starters_only = st.checkbox("Starters Only")

filtered = df[df["Status"].isin(filter_status)]
if starters_only:
    filtered = filtered[filtered["Starter"] == "Y"]

# Build display table
display_rows = []
for _, row in filtered.iterrows():
    sc = score_color(row["Status"])
    display_rows.append({
        "Player": f"{'⭐ ' if row['Starter'] == 'Y' else ''}{row['Name']}",
        "Position": row["Position"],
        "Sleep": f"{row['Hours Slept']}h",
        "Fatigue": f"{row['Fatigue']}/10",
        "Soreness": f"{row['Soreness']}/10",
        "Readiness": row["Readiness Score"],
        "Status": row["Status"],
        "Injury Risk": row["Injury Risk"],
        "Recommendation": row["Recommendation"],
    })

display_df = pd.DataFrame(display_rows)

def color_status(val):
    colors = {"Ready": "background-color:#e6f9ee;color:#007a30;font-weight:700",
              "Moderate": "background-color:#fff9e0;color:#7a6000;font-weight:700",
              "Not Ready": "background-color:#fff0f0;color:#cc0000;font-weight:700"}
    return colors.get(val, "")

def color_risk(val):
    if val == "High Risk": return "background-color:#fff0f0;color:#cc0000;font-weight:700"
    return "background-color:#e6f9ee;color:#007a30;font-weight:700"

def color_rec(val):
    colors = {"Train": "background-color:#e6f9ee;color:#007a30;font-weight:700",
              "Rest":  "background-color:#fff9e0;color:#7a6000;font-weight:700",
              "Bench": "background-color:#fff0f0;color:#cc0000;font-weight:700"}
    return colors.get(val, "")

def color_readiness(val):
    if val >= 19: return "color:#00c853;font-weight:700;font-size:16px"
    if val >= 11: return "color:#e6b800;font-weight:700;font-size:16px"
    return "color:#ff1744;font-weight:700;font-size:16px"

styled = (
    display_df.style
    .applymap(color_status,    subset=["Status"])
    .applymap(color_risk,      subset=["Injury Risk"])
    .applymap(color_rec,       subset=["Recommendation"])
    .applymap(color_readiness, subset=["Readiness"])
    .set_properties(**{"font-size": "13px"})
    .hide(axis="index")
)
st.dataframe(styled, use_container_width=True, height=420)


# ══════════════════════════════════════════════════════════════════════════════
# ALERT CARDS + INDIVIDUAL CHARTS  (side by side)
# ══════════════════════════════════════════════════════════════════════════════
left_col, right_col = st.columns([1, 1])

with left_col:
    st.markdown('<div class="section-header">🚨 Alert Cards</div>', unsafe_allow_html=True)
    sorted_df = df.sort_values("Readiness Score")
    for _, row in sorted_df.iterrows():
        card_class = "high" if row["Injury Risk"] == "High Risk" else ("mod" if row["Status"] == "Moderate" else "low")
        sc = score_color(row["Status"])
        starter_badge = "⭐ Starter" if row["Starter"] == "Y" else "Reserve"
        rec_label = {"Train": "▶ Train", "Rest": "◎ Rest", "Bench": "✕ Bench"}.get(row["Recommendation"], row["Recommendation"])
        rec_color = {"Train": "#007a30", "Rest": "#7a6000", "Bench": "#cc0000"}.get(row["Recommendation"], "#888")
        st.markdown(f"""
        <div class="alert-card {card_class}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <div class="alert-name">{row['Name']}</div>
                    <div class="alert-meta">{row['Position']} · {starter_badge}</div>
                    <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap;">
                        {'<span class="chip chip-highrisk">⚠ High Risk</span>' if row["Injury Risk"] == "High Risk" else '<span class="chip chip-lowrisk">✓ Low Risk</span>'}
                        <span class="chip" style="background:#f5f5f5;color:#555;">😴 {row['Hours Slept']}h</span>
                        <span class="chip" style="background:#f5f5f5;color:#555;">Sore {row['Soreness']}/10</span>
                    </div>
                    <div style="margin-top:8px;font-size:12px;font-weight:700;color:{rec_color};">{rec_label}</div>
                </div>
                <div class="alert-score" style="color:{sc};">{row['Readiness Score']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="section-header">📈 Individual Player Chart</div>', unsafe_allow_html=True)
    selected_player = st.selectbox("Select a player", df["Name"].tolist())
    p = df[df["Name"] == selected_player].iloc[0]
    sc = score_color(p["Status"])

    st.markdown(f"""
    <div style="background:white;border-radius:8px;border:1px solid #eee;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,0.07);">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
            <div style="width:48px;height:48px;border-radius:50%;background:{sc};display:flex;align-items:center;justify-content:center;
                font-family:'Oswald',sans-serif;font-size:16px;font-weight:700;color:white;">
                {''.join([w[0] for w in p['Name'].split()])}
            </div>
            <div>
                <div style="font-family:'Oswald',sans-serif;font-size:18px;font-weight:700;">{p['Name']}</div>
                <div style="font-size:11px;color:#999;text-transform:uppercase;letter-spacing:0.5px;">
                    {p['Position']} · {'Starter' if p['Starter'] == 'Y' else 'Reserve'}
                </div>
            </div>
            <div style="margin-left:auto;font-family:'Oswald',sans-serif;font-size:36px;font-weight:700;color:{sc};">{p['Readiness Score']}</div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:16px;">
            <div style="text-align:center;padding:8px;background:#f9f9f9;border-radius:6px;">
                <div style="font-family:'Oswald',sans-serif;font-size:22px;font-weight:700;color:{sc};">{p['Readiness Score']}</div>
                <div style="font-size:9px;text-transform:uppercase;letter-spacing:0.5px;color:#aaa;font-weight:700;">Readiness</div>
            </div>
            <div style="text-align:center;padding:8px;background:#f9f9f9;border-radius:6px;">
                <div style="font-family:'Oswald',sans-serif;font-size:22px;font-weight:700;">{p['Hours Slept']}h</div>
                <div style="font-size:9px;text-transform:uppercase;letter-spacing:0.5px;color:#aaa;font-weight:700;">Sleep</div>
            </div>
            <div style="text-align:center;padding:8px;background:#f9f9f9;border-radius:6px;">
                <div style="font-family:'Oswald',sans-serif;font-size:22px;font-weight:700;color:{'#ff1744' if p['Fatigue']>=7 else '#e6b800' if p['Fatigue']>=4 else '#00c853'};">{p['Fatigue']}/10</div>
                <div style="font-size:9px;text-transform:uppercase;letter-spacing:0.5px;color:#aaa;font-weight:700;">Fatigue</div>
            </div>
            <div style="text-align:center;padding:8px;background:#f9f9f9;border-radius:6px;">
                <div style="font-family:'Oswald',sans-serif;font-size:22px;font-weight:700;color:{'#ff1744' if p['Soreness']>=7 else '#e6b800' if p['Soreness']>=4 else '#00c853'};">{p['Soreness']}/10</div>
                <div style="font-size:9px;text-transform:uppercase;letter-spacing:0.5px;color:#aaa;font-weight:700;">Soreness</div>
            </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:8px;">
            <div><div style="font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;margin-bottom:3px;">Sleep</div>
                {bar_html(p['Hours Slept'], 10, invert=False)}</div>
            <div><div style="font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;margin-bottom:3px;">Fatigue</div>
                {bar_html(p['Fatigue'], 10, invert=True)}</div>
            <div><div style="font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;margin-bottom:3px;">Soreness</div>
                {bar_html(p['Soreness'], 10, invert=True)}</div>
            <div><div style="font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;margin-bottom:3px;">Readiness Score</div>
                {bar_html(p['Readiness Score'], 30, invert=False)}</div>
        </div>
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid #f0f0f0;display:flex;gap:8px;align-items:center;">
            <span style="font-size:11px;color:#aaa;font-weight:700;text-transform:uppercase;">Recommendation:</span>
            <span style="font-size:13px;font-weight:700;color:{'#007a30' if p['Recommendation']=='Train' else '#7a6000' if p['Recommendation']=='Rest' else '#cc0000'};">
                {'▶ Train' if p['Recommendation']=='Train' else '◎ Rest' if p['Recommendation']=='Rest' else '✕ Bench'}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# POSITION-BASED COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📊 Position-Based Comparison</div>', unsafe_allow_html=True)

positions = df["Position"].unique()
pos_stats = []
for pos in positions:
    grp = df[df["Position"] == pos]
    pos_stats.append({
        "Position": pos,
        "Players": len(grp),
        "Avg Readiness": round(grp["Readiness Score"].mean(), 1),
        "Avg Sleep (h)": round(grp["Hours Slept"].mean(), 1),
        "Avg Fatigue": round(grp["Fatigue"].mean(), 1),
        "Avg Soreness": round(grp["Soreness"].mean(), 1),
        "High Risk Count": len(grp[grp["Injury Risk"] == "High Risk"]),
        "Ready Count": len(grp[grp["Status"] == "Ready"]),
    })
pos_df = pd.DataFrame(pos_stats).sort_values("Avg Readiness", ascending=False)

p1, p2, p3 = st.columns(3)
for col, (_, row) in zip([p1, p2, p3], pos_df.iterrows()):
    sc2 = "#00c853" if row["Avg Readiness"] >= 19 else "#e6b800" if row["Avg Readiness"] >= 11 else "#ff1744"
    with col:
        st.markdown(f"""
        <div style="background:white;border-radius:8px;border:1px solid #eee;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,0.07);">
            <div style="font-family:'Oswald',sans-serif;font-size:20px;font-weight:700;border-bottom:3px solid {sc2};padding-bottom:8px;margin-bottom:12px;">{row['Position']}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                <div style="text-align:center;padding:8px;background:#f9f9f9;border-radius:6px;">
                    <div style="font-family:'Oswald',sans-serif;font-size:24px;font-weight:700;color:{sc2};">{row['Avg Readiness']}</div>
                    <div style="font-size:9px;text-transform:uppercase;color:#aaa;font-weight:700;">Avg Readiness</div>
                </div>
                <div style="text-align:center;padding:8px;background:#f9f9f9;border-radius:6px;">
                    <div style="font-family:'Oswald',sans-serif;font-size:24px;font-weight:700;">{row['Avg Sleep (h)']}h</div>
                    <div style="font-size:9px;text-transform:uppercase;color:#aaa;font-weight:700;">Avg Sleep</div>
                </div>
                <div style="text-align:center;padding:8px;background:#f9f9f9;border-radius:6px;">
                    <div style="font-family:'Oswald',sans-serif;font-size:24px;font-weight:700;color:#ff1744;">{row['High Risk Count']}</div>
                    <div style="font-size:9px;text-transform:uppercase;color:#aaa;font-weight:700;">High Risk</div>
                </div>
                <div style="text-align:center;padding:8px;background:#f9f9f9;border-radius:6px;">
                    <div style="font-family:'Oswald',sans-serif;font-size:24px;font-weight:700;color:#00c853;">{row['Ready Count']}</div>
                    <div style="font-size:9px;text-transform:uppercase;color:#aaa;font-weight:700;">Ready</div>
                </div>
            </div>
            <div style="margin-top:10px;font-size:11px;color:#aaa;text-align:center;">{row['Players']} players in this group</div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;font-size:11px;color:#bbb;padding:16px 0;border-top:1px solid #eee;">
    ⚡ Geiger Performance Pulse &nbsp;|&nbsp; Powered by Streamlit &nbsp;|&nbsp; Recovery data is for coaching use only
</div>
""", unsafe_allow_html=True)
