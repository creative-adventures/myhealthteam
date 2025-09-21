import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src import database as db

def display_coordinator_monthly_summary(coordinator_id=None, show_all=False, title="Coordinator Monthly Summary"):
    """Display coordinator monthly performance summary"""
    st.subheader(title)
    
    conn = db.get_db_connection()
    try:
        if show_all:
            # Admin view - show all coordinators
            query = """
                SELECT 
                    cms.coordinator_id,
                    u.full_name as coordinator_name,
                    cms.year,
                    cms.month,
                    cms.total_minutes,
                    cms.total_minutes_per_patient,
                    cms.total_tasks_completed,
                    cms.average_daily_tasks,
                    cms.created_date
                FROM dashboard_coordinator_monthly_summary cms
                JOIN coordinators c ON cms.coordinator_id = c.coordinator_id
                JOIN users u ON c.user_id = u.user_id
                ORDER BY cms.year DESC, cms.month DESC, u.full_name
                LIMIT 100
            """
            data = conn.execute(query).fetchall()
        else:
            # Individual coordinator view
            query = """
                SELECT 
                    cms.coordinator_id,
                    u.full_name as coordinator_name,
                    cms.year,
                    cms.month,
                    cms.total_minutes,
                    cms.total_minutes_per_patient,
                    cms.total_tasks_completed,
                    cms.average_daily_tasks,
                    cms.created_date
                FROM dashboard_coordinator_monthly_summary cms
                JOIN coordinators c ON cms.coordinator_id = c.coordinator_id
                JOIN users u ON c.user_id = u.user_id
                WHERE cms.coordinator_id = ?
                ORDER BY cms.year DESC, cms.month DESC
                LIMIT 12
            """
            data = conn.execute(query, (coordinator_id,)).fetchall()
        
        if data:
            df = pd.DataFrame([dict(row) for row in data])
            
            # Format the data for display
            df['period'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
            df['avg_minutes_per_task'] = df['total_minutes'] / df['total_tasks_completed']
            df['avg_minutes_per_task'] = df['avg_minutes_per_task'].fillna(0).round(2)
            
            # Display metrics
            if not show_all:
                col1, col2, col3, col4 = st.columns(4)
                latest = df.iloc[0]
                col1.metric("Total Minutes (Latest Month)", f"{latest['total_minutes']:.0f}")
                col2.metric("Tasks Completed", f"{latest['total_tasks_completed']:.0f}")
                col3.metric("Avg Daily Tasks", f"{latest['average_daily_tasks']:.1f}")
                col4.metric("Avg Minutes per Patient", f"{latest['total_minutes_per_patient']:.1f}")
            
            # Display table with human-readable column names
            display_df = df[['period', 'coordinator_name', 'total_minutes', 'total_tasks_completed', 
                          'average_daily_tasks', 'total_minutes_per_patient', 'avg_minutes_per_task']].copy()
            
            # Rename columns to be more human-readable
            display_df.columns = ['Period', 'Coordinator', 'Total Minutes', 'Tasks Completed', 
                                'Avg Daily Tasks', 'Minutes per Patient', 'Minutes per Task']
            
            # Configure columns for better display
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "Period": st.column_config.TextColumn("Period", width="small"),
                    "Coordinator": st.column_config.TextColumn("Coordinator", width="medium"),
                    "Total Minutes": st.column_config.NumberColumn("Total Minutes", format="%.0f"),
                    "Tasks Completed": st.column_config.NumberColumn("Tasks Completed", format="%.0f"),
                    "Avg Daily Tasks": st.column_config.NumberColumn("Avg Daily Tasks", format="%.1f"),
                    "Minutes per Patient": st.column_config.NumberColumn("Minutes per Patient", format="%.1f"),
                    "Minutes per Task": st.column_config.NumberColumn("Minutes per Task", format="%.1f"),
                },
                hide_index=True
            )
        else:
            st.info("No coordinator monthly summary data available.")
            
    except Exception as e:
        st.error(f"Error loading coordinator monthly summary: {e}")
    finally:
        conn.close()

def display_coordinator_weekly_summary(coordinator_id=None, show_all=False, title="Coordinator Weekly Summary"):
    """Display coordinator weekly performance summary (placeholder - table doesn't exist yet)"""
    st.subheader(title)
    st.info("⚠️ Coordinator weekly summary table not yet implemented in database schema.")
    
    # This would be the implementation when the table exists:
    # Similar structure to monthly but with weekly data from coordinator_weekly_summary table

