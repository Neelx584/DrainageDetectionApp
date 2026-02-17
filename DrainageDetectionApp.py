import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Flood & Drainage Monitoring Dashboard",
    page_icon="💧",
    layout="wide"
)

# -------------------------------------------------
# AUTO REFRESH (BUILT-IN, CLOUD SAFE)
# -------------------------------------------------
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# -------------------------------------------------
# DARK CONTROL-ROOM CSS + ICONS
# -------------------------------------------------
st.markdown(
"""
<style>

/* SMART CITY BACKGROUND + DRIFT */

.stApp {
  background:
    radial-gradient(circle at 15% 20%, rgba(91,192,255,0.08) 0%, transparent 35%),
    radial-gradient(circle at 85% 15%, rgba(91,192,255,0.05) 0%, transparent 40%),
    radial-gradient(circle at 50% 90%, rgba(91,192,255,0.04) 0%, transparent 45%),
    linear-gradient(180deg, #0b1220 0%, #070b14 60%, #05070e 100%);
  color: #e6eefc;
  overflow: hidden;
}

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

.block-container,
section[data-testid="stSidebar"],
header,
footer {
  position: relative;
  z-index: 1;
}

@keyframes glowDrift {
  0%   { transform: translate(-2%, -1%) scale(1.02); }
  50%  { transform: translate(2%, 1%) scale(1.05); }
  100% { transform: translate(-1%, 2%) scale(1.03); }
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
    return "<div class='section-title'><i class='fa-solid {}'></i><span>{}</span></div>".format(icon_class, title)

def kpi_box(icon_class: str, title: str, value: str) -> str:
    return f"""
    <div class="kpi">
      <div class="kpi-title"><i class="fa-solid {icon_class}"></i> {title}</div>
      <div class="kpi-value">{value}</div>
    </div>
    """

# -------------------------------------------------
# DATA + MODEL
# -------------------------------------------------
def make_demo_data(n_hours=24):
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    times = [now - timedelta(hours=i) for i in range(n_hours)][::-1]

    rain = np.maximum(0, np.random.normal(2.0, 1.6, n_hours))
    flow = (10 + rain * 2.5) + np.random.normal(0, 1.0, n_hours)
    flow = np.clip(flow, 0, None)

    tank = np.zeros(n_hours)
    tank[0] = 30
    for i in range(1, n_hours):
        tank[i] = tank[i-1] + rain[i] * 1.2 - flow[i] * 0.08
    tank = np.clip(tank, 0, 100)

    return pd.DataFrame({
        "timestamp": times,
        "rain_mm_per_hr": rain,
        "drain_flow_Lps": flow,
        "tank_fill_pct": tank
    })

def compute_risk(rain, flow, tank):
    return int(min(100, 0.4 * rain + 0.3 * tank + 0.3 * (100 - flow)))

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.subheader("Auto-refresh")
refresh_sec = st.sidebar.slider("Refresh interval (seconds)", 2, 30, 8)

# Trigger refresh
if time.time() - st.session_state.last_refresh >= refresh_sec:
    st.session_state.last_refresh = time.time()
    st.rerun()

# -------------------------------------------------
# DATA
# -------------------------------------------------
df = make_demo_data(24)
latest = df.iloc[-1]
rain_now = latest["rain_mm_per_hr"]
flow_now = latest["drain_flow_Lps"]
tank_now = latest["tank_fill_pct"]

risk_now = compute_risk(rain_now, flow_now, tank_now)

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.title("Flood & Drainage Monitoring Dashboard")

# -------------------------------------------------
# KPI ROW
# -------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rain (mm/h)", f"{rain_now:.2f}")
c2.metric("Flow (L/s)", f"{flow_now:.2f}")
c3.metric("Tank (%)", f"{tank_now:.1f}")
c4.metric("Risk (0–100)", risk_now)

# -------------------------------------------------
# TREND
# -------------------------------------------------
fig = px.line(df, x="timestamp", y=["rain_mm_per_hr", "tank_fill_pct"])
fig.update_layout(template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# GAUGE
# -------------------------------------------------
gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=risk_now,
    gauge={"axis": {"range": [0, 100]}}
))
gauge.update_layout(template="plotly_dark")
st.plotly_chart(gauge, use_container_width=True)

