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

# ========== Compute Overdue and Traffic Light ==========
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

    def assign_traffic(row):
        if row["Computed Status"] == "Completed":
            return "Blue"
        elif row["Computed Status"] == "Overdue":
            return "Red"
        elif row["Computed Status"] == "In Progress":
            due_soon = pd.to_datetime(row["Target Completion Date"]).date() in next_5_working_days(today)
            return "Yellow" if due_soon else "Green"
        else:
            return "Green"

    df["Computed Traffic Light"] = df.apply(assign_traffic, axis=1)
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

# ========== Manage Existing Projects ==========
st.header("🛠 Manage Existing Projects")

if not st.session_state.projects.empty:
    selected_project = st.selectbox("Select a Project to Edit / Mark Completed", st.session_state.projects["Project Name"])

    project_index = st.session_state.projects.index[st.session_state.projects["Project Name"] == selected_project][0]
    selected_project_data = st.session_state.projects.loc[project_index]

    with st.form(key="edit_project_form"):
        edit_project_name = st.text_input("Edit Project Name", selected_project_data["Project Name"])
        edit_officer = st.text_input("Edit Officer", selected_project_data["Officer"])
        edit_status = st.selectbox("Edit Status", ["Not Started", "In Progress", "Completed"], index=["Not Started", "In Progress", "Completed"].index(selected_project_data["Status"]))
        edit_start_date = st.date_input("Edit Start Date", selected_project_data["Start Date"])
        edit_target_date = st.date_input("Edit Target Completion Date", selected_project_data["Target Completion Date"])
        edit_remarks = st.text_area("Edit Remarks", selected_project_data["Remarks"])

        update_button = st.form_submit_button(label="Update Project")

        if update_button:
            st.session_state.projects.at[project_index, "Project Name"] = edit_project_name
            st.session_state.projects.at[project_index, "Officer"] = edit_officer
            st.session_state.projects.at[project_index, "Status"] = edit_status
            st.session_state.projects.at[project_index, "Start Date"] = edit_start_date
            st.session_state.projects.at[project_index, "Target Completion Date"] = edit_target_date
            st.session_state.projects.at[project_index, "Remarks"] = edit_remarks
            st.session_state.projects.at[project_index, "Last Update"] = today
            save_projects(st.session_state.projects)
            st.success(f"✅ Project '{edit_project_name}' updated successfully!")
            st.experimental_rerun()

    if st.button("✅ Mark as Completed"):
        st.session_state.projects.at[project_index, "Status"] = "Completed"
        st.session_state.projects.at[project_index, "Last Update"] = today
        save_projects(st.session_state.projects)
        st.success(f"🎯 Project '{selected_project}' marked as Completed!")
        st.experimental_rerun()

else:
    st.info("No projects available yet. Add a new project first.")

# ========== Style DataFrames ==========
def color_rows(row):
    if row["Computed Traffic Light"] == "Red":
        return ['background-color: red']*len(row)
    elif row["Computed Traffic Light"] == "Yellow":
        return ['background-color: yellow']*len(row)
    elif row["Computed Traffic Light"] == "Green":
        return ['background-color: lightgreen']*len(row)
    elif row["Computed Traffic Light"] == "Blue":
        return ['background-color: lightblue']*len(row)
    else:
        return ['']*len(row)

# ========== Sections: Overdue / Upcoming / Other In Progress ==========
st.header("⏰ Overdue Projects")
overdue_projects = st.session_state.projects[st.session_state.projects["Computed Status"] == "Overdue"]

if not overdue_projects.empty:
    st.dataframe(overdue_projects.style.apply(color_rows, axis=1))
else:
    st.success("🎉 No overdue projects!")

st.header("🚨 Projects Due in the Next 5 Working Days")
st.info("📢 Only projects with deadlines in the next 5 working days are shown below.")

upcoming_days = next_5_working_days(today)
upcoming_projects = st.session_state.projects[
    (st.session_state.projects["Computed Status"] == "In Progress") &
    (pd.to_datetime(st.session_state.projects["Target Completion Date"]).dt.date.isin(upcoming_days))
]

if not upcoming_projects.empty:
    st.dataframe(upcoming_projects.style.apply(color_rows, axis=1))
else:
    st.success("🎉 No upcoming deadlines within the next 5 working days!")

st.header("🛠 Other Projects Still In Progress")
other_in_progress_projects = st.session_state.projects[
    (st.session_state.projects["Computed Status"] == "In Progress") &
    (~pd.to_datetime(st.session_state.projects["Target Completion Date"]).dt.date.isin(upcoming_days)) &
    (pd.to_datetime(st.session_state.projects["Target Completion Date"]).dt.date > today)
]

if not other_in_progress_projects.empty:
    st.dataframe(other_in_progress_projects.style.apply(color_rows, axis=1))
else:
    st.success("🎉 No other ongoing projects.")

# ========== Gantt Chart ==========
st.header("🗓 Gantt Chart View")

if not st.session_state.projects.empty:

    st.markdown("""
    ### 📖 How to Read the Gantt Chart
    - **Blue** = Completed Projects
    - **Green** = In Progress Projects
    - **Yellow** = Projects Due within the Next 5 Working Days
    - **Red** = Overdue Projects

    ### 🔍 How to Use the Filter
    - Use the dropdown menu below to **select** which types of projects (by status) you want to view on the Gantt chart.
    - You can select **one or multiple statuses**.
    """)

    gantt_data = st.session_state.projects.copy()

    def categorize_project(row):
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

    gantt_data["Project Category"] = gantt_data.apply(categorize_project, axis=1)

    selected_status = st.multiselect(
        "Filter by Project Status",
        options=["Completed", "In Progress", "Due Soon", "Overdue"],
        default=["Completed", "In Progress", "Due Soon", "Overdue"]
    )

    gantt_data = gantt_data[gantt_data["Project Category"].isin(selected_status)]

    gantt_data["Start"] = pd.to_datetime(gantt_data["Start Date"]).dt.date
    gantt_data["Finish"] = pd.to_datetime(gantt_data["Target Completion Date"]).dt.date
    gantt_data = gantt_data.sort_values("Start")

    color_discrete_map = {
        "Completed": "blue",
        "In Progress": "green",
        "Due Soon": "yellow",
        "Overdue": "red"
    }

    fig = px.timeline(
        gantt_data,
        x_start="Start",
        x_end="Finish",
        y="Project Name",
        color="Project Category",
        title="Project Gantt Chart",
        color_discrete_map=color_discrete_map,
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No project data to show in Gantt chart yet.")
