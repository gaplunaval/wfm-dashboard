import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Synsex Performance Report", page_icon="📊", layout="wide"
)

# --- CUSTOM CSS FOR ANIMATED CARDS & MARQUEE HEADER ---
st.markdown(
    """
    <style>
    /* Marquee Animation for Top Title */
    .marquee-container {
        background: linear-gradient(90deg, #1f77b4, #2ca02c, #ff7f0e);
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 20px;
        overflow: hidden;
        white-space: nowrap;
    }
    .marquee-text {
        display: inline-block;
        font-size: 24px;
        font-weight: bold;
        color: white;
        text-transform: uppercase;
        animation: marquee 12s linear infinite;
    }
    @keyframes marquee {
        0%   { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    /* Animated KPI Cards */
    .kpi-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 5px solid #1f77b4;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border-left: 5px solid #ff7f0e;
    }
    .kpi-title {
        font-size: 14px;
        font-weight: 600;
        color: #6c757d;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: bold;
        color: #2c3e50;
    }
    </style>
    
    <!-- Top Left-to-Right Animated Banner -->
    <div class="marquee-container">
        <div class="marquee-text">🚀 Synsex Performance Report &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; WFM Operations Dashboard &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; Real-time Analytics</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --- DATA LOADING (Hybrid: Repo file + Web Uploader) ---
@st.cache_data
def load_default_data():
  for file in os.listdir("."):
    if file.lower().endswith((".xlsx", ".xls")):
      try:
        return pd.read_excel(file)
      except Exception:
        pass
    elif file.lower().endswith(".csv"):
      try:
        return pd.read_csv(file)
      except Exception:
        pass
  return None


# Sidebar for optional live file upload
st.sidebar.header("📁 Data Source & Filters")
uploaded_file = st.sidebar.file_uploader(
    "Upload New Data File (Optional)", type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
  try:
    if uploaded_file.name.endswith(".csv"):
      df = pd.read_csv(uploaded_file)
    else:
      df = pd.read_excel(uploaded_file)
    st.sidebar.success("Using newly uploaded file!")
  except Exception as e:
    st.sidebar.error(f"Error reading file: {e}")
    df = load_default_data()
else:
  df = load_default_data()

if df is not None:
  # Clean column names
  df.columns = df.columns.str.strip()

  # Convert call metrics safely to numeric
  numeric_cols = [
      "Received Calls",
      "Answered Calls",
      "Answered in SLA",
      "Abandoned Calls",
      "Talk Time",
      "Talktime",
  ]
  for col in numeric_cols:
    if col in df.columns:
      df[col] = pd.to_numeric(
          df[col].astype(str).str.replace(",", ""), errors="coerce"
      ).fillna(0)

  # Detect Talk Time column correctly
  talktime_col = None
  for col in ["Talk Time", "Talktime", "Handle Time", "AHT"]:
    if col in df.columns:
      talktime_col = col
      break


  # Helper function to convert Talk Time
  def parse_talk_time(val):
    if pd.isna(val):
      return 0.0
    if isinstance(val, (int, float)):
      return float(val)
    val_str = str(val).strip()
    if ":" in val_str:
      parts = val_str.split(":")
      try:
        if len(parts) == 3:
          return (
              float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
          )
        elif len(parts) == 2:
          return float(parts[0]) * 60 + float(parts[1])
      except:
        return 0.0
    try:
      return float(val_str.replace(",", ""))
    except:
      return 0.0


  if talktime_col:
    df["Talk_Time_Sec"] = df[talktime_col].apply(parse_talk_time)
  else:
    df["Talk_Time_Sec"] = 0.0

  # --- SIDEBAR FILTERS ---
  st.sidebar.markdown("---")
  st.sidebar.subheader("🔍 Filter Data")

  if "Month" in df.columns:
    months = ["All"] + list(df["Month"].dropna().unique())
    selected_month = st.sidebar.selectbox("Filter by Month", months)
    if selected_month != "All":
      df = df[df["Month"] == selected_month]

  if "Week" in df.columns:
    weeks = ["All"] + list(df["Week"].dropna().unique())
    selected_week = st.sidebar.selectbox("Filter by Week", weeks)
    if selected_week != "All":
      df = df[df["Week"] == selected_week]

  if "Queue" in df.columns:
    queues = ["All"] + list(df["Queue"].dropna().unique())
    selected_queue = st.sidebar.selectbox("Filter by Queue", queues)
    if selected_queue != "All":
      df = df[df["Queue"] == selected_queue]

  # --- CALCULATIONS & METRICS ---
  rec_calls = (
      df["Received Calls"].sum() if "Received Calls" in df.columns else 0
  )
  ans_calls = (
      df["Answered Calls"].sum() if "Answered Calls" in df.columns else 0
  )
  ans_sla = (
      df["Answered in SLA"].sum() if "Answered in SLA" in df.columns else 0
  )
  abnd_calls = (
      df["Abandoned Calls"].sum() if "Abandoned Calls" in df.columns else 0
  )

  calc_sla = (ans_sla / rec_calls * 100) if rec_calls > 0 else 0
  total_talktime = df["Talk_Time_Sec"].sum()
  aht = (total_talktime / ans_calls) if ans_calls > 0 else 0

  # --- ANIMATED KPI CARDS SECTION ---
  st.markdown("### 📊 Operational Summary KPIs")
  kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

  with kpi1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Received Calls</div>
            <div class="kpi-value">{int(rec_calls):,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with kpi2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Answered Calls</div>
            <div class="kpi-value">{int(ans_calls):,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with kpi3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Answered in SLA</div>
            <div class="kpi-value">{int(ans_sla):,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with kpi4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Abandoned Calls</div>
            <div class="kpi-value">{int(abnd_calls):,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with kpi5:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">SLA %</div>
            <div class="kpi-value">{calc_sla:.2f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with kpi6:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">AHT (Sec)</div>
            <div class="kpi-value">{aht:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)
  st.markdown("---")

  # --- GROUPING FOR TRENDS ---
  group_col = "Date" if "Date" in df.columns else (
      "Day" if "Day" in df.columns else None
  )

  if group_col and not df.empty:
    agg_dict = {
        "Received Calls": "sum" if "Received Calls" in df.columns else "count",
        "Answered Calls": "sum" if "Answered Calls" in df.columns else "count",
        "Answered in SLA": "sum" if "Answered in SLA" in df.columns else "count",
        "Abandoned Calls": "sum" if "Abandoned Calls" in df.columns else "count",
        "Talk_Time_Sec": "sum",
    }

    trend_df = df.groupby(group_col).agg(agg_dict).reset_index()

    if "Received Calls" in trend_df.columns and "Answered in SLA" in trend_df.columns:
      trend_df["SLA_Pct"] = (
          trend_df["Answered in SLA"] / trend_df["Received Calls"] * 100
      ).fillna(0)
    else:
      trend_df["SLA_Pct"] = 0

    trend_df["AHT"] = (
        trend_df["Talk_Time_Sec"] / trend_df["Answered Calls"]
    ).fillna(0)

    st.subheader(f"📈 Performance Trend Analysis (By {group_col})")

    available_line_metrics = ["SLA_Pct", "AHT"]
    if "Abandoned Calls" in trend_df.columns:
      available_line_metrics.append("Abandoned Calls")

    chart_metric = st.selectbox(
        "Select Secondary Line Metric for Combination Chart",
        available_line_metrics,
    )

    # --- COLUMN & LINE COMBINATION CHART ---
    fig = go.Figure()

    if "Received Calls" in trend_df.columns:
      fig.add_trace(
          go.Bar(
              x=trend_df[group_col],
              y=trend_df["Received Calls"],
              name="Received Calls",
              marker_color="#1f77b4",
          )
      )
    if "Answered Calls" in trend_df.columns:
      fig.add_trace(
          go.Bar(
              x=trend_df[group_col],
              y=trend_df["Answered Calls"],
              name="Answered Calls",
              marker_color="#2ca02c",
          )
      )

    fig.add_trace(
        go.Scatter(
            x=trend_df[group_col],
            y=trend_df[chart_metric],
            name=chart_metric,
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#ff7f0e", width=3),
        )
    )

    fig.update_layout(
        title=f"Call Volume Columns with {chart_metric} Trend Line",
        xaxis=dict(title=group_col),
        yaxis=dict(title="Call Volume", side="left"),
        yaxis2=dict(
            title=chart_metric,
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        margin=dict(l=20, r=20, t=50, b=20),
        height=450,
    )

    st.plotly_chart(fig, use_container_width=True)

  st.markdown("---")

  if st.checkbox("Show Filtered Raw Data Table"):
    st.dataframe(df, use_container_width=True)

else:
  st.error(
      "⚠️ No data file found! Please upload a file via the sidebar or add one"
      " to your GitHub repository."
  )
