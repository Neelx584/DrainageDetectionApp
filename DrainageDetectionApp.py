# DrainageDetectionApp.py
# Dark control-room dashboard + auto-refresh + zone map visual

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import plotly.express as px
import plotly.graph_objects as go

# Auto-refresh component
# pip install streamlit-autorefresh
from streamlit_autorefresh import st_autorefresh

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Flood & Drainage Monitoring Dashboard",
    page_icon="💧",
    layout="wide"
)

# -------------------------------------------------
# DARK CONTROL-ROOM CSS + ICONS
# -------------------------------------------------
st.markdown(
    """
<style>
/* ============================= */
/* SMART CITY BACKGROUND + DRIFT */
/* ============================= */

.stApp {
  background:
    radial-gradient(circle at 15% 20%, rgba(91,192,255,0.08) 0%, transparent 35%),
    radial-gradient(circle at 85% 15%, rgba(91,192,255,0.05) 0%, transparent 40%),
    radial-gradient(circle at 50% 90%, rgba(91,192,255,0.04) 0%, transparent 45%),
    linear-gradient(180deg, #0b1220 0%, #070b14 60%, #05070e 100%);
  color: #e6eefc;
  overflow: hidden;
}

/* Animated glow drift layer */
.stApp::before {
  content: "";
  position: fixed;
  inset: -20%;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(circle at 20% 30%, rgba(91,192,255,0.10) 0%, transparent 35%),
    radial-gradient(circle at 70% 60%, rgba(91,192,255,0.07) 0%, transparent 40%),
    radial-gradient(circle at 40% 85%, rgba(91,192,255,0.06) 0%, transparent 42%);
  filter: blur(18px);
  opacity: 0.45;
  animation: glowDrift 28s ease-in-out infinite alternate;
}

/* Keep all app content above the drift */
.block-container,
section[data-testid="stSidebar"],
header,
footer {
  position: relative;
  z-index: 1;
}

/* Slow drift motion */
@keyframes glowDrift {
  0%   { transform: translate(-2%, -1%) scale(1.02); }
  50%  { transform: translate(2%, 1%) scale(1.05); }
  100% { transform: translate(-1%, 2%) scale(1.03); }
}

/* Hide Streamlit chrome */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* ============================= */
/* GLASS HEADER PANEL            */
/* ============================= */

.header {
  padding: 22px;
  border-radius: 20px;
  background: rgba(14, 21, 38, 0.82);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(91,192,255,0.15);
  box-shadow:
    0 0 35px rgba(91,192,255,0.10),
    0 18px 40px rgba(0,0,0,0.45);
}

/* ============================= */
/* CARD SYSTEM                   */
/* ============================= */

.card, .kpi {
  border-radius: 20px;
  background: rgba(12,18,34,0.82);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(91,192,255,0.12);
  box-shadow:
    0 0 25px rgba(91,192,255,0.05),
    0 14px 30px rgba(0,0,0,0.40);
  transition: all 0.25s ease;
}

.card:hover, .kpi:hover {
  border: 1px solid rgba(91,192,255,0.25);
  box-shadow:
    0 0 45px rgba(91,192,255,0.18),
    0 18px 45px rgba(0,0,0,0.50);
}

/* KPI TEXT GLOW */
.kpi-title {
  font-size: 0.85rem;
  opacity: 0.75;
  margin-bottom: 6px;
}

.kpi-value {
  font-size: 1.85rem;
  font-weight: 850;
  letter-spacing: 0.5px;
  text-shadow:
    0 0 12px rgba(91,192,255,0.35),
    0 0 20px rgba(91,192,255,0.15);
}

/* SECTION TITLES */
.section-title {
  font-weight: 900;
  font-size: 1.05rem;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #5BC0FF;
  text-shadow: 0 0 10px rgba(91,192,255,0.35);
}

/* PROGRESS BARS */
div[data-testid="stProgressBar"] > div > div {
  background: linear-gradient(90deg, #5BC0FF, #38A9F8) !important;
  box-shadow:
    0 0 14px rgba(91,192,255,0.8),
    0 0 25px rgba(91,192,255,0.4);
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
  background: rgba(6,10,18,0.95);
  border-right: 1px solid rgba(91,192,255,0.15);
}

section[data-testid="stSidebar"] * {
  color: #e6eefc;
}

input:focus, textarea:focus, select:focus {
  outline: none !important;
  box-shadow: 0 0 10px rgba(91,192,255,0.6) !important;
}

/* BUTTONS */
button[kind="primary"] {
  background-color: #5BC0FF !important;
  color: #000 !important;
  box-shadow:
    0 0 20px rgba(91,192,255,0.5),
    0 0 40px rgba(91,192,255,0.3);
}

/* DATA TABLE */
[data-testid="stDataFrame"] {
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid rgba(91,192,255,0.15);
  box-shadow:
    0 0 25px rgba(91,192,255,0.08),
    0 10px 30px rgba(0,0,0,0.35);
}

/* SMOOTH TRANSITIONS */
* {
  transition: background 0.2s ease, box-shadow 0.2s ease, border 0.2s ease;
}
</style>
""",
    unsafe_allow_html=True
)


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def pill_html(text: str, cls: str) -> str:
    return "<span class='pill {}'>{}</span>".format(cls, text)

