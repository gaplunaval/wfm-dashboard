import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Synsex Performance Report", page_icon="📊", layout="wide"
)

# --- CUSTOM CSS FOR DARK BLUE TABS & ANIMATED CARDS ---
st.markdown(
    """
    <style>
    /* Marquee Animation for Top Title */
    .marquee-container {
        background: linear-gradient(90deg, #1b365d, #0056b3, #1b365d);
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
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

    /* Dark Blue Styling for Streamlit Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f1f3f5;
        padding: 10px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1b365d !important;
        color: white !important;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #004085 !important;
        border-bottom: 3px solid #ff7f0e;
    }

    /* Animated KPI Cards */
    .kpi-card {
        background: #ffffff;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 5px solid #1b365d;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 10px;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border-left: 5px solid #ff7f0e;
    }
    .kpi-title {
        font-size: 13px;
        font-weight: 600;
        color: #6c757d;
        margin-bottom: 6px;
        text-transform: uppercase;
    }
    .kpi-value {
        font-size: 22px;
        font-weight: bold;
        color: #1b365d;
    }
    </style>
    
    <!-- Top Left-to-Right Animated Banner -->
    <div class="marquee-container">
        <div class="marquee-text">🚀 Synsex Performance Report &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; WFM Operations Dashboard &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; Real-time Analytics</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --- AUTOMATIC DATA LOADING FROM REPOSITORY ---
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
  # Clean column names
  df.columns = df.columns.str.strip()


  # Helper function to convert time format (hh:mm:ss or mm:ss or seconds) to total seconds
  def time_to_seconds(val):
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


  # Helper function to convert seconds back to hh:mm:ss format for display
  def seconds_to_time_format(seconds):
    if pd.isna(seconds) or seconds == 0:
      return "00:00:00"
    int_sec = int(round(seconds))
    hrs = int_sec // 3600
    mins = (int_sec % 3600) // 60
    secs = int_sec % 60
    if hrs > 0:
      return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    else:
      return f"{mins:02d}:{secs:02d}"


  # Convert time/numeric columns based on new headers
  time_cols = [
      "Staff time",
      "Net Login time",
      "Break time",
      "Avail time",
      "Total Talk time",
      "Total ACW Time",
      "Hold time",
      "Outbound Talk time",
  ]
  for col in time_cols:
    if col in df.columns:
      df[f"{col}_sec"] = df[col].apply(time_to_seconds)

  num_cols = [
      "HC",
      "Schedule",
      "Present",
      "Absent_New",
      "WO",
      "Leave",
      "Received Calls",
  ]
  for col in num_cols:
    if col in df.columns:
      df[col] = pd.to_numeric(
          df[col].astype(str).str.replace(",", ""), errors="coerce"
      ).fillna(0)

  # --- TOP CONTROLS: QUEUE / SKILL & FILTERS ---
  st.markdown("### 🎛️ Report Filters & Queue Selection")
  ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])

  with ctrl_col1:
    st.markdown("**Select Skill / Queue:**")
    skill_col_name = (
        "Skill/Type" if "Skill/Type" in df.columns else "Process"
    )
    if skill_col_name in df.columns:
      unique_skills = list(df[skill_col_name].dropna().unique())
      s1 = unique_skills[0] if len(unique_skills) > 0 else "Skill 1"
      s2 = unique_skills[1] if len(unique_skills) > 1 else "Skill 2"
      s3 = unique_skills[2] if len(unique_skills) > 2 else "Skill 3"

      if "selected_skill_btn" not in st.session_state:
        st.session_state.selected_skill_btn = "All"

      sb1, sb2, sb3, sb4 = st.columns(4)
      with sb1:
        if st.button("All", use_container_width=True):
          st.session_state.selected_skill_btn = "All"
      with sb2:
        if st.button(str(s1), use_container_width=True):
          st.session_state.selected_skill_btn = s1
      with sb3:
        if st.button(str(s2), use_container_width=True):
          st.session_state.selected_skill_btn = s2
      with sb4:
        if len(unique_skills) > 2:
          if st.button(str(s3), use_container_width=True):
            st.session_state.selected_skill_btn = s3

      current_skill = st.session_state.selected_skill_btn
      if current_skill != "All":
        df = df[df[skill_col_name] == current_skill]

  with ctrl_col2:
    if "Month" in df.columns:
      months = ["All"] + list(df["Month"].dropna().unique())
      selected_month = st.selectbox("Filter by Month", months)
      if selected_month != "All":
        df = df[df["Month"] == selected_month]

  with ctrl_col3:
    if "Week" in df.columns:
      weeks = ["All"] + list(df["Week"].dropna().unique())
      selected_week = st.selectbox("Filter by Week", weeks)
      if selected_week != "All":
        df = df[df["Week"] == selected_week]

  st.markdown("---")

  # --- CREATE 6 TABS WITH DARK BLUE STYLING ---
  tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
      "Summary & KPI",
      "Day wise",
      "Week wise",
      "Supervisor wise",
      "Agent wise",
      "Month wise",
  ])

  # ================= TAB 1: SUMMARY & KPI =================
  with tab1:
    st.subheader("📊 Summary & KPI Operational Dashboard")

    # Sum metrics
    tot_hc = df["HC"].sum() if "HC" in df.columns else 0
    tot_sched = df["Schedule"].sum() if "Schedule" in df.columns else 0
    tot_pres = df["Present"].sum() if "Present" in df.columns else 0
    tot_abs = df["Absent_New"].sum() if "Absent_New" in df.columns else 0
    tot_wo = df["WO"].sum() if "WO" in df.columns else 0
    tot_leave = df["Leave"].sum() if "Leave" in df.columns else 0

    tot_staff_sec = (
        df["Staff time_sec"].sum() if "Staff time_sec" in df.columns else 0
    )
    tot_net_sec = (
        df["Net Login time_sec"].sum()
        if "Net Login time_sec" in df.columns
        else 0
    )
    tot_break_sec = (
        df["Break time_sec"].sum() if "Break time_sec" in df.columns else 0
    )
    tot_avail_sec = (
        df["Avail time_sec"].sum() if "Avail time_sec" in df.columns else 0
    )
    tot_talk_sec = (
        df["Total Talk time_sec"].sum()
        if "Total Talk time_sec" in df.columns
        else 0
    )
    tot_acw_sec = (
        df["Total ACW Time_sec"].sum()
        if "Total ACW Time_sec" in df.columns
        else 0
    )
    tot_rec_calls = (
        df["Received Calls"].sum() if "Received Calls" in df.columns else 0
    )

    # Row 1 KPIs: Headcount & Attendance
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Total Headcount</div><div'
          f' class="kpi-value">{int(tot_hc):,}</div></div>',
          unsafe_allow_html=True,
      )
    with c2:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Total'
          f' Schedule</div><div class="kpi-value">{int(tot_sched):,}</div></div>',
          unsafe_allow_html=True,
      )
    with c3:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Total'
          f' Present</div><div class="kpi-value">{int(tot_pres):,}</div></div>',
          unsafe_allow_html=True,
      )
    with c4:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Total'
          f' Absent</div><div class="kpi-value">{int(tot_abs):,}</div></div>',
          unsafe_allow_html=True,
      )
    with c5:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Total'
          f' WO</div><div class="kpi-value">{int(tot_wo):,}</div></div>',
          unsafe_allow_html=True,
      )
    with c6:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Total'
          f' Leave</div><div class="kpi-value">{int(tot_leave):,}</div></div>',
          unsafe_allow_html=True,
      )

    # Row 2 KPIs: Time & Calls
    cc1, cc2, cc3, cc4, cc5, cc6, cc7 = st.columns(7)
    with cc1:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Staff Time</div><div'
          f' class="kpi-value">{seconds_to_time_format(tot_staff_sec)}</div></div>',
          unsafe_allow_html=True,
      )
    with cc2:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Net Login'
          f' Time</div><div'
          f' class="kpi-value">{seconds_to_time_format(tot_net_sec)}</div></div>',
          unsafe_allow_html=True,
      )
    with cc3:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Break'
          f' Time</div><div'
          f' class="kpi-value">{seconds_to_time_format(tot_break_sec)}</div></div>',
          unsafe_allow_html=True,
      )
    with cc4:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Avail'
          f' Time</div><div'
          f' class="kpi-value">{seconds_to_time_format(tot_avail_sec)}</div></div>',
          unsafe_allow_html=True,
      )
    with cc5:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Total Talk'
          f' Time</div><div'
          f' class="kpi-value">{seconds_to_time_format(tot_talk_sec)}</div></div>',
          unsafe_allow_html=True,
      )
    with cc6:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Total ACW'
          f' Time</div><div'
          f' class="kpi-value">{seconds_to_time_format(tot_acw_sec)}</div></div>',
          unsafe_allow_html=True,
      )
    with cc7:
      st.markdown(
          f'<div class="kpi-card"><div class="kpi-title">Received'
          f' Calls</div><div class="kpi-value">{int(tot_rec_calls):,}</div></div>',
          unsafe_allow_html=True,
      )

  # ================= TAB 2: DAY WISE =================
  with tab2:
    st.subheader("📅 Day Wise Performance Report")
    day_col = "Day" if "Day" in df.columns else ("Date" if "Date" in df.columns else None)
    if day_col:
      agg_cols = {}
      for c in [
          "HC",
          "Schedule",
          "Present",
          "Absent_New",
          "WO",
          "Leave",
          "Received Calls",
          "Staff time_sec",
          "Net Login time_sec",
          "Break time_sec",
          "Avail time_sec",
          "Total Talk time_sec",
          "Total ACW Time_sec",
      ]:
        if c in df.columns:
          agg_cols[c] = "sum"

      day_df = df.groupby(day_col).agg(agg_cols).reset_index()
      st.dataframe(day_df, use_container_width=True)
    else:
      st.warning("Day or Date column not found in data.")

  # ================= TAB 3: WEEK WISE =================
  with tab3:
    st.subheader("📆 Week Wise Performance Report")
    if "Week" in df.columns:
      agg_cols = {}
      for c in [
          "HC",
          "Schedule",
          "Present",
          "Absent_New",
          "WO",
          "Leave",
          "Received Calls",
          "Staff time_sec",
          "Net Login time_sec",
          "Break time_sec",
          "Avail time_sec",
          "Total Talk time_sec",
          "Total ACW Time_sec",
      ]:
        if c in df.columns:
          agg_cols[c] = "sum"

      week_df = df.groupby("Week").agg(agg_cols).reset_index()
      st.dataframe(week_df, use_container_width=True)
    else:
      st.warning("Week column not found in data.")

  # ================= TAB 4: SUPERVISOR WISE =================
  with tab4:
    st.subheader("👔 Supervisor Wise Performance Report")
    sup_col = (
        "Supervisor"
        if "Supervisor" in df.columns
        else ("Shift Manager" if "Shift Manager" in df.columns else None)
    )
    if sup_col:
      agg_cols = {}
      for c in [
          "HC",
          "Schedule",
          "Present",
          "Absent_New",
          "WO",
          "Leave",
          "Received Calls",
          "Staff time_sec",
          "Net Login time_sec",
          "Break time_sec",
          "Avail time_sec",
          "Total Talk time_sec",
          "Total ACW Time_sec",
      ]:
        if c in df.columns:
          agg_cols[c] = "sum"

      sup_df = df.groupby(sup_col).agg(agg_cols).reset_index()
      st.dataframe(sup_df, use_container_width=True)
    else:
      st.warning("Supervisor column not found in data.")

  # ================= TAB 5: AGENT WISE =================
  with tab5:
    st.subheader("agents Agent Wise Performance Report")
    agent_col = (
        "Name"
        if "Name" in df.columns
        else ("Emp ID" if "Emp ID" in df.columns else None)
    )
    if agent_col:
      agg_cols = {}
      for c in [
          "Received Calls",
          "Staff time_sec",
          "Net Login time_sec",
          "Break time_sec",
          "Avail time_sec",
          "Total Talk time_sec",
          "Total ACW Time_sec",
      ]:
        if c in df.columns:
          agg_cols[c] = "sum"

      agent_df = df.groupby([agent_col]).agg(agg_cols).reset_index()
      st.dataframe(agent_df, use_container_width=True)
    else:
      st.warning("Agent Name or Emp ID column not found in data.")

  # ================= TAB 6: MONTH WISE =================
  with tab6:
    st.subheader("🗓️ Month Wise Performance Report")
    if "Month" in df.columns:
      agg_cols = {}
      for c in [
          "HC",
          "Schedule",
          "Present",
          "Absent_New",
          "WO",
          "Leave",
          "Received Calls",
          "Staff time_sec",
          "Net Login time_sec",
          "Break time_sec",
          "Avail time_sec",
          "Total Talk time_sec",
          "Total ACW Time_sec",
      ]:
        if c in df.columns:
          agg_cols[c] = "sum"

      month_df = df.groupby("Month").agg(agg_cols).reset_index()
      st.dataframe(month_df, use_container_width=True)
    else:
      st.warning("Month column not found in data.")

else:
  st.error(
      "⚠️ Data file not found in the GitHub repository! Please make sure your"
      " updated dataset file is uploaded."
  )
