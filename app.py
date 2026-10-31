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


# Sidebar for optional live file upload (No need to touch GitHub!)
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
    st.sidebar.info("Loaded default file from repository.")

if df is not None:
  # Clean column names (strip any extra spaces)
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


  # Helper function to convert Talk Time (handles HH:MM:SS or numbers)
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
  total_talktime = df["Talk_Time_Sec"].sum()
  aht = (total_talktime / ans_calls) if ans_calls > 0 else 0

  # --- KPI CARDS SECTION ---
  st.subheader("📊 Operational Summary KPIs")
  col1, col2, col3, col4, col5, col6 = st.columns(6)

  with col1:
    st.metric(label="Received Calls", value=f"{int(rec_calls):,}")
  with col2:
    st.metric(label="Answered Calls", value=f"{int(ans_calls):,}")
  with col3:
    st.metric(label="Answered in SLA", value=f"{int(ans_sla):,}")
  with col4:
    st.metric(label="Abandoned Calls", value=f"{int(abnd_calls):,}")
  with col5:
    st.metric(label="SLA %", value=f"{calc_sla:.2f}%")
  with col6:
    st.metric(label="AHT (Sec)", value=f"{aht:.2f}")

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