def section_title(icon_class: str, title: str) -> str:
    # icon_class example: "fa-chart-line"
    return "<div class='section-title'><i class='fa-solid {}'></i><span>{}</span></div>".format(icon_class, title)

def kpi_box(icon_class: str, title: str, value: str) -> str:
    return """
    <div class="kpi">
      <div class="kpi-title"><i class="fa-solid {icon}"></i> {title}</div>
      <div class="kpi-value">{value}</div>
    </div>
    """.format(icon=icon_class, title=title, value=value)

# -------------------------------------------------
# DATA + MODEL
# -------------------------------------------------
def make_demo_data(n_hours=24) -> pd.DataFrame:
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    times = [now - timedelta(hours=i) for i in range(n_hours)][::-1]

    rain = np.maximum(0, np.random.normal(2.0, 1.6, n_hours))
    if n_hours >= 10:
        rain[np.random.randint(n_hours - 6, n_hours)] += np.random.uniform(7, 13)

    flow = (10 + rain * 2.5) + np.random.normal(0, 1.0, n_hours)
    flow = np.clip(flow, 0, None)

    tank = np.zeros(n_hours)
    tank[0] = np.random.uniform(22, 48)
    for i in range(1, n_hours):
        tank[i] = tank[i-1] + rain[i] * 1.2 - flow[i] * 0.08
    tank = np.clip(tank, 0, 100)

    return pd.DataFrame({
        "timestamp": times,
        "rain_mm_per_hr": np.round(rain, 2),
        "drain_flow_Lps": np.round(flow, 2),
        "tank_fill_pct": np.round(tank, 1),
    })

def compute_risk_feature(
    rain_mmph: float,
    flow_Lps: float,
    tank_pct: float,
    infil_mmph: float,
    vertical_Lps: float,
    storage_m3: float,
    clog_pct: float,
    area_m2: float
):
    clog = float(np.clip(clog_pct / 100.0, 0, 1))

    eff_infil = infil_mmph * (1 - 0.70 * clog)
    runoff_mmph = max(0.0, rain_mmph - eff_infil)

    demand_Lps = (runoff_mmph * area_m2) / 3600.0

    convey_Lps = (vertical_Lps * (1 - 0.50 * clog)) + (flow_Lps * (1 - 0.35 * clog))
    unmet_Lps = max(0.0, demand_Lps - convey_Lps)

    tank_full = float(np.clip(tank_pct / 100.0, 0, 1))
    storage_norm = float(np.clip(np.log1p(storage_m3) / np.log1p(5000), 0, 1))
    buffer = (1 - tank_full) * storage_norm
    penalty = 1 - buffer

    rain_score = float(np.clip((rain_mmph / 20.0) * 100, 0, 100))
    crit_unmet = max(10.0, 0.001 * area_m2)
    unmet_score = float(np.clip((unmet_Lps / crit_unmet) * 100, 0, 100))
    tank_score = float(np.clip((tank_full * 100) * (0.60 + 0.40 * penalty), 0, 100))
    vuln = float(np.clip(40 * clog, 0, 40))

    risk = 0.35 * rain_score + 0.40 * unmet_score + 0.25 * tank_score + vuln
    risk = int(np.clip(risk, 0, 100))

    return {
        "risk": risk,
        "eff_infil": eff_infil,
        "runoff_mmph": runoff_mmph,
        "demand_Lps": demand_Lps,
        "convey_Lps": convey_Lps,
        "unmet_Lps": unmet_Lps,
        "rain_score": rain_score,
        "unmet_score": unmet_score,
        "tank_score": tank_score,
        "vuln": vuln,
    }