def display_provider_monthly_summary(provider_id=None, show_all=False, title="Provider Monthly Summary"):
    """Display provider monthly performance summary"""
    st.subheader(title)
    
    conn = db.get_db_connection()
    try:
        if show_all:
            # Admin/CPM view - show all providers or providers under CPM
            query = """
                SELECT 
                    pms.provider_id,
                    u.full_name as provider_name,
                    pms.year,
                    pms.month,
                    pms.total_tasks_completed,
                    pms.total_time_spent_minutes,
                    pms.total_patients_served,
                    pms.max_patients_allowed,
                    pms.patients_assigned,
                    pms.average_task_completion_time_minutes,
                    pms.created_date
                FROM dashboard_provider_monthly_summary pms
                JOIN providers p ON pms.provider_id = p.provider_id
                JOIN users u ON p.user_id = u.user_id
                ORDER BY pms.year DESC, pms.month DESC, u.full_name
                LIMIT 100
            """
            data = conn.execute(query).fetchall()
        else:
            # Individual provider view
            query = """
                SELECT 
                    pms.provider_id,
                    u.full_name as provider_name,
                    pms.year,
                    pms.month,
                    pms.total_tasks_completed,
                    pms.total_time_spent_minutes,
                    pms.total_patients_served,
                    pms.max_patients_allowed,
                    pms.patients_assigned,
                    pms.average_task_completion_time_minutes,
                    pms.created_date
                FROM dashboard_provider_monthly_summary pms
                JOIN providers p ON pms.provider_id = p.provider_id
                JOIN users u ON p.user_id = u.user_id
                WHERE pms.provider_id = ?
                ORDER BY pms.year DESC, pms.month DESC
                LIMIT 12
            """
            data = conn.execute(query, (provider_id,)).fetchall()
        
        if data:
            df = pd.DataFrame([dict(row) for row in data])
            
            # Format the data for display
            df['period'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
            df['utilization_rate'] = ((df['patients_assigned'] / df['max_patients_allowed']) * 100).round(1)
            df['utilization_rate'] = df['utilization_rate'].fillna(0)
            
            # Display metrics
            if not show_all:
                col1, col2, col3, col4 = st.columns(4)
                latest = df.iloc[0]
                col1.metric("Tasks Completed (Latest)", f"{latest['total_tasks_completed']:.0f}")
                col2.metric("Total Minutes", f"{latest['total_time_spent_minutes']:.0f}")
                col3.metric("Patients Served", f"{latest['total_patients_served']:.0f}")
                col4.metric("Utilization Rate", f"{latest['utilization_rate']:.1f}%")
            
            # Display table with human-readable column names
            display_df = df[['period', 'provider_name', 'total_tasks_completed', 'total_time_spent_minutes',
                          'total_patients_served', 'patients_assigned', 'max_patients_allowed', 'utilization_rate']].copy()
            
            # Rename columns to be more human-readable
            display_df.columns = ['Period', 'Provider', 'Tasks Completed', 'Total Minutes',
                                'Patients Served', 'Patients Assigned', 'Max Capacity', 'Utilization %']
            
            # Configure columns for better display
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "Period": st.column_config.TextColumn("Period", width="small"),
                    "Provider": st.column_config.TextColumn("Provider", width="medium"),
                    "Tasks Completed": st.column_config.NumberColumn("Tasks Completed", format="%.0f"),
                    "Total Minutes": st.column_config.NumberColumn("Total Minutes", format="%.0f"),
                    "Patients Served": st.column_config.NumberColumn("Patients Served", format="%.0f"),
                    "Patients Assigned": st.column_config.NumberColumn("Patients Assigned", format="%.0f"),
                    "Max Capacity": st.column_config.NumberColumn("Max Capacity", format="%.0f"),
                    "Utilization %": st.column_config.NumberColumn("Utilization %", format="%.1f%%"),
                },
                hide_index=True
            )
        else:
            st.info("No provider monthly summary data available.")
            
    except Exception as e:
        st.error(f"Error loading provider monthly summary: {e}")
    finally:
        conn.close()

