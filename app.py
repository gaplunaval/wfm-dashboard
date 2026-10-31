import tkinter as tk
from tkinter import filedialog
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="WFM Performance Dashboard", page_icon="📊", layout="wide"
)


# Function to select file via popup window
def get_file_path():
  root = tk.Tk()
  root.withdraw()  # Hide the main tkinter window
  root.attributes("-topmost", True)  # Bring dialog to the front
  file_path = filedialog.askopenfilename(
      title="Select WFM Raw Data File",
      filetypes=[("Excel Files", "*.xlsx *.xls"), ("CSV Files", "*.csv")],
  )
  return file_path


# Sidebar for file loading
st.sidebar.header("📁 Data Source")
if "df" not in st.session_state:
  st.session_state.df = None

if st.sidebar.button("Browse & Select File from PC"):
  path = get_file_path()
  if path:
    try:
      if path.endswith(".csv"):
        st.session_state.df = pd.read_csv(path)
      else:
        st.session_state.df = pd.read_excel(path)
      st.sidebar.success("File successfully loaded!")
    except Exception as e:
      st.sidebar.error(f"Error loading file: {e}")
  else:
      st.sidebar.warning("No file selected.")

# Main Dashboard Logic
df = st.session_state.df

if df is not None:
  st.title("📈 WFM Daily Performance Dashboard")
  st.markdown("---")

  # Display raw data preview option
  if st.checkbox("Show Raw Data Preview"):
    st.dataframe(df.head(10))

  # Summary Metrics Cards / KPIs
  st.subheader("📊 Operational Summary")

  # Assuming column names match your raw data fields (Agent, Supervisor, Calls, Login, Shrinkage, etc.)
  # You can adjust column names here based on your actual file columns
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
      "👉 Please click the **'Browse & Select File from PC'** button in the"
      " sidebar to upload your OneDrive/Local raw data file and view the"
      " report."
  )