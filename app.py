import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="WFM Performance Dashboard", page_icon="📊", layout="wide"
)

st.title("📈 WFM Daily Performance Dashboard")
st.markdown("---")


# Load data automatically from the repository files
@st.cache_data
def load_data():
  try:
    # Yahan apni file ka naam likhein jo aap GitHub par upload karenge (jaise 'wfm_data.xlsx' ya 'wfm_data.csv')
    return pd.read_excel("wfm_data.xlsx")
  except Exception as e:
    try:
      return pd.read_csv("wfm_data.csv")
    except Exception as ex:
      return None


df = load_data()

if df is not None:
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
  st.error(
      "⚠️ Data file not found in repository! Please upload your data file"
      " (`wfm_data.xlsx` or `wfm_data.csv`) to your GitHub repository."
  )