def display_provider_weekly_summary(provider_id=None, show_all=False, title="Provider Weekly Summary"):
    """Display provider weekly performance summary"""
    st.subheader(title)
    
    # Check if current user is admin to show payment status
    is_admin = False
    if 'user_email' in st.session_state:
        is_admin = st.session_state.user_email == 'admin@myhealthteam.org'
    
    conn = db.get_db_connection()
    try:
        if show_all:
            # Admin/CPM view - show all providers
            query = """
                SELECT 
                    pws.provider_id,
                    pws.provider_name,
                    pws.year,
                    pws.week_number,
                    pws.week_start_date,
                    pws.week_end_date,
                    pws.total_tasks_completed,
                    pws.total_time_spent_minutes,
                    pws.average_daily_minutes,
                    pws.days_active,
                    pws.paid,
                    pws.created_date
                FROM provider_weekly_summary pws
                ORDER BY pws.year DESC, pws.week_number DESC, pws.provider_name
                LIMIT 100
            """
            data = conn.execute(query).fetchall()
        else:
            # Individual provider view
            query = """
                SELECT 
                    pws.provider_id,
                    pws.provider_name,
                    pws.year,
                    pws.week_number,
                    pws.week_start_date,
                    pws.week_end_date,
                    pws.total_tasks_completed,
                    pws.total_time_spent_minutes,
                    pws.average_daily_minutes,
                    pws.days_active,
                    pws.paid,
                    pws.created_date
                FROM provider_weekly_summary pws
                WHERE pws.provider_id = ?
                ORDER BY pws.year DESC, pws.week_number DESC
                LIMIT 12
            """
            data = conn.execute(query, (provider_id,)).fetchall()
        
        if data:
            df = pd.DataFrame([dict(row) for row in data])
            
            # Format the data for display
            df['week_period'] = df['year'].astype(str) + '-W' + df['week_number'].astype(str).str.zfill(2)
            df['avg_minutes_per_day'] = df['average_daily_minutes'].round(1)
            df['payment_status'] = df['paid'].apply(lambda x: '✅ Paid' if x else '⏳ Pending')
            
            # Display metrics
            if not show_all:
                col1, col2, col3, col4 = st.columns(4)
                latest = df.iloc[0]
                col1.metric("Tasks (Latest Week)", f"{latest['total_tasks_completed']:.0f}")
                col2.metric("Total Minutes", f"{latest['total_time_spent_minutes']:.0f}")
                col3.metric("Days Active", f"{latest['days_active']:.0f}")
                col4.metric("Avg Daily Minutes", f"{latest['avg_minutes_per_day']:.1f}")
            
            # Display table with human-readable column names
            # Conditionally include payment status column only for admin
            if is_admin:
                display_cols = ['week_period', 'provider_name', 'week_start_date', 'week_end_date',
                              'total_tasks_completed', 'total_time_spent_minutes', 'days_active', 
                              'avg_minutes_per_day', 'payment_status']
                column_names = ['Week', 'Provider', 'Start Date', 'End Date',
                              'Tasks Completed', 'Total Minutes', 'Days Active', 
                              'Avg Minutes/Day', 'Payment Status']
            else:
                display_cols = ['week_period', 'provider_name', 'week_start_date', 'week_end_date',
                              'total_tasks_completed', 'total_time_spent_minutes', 'days_active', 
                              'avg_minutes_per_day']
                column_names = ['Week', 'Provider', 'Start Date', 'End Date',
                              'Tasks Completed', 'Total Minutes', 'Days Active', 
                              'Avg Minutes/Day']
            
            display_df = df[display_cols].copy()
            display_df.columns = column_names
            
            # Configure columns for better display
            if is_admin:
                column_config = {
                    "Week": st.column_config.TextColumn("Week", width="small"),
                    "Provider": st.column_config.TextColumn("Provider", width="medium"),
                    "Start Date": st.column_config.DateColumn("Start Date", width="small"),
                    "End Date": st.column_config.DateColumn("End Date", width="small"),
                    "Tasks Completed": st.column_config.NumberColumn("Tasks Completed", format="%.0f"),
                    "Total Minutes": st.column_config.NumberColumn("Total Minutes", format="%.0f"),
                    "Days Active": st.column_config.NumberColumn("Days Active", format="%.0f"),
                    "Avg Minutes/Day": st.column_config.NumberColumn("Avg Minutes/Day", format="%.1f"),
                    "Payment Status": st.column_config.TextColumn("Payment Status", width="small"),
                }
            else:
                column_config = {
                    "Week": st.column_config.TextColumn("Week", width="small"),
                    "Provider": st.column_config.TextColumn("Provider", width="medium"),
                    "Start Date": st.column_config.DateColumn("Start Date", width="small"),
                    "End Date": st.column_config.DateColumn("End Date", width="small"),
                    "Tasks Completed": st.column_config.NumberColumn("Tasks Completed", format="%.0f"),
                    "Total Minutes": st.column_config.NumberColumn("Total Minutes", format="%.0f"),
                    "Days Active": st.column_config.NumberColumn("Days Active", format="%.0f"),
                    "Avg Minutes/Day": st.column_config.NumberColumn("Avg Minutes/Day", format="%.1f"),
                }
            
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config=column_config,
                hide_index=True
            )
        else:
            st.info("No provider weekly summary data available.")
            
    except Exception as e:
        st.error(f"Error loading provider weekly summary: {e}")
    finally:
        conn.close()