def build_zone_table(risk_pack: dict, clog_pct: float) -> pd.DataFrame:
    # Schematic zones tied to your infrastructure
    # (name, permeability_factor, clog_sensitivity)
    zones = [
        ("Permeable Footpath Segment 1", 1.15, 1.00),
        ("Permeable Footpath Segment 2 (High footfall)", 0.90, 1.25),
        ("Station Frontage Runoff Edge", 0.75, 1.10),
        ("Drain Inlet Cluster", 0.60, 1.35),
        ("Underpass / Low Point", 0.50, 1.15),
        ("Storage Access & Service Bay", 0.65, 1.05),
    ]

    clog = float(np.clip(clog_pct / 100.0, 0, 1))
    rows = []
    for name, perm, clog_sens in zones:
        base = 0.55 * (risk_pack["unmet_Lps"] * 4.0) + 0.45 * (risk_pack["runoff_mmph"] * 4.0)
        zone_score = base * (1.15 - 0.25 * perm) * (1.0 + clog * (0.8 * clog_sens))
        zone_score = int(np.clip(zone_score, 0, 100))
        rows.append((name, zone_score))

    dfz = pd.DataFrame(rows, columns=["zone", "risk_score"]).sort_values("risk_score", ascending=False).reset_index(drop=True)
    return dfz

