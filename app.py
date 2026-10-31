import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="WFM Operations & Performance Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📈 WFM Operations & Performance Dashboard")
st.markdown("---")


# Automatically find and load data file from the repository
@st.cache_data
def load_data():
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


df = load_data()

if df is not None:
  # Clean column names (strip any extra spaces)
  df.columns = df.columns.str.strip()

  # --- SIDEBAR FILTERS ---
  st.sidebar.header("🔍 Global Filters")

  # Month Filter
  if "Month" in df.columns:
    months = ["All"] + list(df["Month"].dropna().unique())
    selected_month = st.sidebar.selectbox("Filter by Month", months)
    if selected_month != "All":
      df = df[df["Month"] == selected_month]

  # Week Filter
  if "Week" in df.columns:
    weeks = ["All"] + list(df["Week"].dropna().unique())
    selected_week = st.sidebar.selectbox("Filter by Week", weeks)
    if selected_week != "All":
      df = df[df["Week"] == selected_week]

  # Queue Filter
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

  # Derived Metrics
  calc_sla = (ans_sla / rec_calls * 100) if rec_calls > 0 else 0

  # AHT calculation: Talktime / Answered Calls
  total_talktime = df["Talktime"].sum() if "Talktime" in df.columns else 0
  aht = (total_talktime / ans_calls) if ans_calls > 0 else 0

  # --- KPI CARDS SECTION ---
  st.subheader("📊 Operational Summary KPIs")
  col1, col2, col3, col4, col5, col6 = st.columns(6)

  with col1:
    st.metric(label="Received Calls", value=f"{rec_calls:,}")
  with col2:
    st.metric(label="Answered Calls", value=f"{ans_calls:,}")
  with col3:
    st.metric(label="Answered in SLA", value=f"{ans_sla:,}")
  with col4:
    st.metric(label="Abandoned Calls", value=f"{abnd_calls:,}")
  with col5:
    st.metric(label="SLA %", value=f"{calc_sla:.2f}%")
  with col6:
    st.metric(label="AHT (Sec/Min)", value=f"{aht:.2f}")

  st.markdown("---")

  # --- GROUPING FOR TRENDS (By Date or Day) ---
  group_col = "Date" if "Date" in df.columns else (
      "Day" if "Day" in df.columns else None
  )

  if group_col and not df.empty:
    trend_df = (
        df.groupby(group_col)
        .agg({
            "Received Calls": "sum",
            "Answered Calls": "sum",
            "Answered in SLA": "sum",
            "Abandoned Calls": "sum",
            "Talktime": "sum",
        })
        .reset_index()
    )

    # Calculate SLA% and AHT per group for lines
    trend_df["SLA_Pct"] = (
        trend_df["Answered in SLA"] / trend_df["Received Calls"] * 100
    ).fillna(0)
    trend_df["AHT"] = (
        trend_df["Talktime"] / trend_df["Answered Calls"]
    ).fillna(0)

    st.subheader(f"📈 Performance Trend Analysis (By {group_col})")

    # Interactive metric selector for chart
    chart_metric = st.selectbox(
        "Select Secondary Line Metric for Combination Chart",
        ["SLA_Pct", "AHT", "Abandoned Calls"],
    )

    # --- COLUMN & LINE COMBINATION CHART USING PLOTLY ---
    fig = go.Figure()

    # Add Columns (Received & Answered Calls)
    fig.add_trace(
        go.Bar(
            x=trend_df[group_col],
            y=trend_df["Received Calls"],
            name="Received Calls",
            marker_color="#1f77b4",
        )
    )
    fig.add_trace(
        go.Bar(
            x=trend_df[group_col],
            y=trend_df["Answered Calls"],
            name="Answered Calls",
            marker_color="#2ca02c",
        )
    )

    # Add Line for selected performance indicator
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

    # Layout setup for dual-axis combination chart
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

  # Raw Data Preview Option
  if st.checkbox("Show Filtered Raw Data Table"):
    st.dataframe(df, use_container_width=True)

else:
  st.error(
      "⚠️ Data file not found in the repository! Please ensure your Excel or"
      " CSV file is uploaded in GitHub."
  )