def display_patient_assignments_by_workflow(user_id, role_id, title="Patient Assignments"):
    """Display patient assignments based on onboarding workflow"""
    st.subheader(title)
    
    conn = db.get_db_connection()
    try:
        if role_id in [33, 38]:  # Care Provider or Care Provider Manager
            # Show provider-related patient assignments
            query = """
                SELECT 
                    p.first_name,
                    p.last_name,
                    p.date_of_birth,
                    pa.assignment_date,
                    pa.assignment_type,
                    pa.status,
                    pa.priority_level,
                    r.region_name,
                    CASE 
                        WHEN op.stage1_complete = 0 THEN 'Initial Contact Needed'
                        WHEN op.stage2_complete = 0 THEN 'TV Visit Scheduled'
                        WHEN op.stage3_complete = 0 THEN 'Documentation Pending'
                        ELSE 'Ready for Care'
                    END as workflow_stage
                FROM patient_assignments pa
                JOIN patients p ON pa.patient_id = p.patient_id
                LEFT JOIN regions r ON p.region_id = r.region_id
                LEFT JOIN onboarding_patients op ON p.patient_id = op.patient_id
                WHERE pa.provider_id = ?
                ORDER BY pa.assignment_date DESC
                LIMIT 50
            """
            data = conn.execute(query, (user_id,)).fetchall()
            
        elif role_id in [36, 39, 40]:  # Care Coordinator roles
            # Show coordinator-related patient assignments
            query = """
                SELECT 
                    p.first_name,
                    p.last_name,
                    p.date_of_birth,
                    pa.assignment_date,
                    pa.assignment_type,
                    pa.status,
                    pa.priority_level,
                    r.region_name,
                    CASE 
                        WHEN op.stage1_complete = 0 THEN 'Initial Contact Needed'
                        WHEN op.stage2_complete = 0 THEN 'TV Visit Scheduling'
                        WHEN op.stage3_complete = 0 THEN 'Documentation Review'
                        ELSE 'Onboarding Complete'
                    END as workflow_stage
                FROM patient_assignments pa
                JOIN patients p ON pa.patient_id = p.patient_id
                LEFT JOIN regions r ON p.region_id = r.region_id
                LEFT JOIN onboarding_patients op ON p.patient_id = op.patient_id
                WHERE pa.coordinator_id = ?
                ORDER BY pa.assignment_date DESC
                LIMIT 50
            """
            data = conn.execute(query, (user_id,)).fetchall()
        else:
            st.warning("Role not supported for patient assignments view.")
            return
        
        if data:
            df = pd.DataFrame([dict(row) for row in data])
            
            # Create summary metrics
            col1, col2, col3, col4 = st.columns(4)
            total_patients = len(df)
            active_assignments = len(df[df['status'] == 'Active'])
            high_priority = len(df[df['priority_level'] == 'High'])
            pending_workflow = len(df[df['workflow_stage'] != 'Onboarding Complete'])
            
            col1.metric("Total Patients", total_patients)
            col2.metric("Active Assignments", active_assignments)
            col3.metric("High Priority", high_priority)
            col4.metric("Pending Workflow", pending_workflow)
            
            # Display the assignments table with human-readable column names
            display_df = df[['first_name', 'last_name', 'assignment_date', 'assignment_type',
                          'status', 'priority_level', 'region_name', 'workflow_stage']].copy()
            
            # Rename columns to be more human-readable
            display_df.columns = ['First Name', 'Last Name', 'Assignment Date', 'Type',
                                'Status', 'Priority', 'Region', 'Workflow Stage']
            
            # Configure columns for better display
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "First Name": st.column_config.TextColumn("First Name", width="small"),
                    "Last Name": st.column_config.TextColumn("Last Name", width="small"),
                    "Assignment Date": st.column_config.DateColumn("Assignment Date", width="small"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Priority": st.column_config.TextColumn("Priority", width="small"),
                    "Region": st.column_config.TextColumn("Region", width="small"),
                    "Workflow Stage": st.column_config.TextColumn("Workflow Stage", width="medium"),
                },
                hide_index=True
            )
            
            # Workflow stage breakdown
            if 'workflow_stage' in df.columns:
                stage_counts = df['workflow_stage'].value_counts()
                st.subheader("Workflow Stage Breakdown")
                for stage, count in stage_counts.items():
                    st.write(f"**{stage}**: {count} patients")
                    
        else:
            st.info("No patient assignments found for this user.")
            
    except Exception as e:
        st.error(f"Error loading patient assignments: {e}")
    finally:
        conn.close()