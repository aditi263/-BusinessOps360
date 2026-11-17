
import streamlit as st


from database import get_engine
from sqlalchemy import text

def get_ticket_count():
    with get_engine().connect() as connection:
        return connection.execute(
            text("SELECT COUNT(*) FROM tickets")
        ).scalar_one()

st.set_page_config(
    page_title="BusinessOps 360",
    page_icon="📊",
    layout="wide"
)

st.title("BusinessOps 360")
st.subheader("Enterprise Operations & IT Service Management")

st.write(
    "An interactive platform for tracking business "
    "applications, IT support tickets, and operational performance."
)

col1, col2, col3 = st.columns(3)

with col1:
   st.metric("Total Tickets", get_ticket_count())

with col2:
    st.metric("Business Applications", 5)

with col3:
    st.metric("Employees", 5)

st.divider()
st.success("BusinessOps 360 application is running!")
from database import get_engine
from sqlalchemy import text
import pandas as pd

st.subheader("IT Support Tickets")

with get_engine().connect() as connection:
    tickets = pd.read_sql(
        text("SELECT * FROM tickets"),
        connection
    )

st.dataframe(tickets, use_container_width=True)
st.subheader("Ticket Status Analysis")

status_counts = tickets["status"].value_counts()

st.bar_chart(status_counts)
st.subheader("Interactive Ticket Explorer")

col1, col2 = st.columns(2)

with col1:
    selected_status = st.selectbox(
        "Filter by Status",
        ["All"] + sorted(tickets["status"].dropna().unique().tolist())
    )

with col2:
    selected_priority = st.selectbox(
        "Filter by Priority",
        ["All"] + sorted(tickets["priority"].dropna().unique().tolist())
    )

filtered_tickets = tickets.copy()

if selected_status != "All":
    filtered_tickets = filtered_tickets[
        filtered_tickets["status"] == selected_status
    ]

if selected_priority != "All":
    filtered_tickets = filtered_tickets[
        filtered_tickets["priority"] == selected_priority
    ]

st.metric("Matching Tickets", len(filtered_tickets))

st.dataframe(filtered_tickets, use_container_width=True)

# DAY 2: SLA Monitoring

st.divider()
st.header("SLA Monitoring")

sla_data = tickets.copy()
sla_data["due_at"] = pd.to_datetime(sla_data["due_at"])

current_time = pd.Timestamp.now()

sla_data["is_overdue"] = (
    ~sla_data["status"].isin(["Resolved", "Closed"])
    & sla_data["due_at"].notna()
    & (sla_data["due_at"] < current_time)
)

overdue_tickets = sla_data[sla_data["is_overdue"]]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Tickets", len(sla_data))

with col2:
    st.metric("Overdue Tickets", len(overdue_tickets))

with col3:
    st.metric(
        "Within Deadline / Completed",
        len(sla_data) - len(overdue_tickets)
    )

st.subheader("Overdue Ticket Details")

if overdue_tickets.empty:
    st.success("No overdue tickets!")
else:
    st.error(f"{len(overdue_tickets)} tickets are overdue!")

    st.dataframe(
        overdue_tickets[
            ["ticket_id", "title", "priority", "status", "due_at"]
        ],
       width="stretch"
    )

# DAY 7: SLA Compliance Dashboard

st.divider()
st.header("SLA Compliance Dashboard")

sla_dashboard = sla_data.copy()

sla_dashboard["sla_status"] = "On Track"

sla_dashboard.loc[
    sla_dashboard["status"].isin(["Resolved", "Closed"]),
    "sla_status"
] = "Completed"

sla_dashboard.loc[
    sla_dashboard["is_overdue"],
    "sla_status"
] = "Overdue"

approaching = (
    ~sla_dashboard["status"].isin(["Resolved", "Closed"])
    & ~sla_dashboard["is_overdue"]
    & sla_dashboard["due_at"].notna()
    & (sla_dashboard["due_at"] <= current_time + pd.Timedelta(hours=24))
)

sla_dashboard.loc[
    approaching,
    "sla_status"
] = "Approaching Deadline"

st.subheader("SLA Status Overview")

st.bar_chart(
    sla_dashboard["sla_status"].value_counts()
)

