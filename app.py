import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os

# ========== File paths ==========
DATA_FILE_PROJECTS = "projects_data.csv"

# ========== Load and Save ==========
def load_projects():
    if os.path.exists(DATA_FILE_PROJECTS):
        return pd.read_csv(DATA_FILE_PROJECTS, parse_dates=["Start Date", "Target Completion Date", "Last Update"])
    else:
        return pd.DataFrame(columns=[
            "Project Name", "Officer", "Status",
            "Start Date", "Target Completion Date", "Last Update", "Remarks"
        ])

def save_projects(df):
    df.to_csv(DATA_FILE_PROJECTS, index=False)

# ========== App Initialization ==========
if "projects" not in st.session_state:
    st.session_state.projects = load_projects()

st.title("📋 Project Management System")

today = datetime.date.today()

# ========== Compute Status and Traffic Light ==========
def next_5_working_days(start_date):
    days = []
    date = start_date
    while len(days) < 5:
        date += datetime.timedelta(days=1)
        if date.weekday() < 5:
            days.append(date)
    return days

def compute_status_and_traffic(df):
    df = df.copy()
    df["Computed Status"] = df["Status"]
    overdue_mask = (df["Status"] != "Completed") & (pd.to_datetime(df["Target Completion Date"]).dt.date < today)
    df.loc[overdue_mask, "Computed Status"] = "Overdue"

    def categorize(row):
        if row["Computed Status"] == "Completed":
            return "Completed"
        elif row["Computed Status"] == "Overdue":
            return "Overdue"
        elif row["Computed Status"] == "In Progress":
            if pd.to_datetime(row["Target Completion Date"]).date() in next_5_working_days(today):
                return "Due Soon"
            else:
                return "In Progress"
        else:
            return "In Progress"

    df["Project Category"] = df.apply(categorize, axis=1)

    def assign_traffic(cat):
        if cat == "Completed":
            return "Blue"
        elif cat == "Overdue":
            return "Red"
        elif cat == "Due Soon":
            return "Yellow"
        elif cat == "In Progress":
            return "Green"
        else:
            return "Green"

    df["Computed Traffic Light"] = df["Project Category"].apply(assign_traffic)
    return df

st.session_state.projects = compute_status_and_traffic(st.session_state.projects)

# ========== Sidebar: Add New Project ==========
st.sidebar.header("➕ Add New Project")
with st.sidebar.form(key="add_project_form"):
    project_name = st.text_input("Project Name")
    officer = st.text_input("Responsible Officer")
    status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
    start_date = st.date_input("Start Date", datetime.date.today())
    target_date = st.date_input("Target Completion Date")
    remarks = st.text_area("Remarks")

    add_button = st.form_submit_button(label="Add Project")

    if add_button:
        new_project = {
            "Project Name": project_name,
            "Officer": officer,
            "Status": status,
            "Start Date": start_date,
            "Target Completion Date": target_date,
            "Last Update": today,
            "Remarks": remarks
        }
        st.session_state.projects = pd.concat(
            [st.session_state.projects, pd.DataFrame([new_project])],
            ignore_index=True
        )
        save_projects(st.session_state.projects)
        st.success(f"✅ Project '{project_name}' added successfully!")
        st.experimental_rerun()

# Note: Continuing below...
