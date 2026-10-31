import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="WFM Performance Dashboard", page_icon="📊", layout="wide"
)

# Sidebar for file loading using Streamlit native uploader (Cloud Compatible)
st.sidebar.header("📁 Data Source")
uploaded_file = st.sidebar.file_uploader(
    "Upload WFM Raw Data File", type=["csv", "xlsx", "xls"]
)

# Main Dashboard Logic
if uploaded_file is not None:
  try:
    if uploaded_file.name.endswith(".csv"):
      df = pd.read_csv(uploaded_file)
    else:
      df = pd.read_excel(uploaded_file)
    st.sidebar.success("File successfully loaded!")
  except Exception as e:
    st.sidebar.error(f"Error loading file: {e}")
    df = None
else:
  df = None

if df is not None:
  st.title("📈 WFM Daily Performance Dashboard")
  st.markdown("---")

  # Display raw data preview option
  if st.checkbox("Show Raw Data Preview"):
    st.dataframe(df.head(10))

  # Summary Metrics Cards / KPIs
  st.subheader("📊 Operational Summary")
  col1, col2, col3, col4 = st.columns(4)

  with col1:
    total_agents = (
        df["Agent"].nunique() if "Agent" in df.columns else len(df)
    )
    st.metric(label="Total Agents", value=total_agents)

  with col2:
    if "Calls Handled" in df.columns:
      total_calls = df["Calls Handled"].sum()
      st.metric(label="Total Calls Handled", value=f"{total_calls:,}")

  with col3:
    if "Login Hours" in df.columns:
      avg_login = df["Login Hours"].mean()
      st.metric(label="Avg Login Hours", value=round(avg_login, 2))

  with col4:
    if "Shrinkage" in df.columns:
      avg_shrinkage = df["Shrinkage"].mean()
      st.metric(label="Avg Shrinkage %", value=f"{round(avg_shrinkage, 2)}%")

  st.markdown("---")

  # Supervisor & Agent Breakdown Filters
  st.subheader("🔍 Detailed Breakdown & Filters")
  if "Supervisor" in df.columns:
    supervisors = ["All"] + list(df["Supervisor"].dropna().unique())
    selected_sup = st.selectbox("Filter by Supervisor", supervisors)

    if selected_sup != "All":
      filtered_df = df[df["Supervisor"] == selected_sup]
    else:
      filtered_df = df
  else:
      filtered_df = df

  st.dataframe(filtered_df, use_container_width=True)

else:
  st.info(
      "👉 Please upload your WFM raw data file using the sidebar option on the"
      " left to view the report."
  )