st.dataframe(
    sla_dashboard[
        ["ticket_id", "title", "priority", "status", "due_at", "sla_status"]
    ],
    use_container_width=True,
    hide_index=True
)


# DAY 7: Ticket Escalation Monitor

st.divider()
st.header("Ticket Escalation Monitor")

def escalation_level(row):
    if row["sla_status"] == "Overdue":
        return "Escalate Immediately"
    elif row["sla_status"] == "Approaching Deadline":
        return "Escalation Warning"
    elif row["sla_status"] == "Completed":
        return "No Action - Completed"
    else:
        return "No Escalation Needed"

escalation_data = sla_dashboard.copy()

escalation_data["escalation_level"] = escalation_data.apply(
    escalation_level,
    axis=1
)

urgent_tickets = escalation_data[
    escalation_data["escalation_level"].isin([
        "Escalate Immediately",
        "Escalation Warning"
    ])
]

st.metric("Tickets Requiring Attention", len(urgent_tickets))

st.dataframe(
    urgent_tickets[
        [
            "ticket_id",
            "title",
            "priority",
            "status",
            "due_at",
            "escalation_level"
        ]
    ],
    hide_index=True,
    use_container_width=True
)


# DAY 7: Ticket Assignment Management

st.divider()
st.header("Ticket Assignment Management")

with get_engine().connect() as connection:
    available_tickets = pd.read_sql(
        text("""
            SELECT ticket_id, title
            FROM tickets
            WHERE status NOT IN ('Resolved', 'Closed')
            ORDER BY ticket_id
        """),
        connection
    )

    support_employees = pd.read_sql(
        text("""
            SELECT employee_id, full_name
            FROM employees
            WHERE department = 'IT'
            ORDER BY full_name
        """),
        connection
    )

if available_tickets.empty or support_employees.empty:
    st.info("No active tickets or IT employees available.")
else:
    ticket_options = dict(
        zip(
            available_tickets["ticket_id"],
            available_tickets["title"]
        )
    )

    employee_options = dict(
        zip(
            support_employees["employee_id"],
            support_employees["full_name"]
        )
    )

    with st.form("assign_ticket_form"):
        selected_ticket = st.selectbox(
            "Select Support Ticket",
            options=list(ticket_options.keys()),
            format_func=lambda x: f"#{x} - {ticket_options[x]}"
        )

        selected_employee = st.selectbox(
            "Assign to IT Employee",
            options=list(employee_options.keys()),
            format_func=lambda x: employee_options[x]
        )

        assign_clicked = st.form_submit_button("Assign Ticket")

 
    if assign_clicked:
        try:
            with get_engine().begin() as connection:
                result = connection.execute(
                    text("""
                        UPDATE tickets
                        SET assigned_to = :employee_id
                        WHERE ticket_id = :ticket_id
                        AND status NOT IN ('Resolved', 'Closed')
                    """),
                    {
                        "employee_id": int(selected_employee),
                        "ticket_id": int(selected_ticket)
                    }
                )

            st.write("Rows updated:", result.rowcount)

            if result.rowcount == 1:
                st.success(
                    f"Ticket #{selected_ticket} assigned to "
                    f"{employee_options[selected_employee]}!"
                )
            else:
                st.warning("No ticket was updated.")

        except Exception as e:
            st.error(f"Assignment failed: {e}")



# DAY 2: Upcoming Deadline Alerts

st.divider()
st.subheader("Upcoming Deadline Alerts")

active_tickets = sla_data[
    ~sla_data["status"].isin(["Resolved", "Closed"])
].copy()

upcoming_tickets = active_tickets[
    (active_tickets["due_at"] >= current_time)
    & (
        active_tickets["due_at"]
        <= current_time + pd.Timedelta(hours=24)
    )
]

if upcoming_tickets.empty:
    st.success("No tickets approaching their deadline.")
else:
    st.warning(
        f"{len(upcoming_tickets)} tickets are due within 24 hours!"
    )

    st.dataframe(
        upcoming_tickets[
            ["ticket_id", "title", "priority", "status", "due_at"]
        ],
        width="stretch"
    )

import streamlit as st



st.subheader("Create New Support Ticket")