def zone_map_points(dfz: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a simple schematic site map (not geographic):
    a 3x2 grid with labelled zones.
    """
    # Fixed layout positions (x,y) for zones by index after sorting
    # If you want a different shape later, we can redraw this grid.
    layout = [
        (0, 2), (1, 2), (2, 2),
        (0, 1), (1, 1), (2, 1),
    ]
    n = min(len(dfz), len(layout))
    xs = [layout[i][0] for i in range(n)]
    ys = [layout[i][1] for i in range(n)]

    out = dfz.iloc[:n].copy()
    out["x"] = xs
    out["y"] = ys
    return out

# -------------------------------------------------
# SIDEBAR CONTROLS
# -------------------------------------------------
st.sidebar.title("System Controls")

data_mode = st.sidebar.radio("Data source", ["Simulated (demo)", "Upload CSV"], index=0)

st.sidebar.subheader("Auto-refresh")
refresh_sec = st.sidebar.slider("Refresh interval (seconds)", 2, 30, 8)

st.sidebar.subheader("Design features (your nation)")
infiltration = st.sidebar.slider("Permeable infiltration capacity (mm/h)", 0.0, 50.0, 18.0, 0.5)
vertical = st.sidebar.slider("Vertical drainage capacity (L/s)", 5.0, 120.0, 45.0, 1.0)
storage = st.sidebar.slider("Underground storage capacity (m³)", 50, 5000, 1200, 50)
clogging = st.sidebar.slider("Clogging / blockage level (%)", 0, 100, 18, 1)
area = st.sidebar.slider("Catchment area served (m²)", 500, 200000, 25000, 500)

st.sidebar.subheader("Alert thresholds")
tank_crit = st.sidebar.slider("Tank critical (%)", 70, 95, 85)
rain_spike_delta = st.sidebar.slider("Rain spike threshold (mm/h increase)", 2.0, 20.0, 6.0, 0.5)
flow_block_thresh = st.sidebar.slider("Flow blocked threshold (L/s)", 0.0, 50.0, 8.0, 0.5)
zone_high_risk = st.sidebar.slider("Zone high-risk score ≥", 0, 100, 70)

hours = st.sidebar.slider("History window (hours)", 6, 72, 24, 6)

# -------------------------------------------------
# AUTO-REFRESH (runs app again every N seconds)
# -------------------------------------------------
st_autorefresh(interval=refresh_sec * 1000, key="auto_refresh")

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
if data_mode == "Upload CSV":
    st.sidebar.caption("CSV columns: timestamp, rain_mm_per_hr, drain_flow_Lps, tank_fill_pct")
    up = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if up is not None:
        df = pd.read_csv(up)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        # Trim to window
        df = df.tail(hours)
    else:
        df = make_demo_data(hours)
else:
    df = make_demo_data(hours)

latest = df.iloc[-1]
prev = df.iloc[-2] if len(df) > 1 else latest

rain_now = float(latest["rain_mm_per_hr"])
flow_now = float(latest["drain_flow_Lps"])
tank_now = float(latest["tank_fill_pct"])
rain_prev = float(prev["rain_mm_per_hr"])

risk_pack = compute_risk_feature(
    rain_mmph=rain_now,
    flow_Lps=flow_now,
    tank_pct=tank_now,
    infil_mmph=infiltration,
    vertical_Lps=vertical,
    storage_m3=storage,
    clog_pct=clogging,
    area_m2=area,
)
risk_now = int(risk_pack["risk"])

# Alerts logic
rain_spike = (rain_now - rain_prev) >= rain_spike_delta
flow_blocked = flow_now <= flow_block_thresh
tank_critical = tank_now >= tank_crit

severity = "OK"
if risk_now >= 60 or tank_critical or flow_blocked or rain_spike:
    severity = "WARNING"
if risk_now >= 80 or tank_now >= min(95, tank_crit + 8) or flow_now <= max(0.0, flow_block_thresh - 3):
    severity = "CRITICAL"

sev_cls = {"OK": "pill-ok", "WARNING": "pill-warn", "CRITICAL": "pill-crit"}[severity]

# -------------------------------------------------
# HEADER
# -------------------------------------------------
header_html = """
<div class="header">
  <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:14px; flex-wrap:wrap;">
    <div>
      <div style="font-size:1.55rem; font-weight:950;">
        <i class="fa-solid fa-droplet"></i>
        Flood & Drainage Monitoring Dashboard
      </div>
      <div style="opacity:0.78; margin-top:2px;">
        Permeable footpaths • Vertical drainage • Underground storage • Zone risk • Alerts
      </div>
    </div>
    <div style="white-space:nowrap;">
      {sys_pill}
      {time_pill}
    </div>
  </div>
</div>
""".format(
    sys_pill=pill_html("SYSTEM: " + severity, sev_cls),
    time_pill=pill_html("Last update: " + pd.to_datetime(latest["timestamp"]).strftime("%Y-%m-%d %H:%M"), "pill-info"),
)

st.markdown(header_html, unsafe_allow_html=True)
st.write("")

# -------------------------------------------------
# KPI ROW
# -------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_box("fa-cloud-rain", "Rain intensity (mm/h)", "{:.2f}".format(rain_now)), unsafe_allow_html=True)
c2.markdown(kpi_box("fa-water", "Drain flow (L/s)", "{:.2f}".format(flow_now)), unsafe_allow_html=True)
c3.markdown(kpi_box("fa-tank-water", "Tank fill (%)", "{:.1f}".format(tank_now)), unsafe_allow_html=True)
c4.markdown(kpi_box("fa-triangle-exclamation", "Flood risk score (0–100)", str(risk_now)), unsafe_allow_html=True)
st.write("")

# -------------------------------------------------
# LAYOUT
# -------------------------------------------------
left, right = st.columns([1.45, 1.0], gap="large")

# -------------------------------------------------
# LEFT: Trend + Gauge + Raw Data
# -------------------------------------------------
with left:
    # Trend chart
    st.markdown("<div class='card'>{}</div>".format(section_title("fa-chart-line", "Trend: Rain vs Tank Level")), unsafe_allow_html=True)

    fig = px.line(
        df,
        x="timestamp",
        y=["rain_mm_per_hr", "tank_fill_pct"],
        labels={"value": "Value", "timestamp": "Time", "variable": ""},
    )
    fig.update_layout(
        template="plotly_dark",
        height=420,
        margin=dict(l=10, r=10, t=35, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gauge
    st.markdown("<div class='card'>{}</div>".format(section_title("fa-gauge", "Flood Risk Indicator")), unsafe_allow_html=True)
    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=risk_now,
            title={"text": "Flood Risk Level"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "deepskyblue"},
                "steps": [
                    {"range": [0, 40], "color": "rgba(16,185,129,0.35)"},
                    {"range": [40, 70], "color": "rgba(245,158,11,0.40)"},
                    {"range": [70, 100], "color": "rgba(239,68,68,0.40)"},
                ],
            },
        )
    )
    gauge.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(gauge, use_container_width=True)

    # Raw feed
    st.markdown("<div class='card'>{}</div>".format(section_title("fa-database", "Raw Sensor Feed")), unsafe_allow_html=True)
    st.dataframe(df.tail(min(len(df), 24)), use_container_width=True, hide_index=True)

# -------------------------------------------------
# RIGHT: Alerts + Zone Map + Zones + Model Breakdown
# -------------------------------------------------
with right:

    # -------------------------
    # Alerts
    # -------------------------
    st.markdown("<div class='card'>{}</div>".format(
        section_title("fa-bell", "Alerts")
    ), unsafe_allow_html=True)

    alerts = []
    if tank_critical:
        alerts.append(("Tank level high", f"Tank at {tank_now:.1f}%"))
    if flow_blocked:
        alerts.append(("Flow restriction detected", f"Flow at {flow_now:.2f} L/s"))
    if rain_spike:
        alerts.append(("Rain spike detected", f"Increase: {rain_now - rain_prev:.2f} mm/h"))
    if risk_now >= 80:
        alerts.append(("High flood risk", f"Risk score {risk_now}/100"))

    if not alerts:
        st.success("SYSTEM STABLE — All parameters within safe limits.")
    else:
        for title, msg in alerts:
            st.warning(f"**{title}** — {msg}")

    # -------------------------
    # Zones (List Only)
    # -------------------------
    st.markdown("<div class='card'>{}</div>".format(
        section_title("fa-layer-group", "Zone Risk Levels")
    ), unsafe_allow_html=True)

    dfz = build_zone_table(risk_pack, clogging)
    dfz["status"] = np.where(dfz["risk_score"] >= zone_high_risk, "HIGH", "OK")

    for _, r in dfz.iterrows():
        tag = "🔴 HIGH RISK" if r["risk_score"] >= zone_high_risk else "🟢 OK"
        st.progress(
            int(r["risk_score"]),
            text=f"{tag} · {r['zone']} — {int(r['risk_score'])}/100"
        )

    st.dataframe(dfz[["zone", "risk_score", "status"]],
                 use_container_width=True,
                 hide_index=True)

    # -------------------------
    # Model Breakdown
    # -------------------------
    st.markdown("<div class='card'>{}</div>".format(
        section_title("fa-diagram-project", "Model Breakdown")
    ), unsafe_allow_html=True)

    m1, m2 = st.columns(2)
    m1.metric("Effective infiltration (mm/h)", f"{risk_pack['eff_infil']:.1f}")
    m1.metric("Runoff after infiltration (mm/h)", f"{risk_pack['runoff_mmph']:.2f}")
    m2.metric("Flow demand (L/s)", f"{risk_pack['demand_Lps']:.1f}")
    m2.metric("Conveyance capacity (L/s)", f"{risk_pack['convey_Lps']:.1f}")