with st.form("new_ticket_form"):
    employee_id = st.number_input(
        "Employee ID",
        min_value=1,
        step=1
    )

    application_id = st.number_input(
        "Application ID",
        min_value=1,
        step=1
    )

    ticket_title = st.text_input("Ticket Title")

    description = st.text_area(
        "Describe the Issue"
    )

    priority = st.selectbox(
        "Priority",
        ["Low", "Medium", "High", "Critical"]
    )

    status = st.selectbox(
        "Status",
        ["Open", "In Progress", "Resolved"]
    )

    submitted = st.form_submit_button(
        "Create Ticket"
    )

    
    if submitted:
        if ticket_title.strip() and description.strip():
            try:
                with get_engine().begin() as connection:
                    new_ticket_id = connection.execute(
                        text("""
                            INSERT INTO tickets (
                                employee_id,
                                application_id,
                                title,
                                description,
                                priority,
                                status,
                                due_at
                            )
                            VALUES (
                                :employee_id,
                                :application_id,
                                :title,
                                :description,
                                :priority,
                                :status,
                                CASE
    WHEN :priority = 'Critical' THEN CURRENT_TIMESTAMP + INTERVAL '4 hours'
    WHEN :priority = 'High' THEN CURRENT_TIMESTAMP + INTERVAL '8 hours'
    WHEN :priority = 'Medium' THEN CURRENT_TIMESTAMP + INTERVAL '24 hours'
    WHEN :priority = 'Low' THEN CURRENT_TIMESTAMP + INTERVAL '72 hours'
END
                            )
                            RETURNING ticket_id
                        """),
                        {
                            "employee_id": int(employee_id),
                            "application_id": int(application_id),
                            "title": ticket_title.strip(),
                            "description": description.strip(),
                            "priority": priority,
                            "status": status
                        }
                    ).scalar_one()

                st.success(
                    f"Ticket #{new_ticket_id} created successfully!"
                )

            except Exception as e:
                st.error(f"Unable to create ticket: {e}")
        else:
            st.error("Please enter a title and description.")


# DAY 3: Update Existing Ticket Status

st.divider()
st.header("Update Ticket Status")

if tickets.empty:
    st.info("No tickets available to update.")
else:
    selected_ticket_id = st.selectbox(
        "Select Ticket ID",
        tickets["ticket_id"].tolist()
    )

    new_status = st.selectbox(
        "Choose New Status",
        ["Open", "In Progress", "Resolved", "Closed"]
    )
    if st.button("Update Ticket"):
        try:
            with get_engine().begin() as connection:

                # Get current ticket status
                old_status = connection.execute(
                    text("""
                        SELECT status
                        FROM tickets
                        WHERE ticket_id = :ticket_id
                        FOR UPDATE
                    """),
                    {"ticket_id": int(selected_ticket_id)}
                ).scalar_one_or_none()

                if old_status is None:
                    st.warning("Ticket not found.")

                elif old_status == new_status:
                    st.info("Ticket already has this status.")

                else:
                    # Update ticket
                    connection.execute(
                        text("""
                            UPDATE tickets
                            SET status = :new_status
                            WHERE ticket_id = :ticket_id
                        """),
                        {
                            "new_status": new_status,
                            "ticket_id": int(selected_ticket_id)
                        }
                    )

                    # Record the change
                    connection.execute(
                        text("""
                            INSERT INTO ticket_history
                            (ticket_id, old_status, new_status)
                            VALUES
                            (:ticket_id, :old_status, :new_status)
                        """),
                        {
                            "ticket_id": int(selected_ticket_id),
                            "old_status": old_status,
                            "new_status": new_status
                        }
                    )

            if old_status is not None and old_status != new_status:
                st.rerun()

        except Exception as e:
            st.error(f"Unable to update ticket: {e}")

# DAY 3: Ticket Activity History

st.divider()
st.header("Ticket Activity History")

with get_engine().connect() as connection:
    history = pd.read_sql(
        text("""
            SELECT
                h.history_id,
                h.ticket_id,
                t.title AS ticket_title,
                h.old_status,
                h.new_status,
                h.changed_at
            FROM ticket_history h
            JOIN tickets t
                ON h.ticket_id = t.ticket_id
            ORDER BY h.changed_at DESC, h.history_id DESC
        """),
        connection
    )

if history.empty:
    st.info("No ticket activity recorded yet.")
else:
    st.metric("Total Status Changes", len(history))

    st.dataframe(
        history,
        use_container_width=True,
        hide_index=True
    )

# DAY 4: Employee Directory

st.divider()
st.header("Employee Directory")

with get_engine().connect() as connection:
    employees = pd.read_sql(
        text("SELECT * FROM employees"),
        connection
    )

st.metric("Total Employees", len(employees))

st.dataframe(
    employees,
    use_container_width=True,
    hide_index=True
)

# DAY 4: Business Applications Directory

st.divider()
st.header("Business Applications Directory")

with get_engine().connect() as connection:
    applications = pd.read_sql(
        text("SELECT * FROM applications"),
        connection
    )

st.metric("Total Business Applications", len(applications))

st.dataframe(
    applications,
    use_container_width=True,
    hide_index=True
)

# DAY 4: Employee and Application Search

st.divider()
st.header("Employee & Application Search")

search_employee = st.text_input(
    "Search Employees",
    placeholder="Enter employee name, department, or email"
)

if search_employee:
    employee_results = employees[
        employees.astype(str).apply(
            lambda col: col.str.contains(
                search_employee,
                case=False,
                regex=False,
                na=False
            )
        ).any(axis=1)
    ]
else:
    employee_results = employees

st.subheader("Employee Results")
st.dataframe(
    employee_results,
    use_container_width=True,
    hide_index=True
)

search_application = st.text_input(
    "Search Business Applications",
    placeholder="Enter application name or keyword"
)

if search_application:
    application_results = applications[
        applications.astype(str).apply(
            lambda col: col.str.contains(
                search_application,
                case=False,
                regex=False,
                na=False
            )
        ).any(axis=1)
    ]
else:
    application_results = applications

st.subheader("Application Results")
st.dataframe(
    application_results,
    use_container_width=True,
    hide_index=True
)

# DAY 5: Executive Operations Dashboard

st.divider()
st.header("Executive Operations Dashboard")

# Calculate KPIs using current database records
total_tickets = len(tickets)

open_tickets = len(
    tickets[tickets["status"] == "Open"]
)

resolved_tickets = len(
    tickets[tickets["status"].isin(["Resolved", "Closed"])]
)

overdue_count = len(overdue_tickets)

resolution_rate = (
    resolved_tickets / total_tickets * 100
    if total_tickets > 0 else 0
)

# Display executive KPIs
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric("Total Tickets", total_tickets)

with kpi2:
    st.metric("Open Tickets", open_tickets)

with kpi3:
    st.metric("Resolved Tickets", resolved_tickets)

with kpi4:
    st.metric("Overdue Tickets", overdue_count)

with kpi5:
    st.metric(
        "Resolution Rate",
        f"{resolution_rate:.1f}%"
    )

# DAY 5: Executive Analytics Charts

st.subheader("Executive Ticket Analytics")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.write("Tickets by Priority")

    priority_counts = (
        tickets["priority"]
        .value_counts()
        .rename_axis("Priority")
        .reset_index(name="Tickets")
    )

    st.bar_chart(
        priority_counts,
        x="Priority",
        y="Tickets"
    )

with chart_col2:
    st.write("Tickets by Status")

    status_summary = (
        tickets["status"]
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Tickets")
    )

    st.bar_chart(
        status_summary,
        x="Status",
        y="Tickets"
    )

# DAY 5: Downloadable Operations Report

st.divider()
st.header("Download Operations Report")

st.write(
    "Export the latest IT support ticket data "
    "for operational analysis and reporting."
)

# Retrieve the latest records from PostgreSQL
with get_engine().connect() as connection:
    report_data = pd.read_sql(
        text("SELECT * FROM tickets ORDER BY ticket_id"),
        connection
    )

# Convert records to CSV
csv_data = report_data.to_csv(index=False).encode("utf-8")

st.download_button(
    label="📥 Download Ticket Report (CSV)",
    data=csv_data,
    file_name="BusinessOps360_Ticket_Report.csv",
    mime="text/csv"
)

st.caption(
    f"Report contains {len(report_data)} tickets."
)


    