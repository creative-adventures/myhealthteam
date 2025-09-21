import streamlit as st
import pandas as pd
from src import database
from datetime import datetime

def show(user_id, user_role_ids=None):
    if user_role_ids is None:
        user_role_ids = []
    
    # Check if user has Lead Coordinator (37) or Coordinator Manager (40) roles
    has_lc_role = 37 in user_role_ids
    has_cm_role = 40 in user_role_ids
    
    st.title("Care Coordinator Dashboard - Enhanced")
    
    # Show onboarding queue statistics only for management roles
    if has_lc_role or has_cm_role:
        show_onboarding_queue_stats_cc(user_id, has_lc_role or has_cm_role)
    
    if has_lc_role or has_cm_role:
        role_text = []
        if has_lc_role:
            role_text.append("Lead Coordinator")
        if has_cm_role:
            role_text.append("Coordinator Manager")
        
        st.info(f"👑 **Management Access**: You have {' & '.join(role_text)} privileges with additional tabs available")
        
        # Create tabs with management functionality
        tab1, tab2 = st.tabs(["📋 My Patients", "👥 Team Management"])
        
        with tab1:
            show_coordinator_patient_list(user_id)
            
        with tab2:
            st.subheader("👥 Coordinator Team Management")
            
            # Import and display performance summaries for coordinators
            try:
                from src.utils.performance_components import (
                    display_coordinator_monthly_summary,
                    display_coordinator_weekly_summary,
                    display_patient_assignments_by_workflow
                )
                
                # Performance Section
                st.header("� Coordinator Performance")
                st.markdown("Monitor and analyze coordinator performance metrics across your team.")
                
                # Coordinator Monthly Performance Summary
                display_coordinator_monthly_summary(show_all=True, title="📈 Coordinator Monthly Performance Summary")
                
                st.divider()
                
                # Coordinator Weekly Performance Summary
                display_coordinator_weekly_summary(show_all=True, title="📅 Coordinator Weekly Performance Summary")
                
                st.divider()
                
                # Patient Assignments Section
                st.header("👥 Patient Assignments")
                st.markdown("Review patient assignments and onboarding workflow progress for your coordinator team.")
                
                # Get all coordinators for assignments display
                try:
                    coordinators = database.get_users_by_role(36)  # Care Coordinator role
                    if coordinators:
                        # Convert sqlite3.Row objects to dictionaries
                        coordinator_dicts = [dict(coordinator) for coordinator in coordinators]
                        
                        for coordinator in coordinator_dicts[:3]:  # Show for first 3 coordinators to avoid overload
                            with st.expander(f"Patient Assignments - {coordinator.get('full_name', coordinator.get('username', 'Unknown'))}"):
                                try:
                                    # Get coordinator user ID for assignments
                                    coordinator_user_id = coordinator.get('user_id', coordinator.get('id'))
                                    display_patient_assignments_by_workflow(
                                        user_id=coordinator_user_id,
                                        role_id=36,  # Care Coordinator role
                                        title=f"Assignments for {coordinator.get('full_name', coordinator.get('username', 'Unknown'))}"
                                    )
                                except Exception as e:
                                    st.error(f"Error loading assignments for {coordinator.get('username', 'Unknown')}: {e}")
                        
                        if len(coordinator_dicts) > 3:
                            st.info(f"Showing assignments for first 3 coordinators. Total coordinators: {len(coordinator_dicts)}")
                    else:
                        st.info("No coordinators found for patient assignment display.")
                except Exception as e:
                    st.error(f"Error getting coordinators: {e}")
                    
            except ImportError as e:
                st.error(f"Error importing performance components: {e}")
                st.info("🚧 Team management functionality coming soon...")
    else:
        # Standard CC dashboard - single patient list view
        show_coordinator_patient_list(user_id)

def show_onboarding_queue_stats_cc(user_id, has_management_role=False):
    """Display onboarding queue statistics for Care Coordinators"""
    st.subheader("📊 Onboarding Queue Status")
    
    # Get onboarding statistics
    queue_stats = database.get_onboarding_queue_stats()
    
    # Create columns for metrics display - CC focused
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📞 Need Initial Contact", 
            queue_stats['pending_initial_contact'],
            help="Patients who need initial contact/assessment"
        )
    
    with col2:
        st.metric(
            "📺 Need TV Visit", 
            queue_stats['pending_tv_visit'],
            help="Patients who need telemedicine visit scheduling"
        )
    
    with col3:
        st.metric(
            "📄 Need Documentation", 
            queue_stats['pending_documentation'],
            help="Patients with pending documentation review"
        )
    
    with col4:
        st.metric(
            "🎯 Unassigned POT", 
            queue_stats['unassigned_pot'],
            help="Patients without assigned Patient Onboarding Team member"
        )
    
    # Show additional management details
    if has_management_role:
        with st.expander("📋 Management Overview", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("🏥 Total in Onboarding", queue_stats['total_onboarding'])
                st.metric("👨‍⚕️ Awaiting Provider Assignment", queue_stats['pending_provider_assignment'])
            
            with col2:
                st.metric("👥 Unassigned Active Patients", queue_stats['unassigned_active_patients'])
                st.metric("🆕 New Patients (30d)", queue_stats['new_patients_30_days'])
                
            # Show my assigned onboarding tasks
            if user_id:
                st.subheader("📋 My Onboarding Tasks")
                my_tasks = database.get_onboarding_tasks_by_role(36, user_id)  # CC role ID is 36
                
                if my_tasks:
                    for task in my_tasks:
                        with st.container():
                            task_col1, task_col2, task_col3 = st.columns([2, 2, 1])
                            with task_col1:
                                st.write(f"**{task['first_name']} {task['last_name']}**")
                            with task_col2:
                                st.write(task['task_status'])
                            with task_col3:
                                st.write(task['created_date'][:10] if task['created_date'] else 'N/A')
                else:
                    st.info("No onboarding tasks currently assigned to you.")

def show_coordinator_patient_list(user_id):
    
    # Get the coordinator_id from user_id first
    coordinator_id = None
    try:
        conn = database.get_db_connection()
        cursor = conn.execute("SELECT coordinator_id FROM coordinators WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result:
            coordinator_id = result[0]
        conn.close()
    except Exception as e:
        st.error(f"Error getting coordinator ID: {e}")

    # Get all patients assigned to this coordinator with proper status information
    try:
        conn = database.get_db_connection()
        cursor = conn.execute("""
            SELECT DISTINCT
                p.patient_id,
                p.first_name,
                p.last_name,
                p.status,
                p.address_street,
                p.address_city,
                p.address_state,
                p.address_zip,
                p.phone_primary,
                p.email
            FROM user_patient_assignments upa
            JOIN patients p ON upa.patient_id = p.patient_id
            WHERE upa.user_id = ?
            ORDER BY p.last_name, p.first_name
        """, (user_id,))
        assigned_patients = cursor.fetchall()
        conn.close()
        # Convert to list of dictionaries for easier handling
        patient_data_list = []
        for patient in assigned_patients:
            patient_dict = {}
            for key in patient.keys():
                patient_dict[key] = patient[key]
            patient_data_list.append(patient_dict)
            
    except Exception as e:
        st.error(f"Error fetching patient data: {e}")
        patient_data_list = []
        assigned_patients = []

    # Filter patients to only show Active, Active-Geri, and Active-PCP statuses for metrics
    active_patient_statuses = ['Active', 'Active-Geri', 'Active-PCP']
    active_patients = [p for p in patient_data_list if p.get('status', '').strip() in active_patient_statuses]
    
    # Get counties and zip codes assigned to this specific coordinator for filtering
    all_counties = []
    all_zip_codes = []
    
    try:
        # Get counties using the new dashboard mapping table
        counties = database.get_provider_counties(coordinator_id)  # Using provider method, but we'll adapt
        all_counties = counties  # Already formatted correctly
        
        # Get zip codes using the new dashboard mapping table
        zip_codes = database.get_provider_zip_codes(coordinator_id)  # Using provider method, but we'll adapt
        all_zip_codes = zip_codes  # Already formatted correctly
        
    except Exception as e:
        print(f"Error getting coordinator counties/zip codes: {e}")
        # Provide fallback data to show that the system is working
        all_counties = [("Los Angeles", "Los Angeles, CA [0]")]
        all_zip_codes = [("90001", "90001 - Los Angeles, CA [0]")]
    
    # Create enhanced metrics cards using Streamlit elements
    col1, col2, col3 = st.columns(3)
    
    # Total patients assigned (only active patients)
    total_patients = len(active_patients)
    col1.metric("Total Patients Assigned", total_patients)
    
    # Active patients (Active, Active-Geri, Active-PCP)
    active_patients_count = len(active_patients)
    col2.metric("Active Patients", active_patients_count)
    
    # Calculate hours:minutes served this month for active patients only
    total_minutes_this_month = 0
    try:
        conn = database.get_db_connection()
        # Get total minutes from coordinator_tasks for this month, filtered by active patients
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        cursor = conn.execute("""
            SELECT SUM(ct.duration_minutes) as total_minutes
            FROM coordinator_tasks ct
            JOIN patients p ON ct.patient_id = p.patient_id
            WHERE ct.coordinator_id = ? 
            AND strftime('%Y-%m', ct.task_date) = ?
            AND p.status IN ('Active', 'Active-Geri', 'Active-PCP')
        """, (coordinator_id, f"{current_year}-{current_month:02d}"))
        
        result = cursor.fetchone()
        total_minutes_this_month = result[0] if result[0] else 0
        conn.close()
        
        # Convert minutes to hours and minutes
        hours = total_minutes_this_month // 60
        minutes = total_minutes_this_month % 60
        time_string = f"{hours}h {minutes}m"
    except Exception as e:
        print(f"Error calculating time served: {e}")
        time_string = "0h 0m"
    
    col3.metric("Time Served This Month", time_string)
    
    st.divider()
    
    st.subheader("Active Patient Assignments")
    
    # Filter patients to only show Active, Active-Geri, and Active-PCP for display
    filtered_patients = [p for p in patient_data_list if p.get('status', '').strip() in active_patient_statuses]
    
    if filtered_patients:
        try:
            # Create DataFrame for display
            patients_df = pd.DataFrame(filtered_patients)
            
            # Create address and contact info columns
            if all(col in patients_df.columns for col in ['address_street', 'address_city', 'address_state', 'address_zip']):
                patients_df['full_address'] = (patients_df['address_street'] + ", " + 
                                             patients_df['address_city'] + ", " + 
                                             patients_df['address_state'] + " " + 
                                             patients_df['address_zip'])
            else:
                patients_df['full_address'] = "Address not available"
            
            if all(col in patients_df.columns for col in ['phone_primary', 'email']):
                patients_df['contact_info'] = patients_df['phone_primary'] + " / " + patients_df['email']
            else:
                patients_df['contact_info'] = "Contact info not available"
            
            # Prepare data for display
            display_df = patients_df[['first_name', 'last_name', 'full_address', 'contact_info', 'status']]
            display_df.columns = ['First Name', 'Last Name', 'Address', 'Contact Info', 'Status']
            
            # Display patient data
            st.dataframe(
                display_df, 
                height=400, 
                use_container_width=True,
                column_config={
                    "First Name": st.column_config.TextColumn("First Name", width="medium"),
                    "Last Name": st.column_config.TextColumn("Last Name", width="medium"),
                    "Address": st.column_config.TextColumn("Address", width="large"),
                    "Contact Info": st.column_config.TextColumn("Contact Info", width="medium"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                },
                hide_index=True
            )
            
        except Exception as e:
            st.error(f"Error processing patient data: {e}")
            # Fallback to simple dataframe
            st.dataframe(
                display_df, 
                height=400, 
                use_container_width=True,
                column_config={
                    "First Name": st.column_config.TextColumn("First Name", width="medium"),
                    "Last Name": st.column_config.TextColumn("Last Name", width="medium"),
                    "Address": st.column_config.TextColumn("Address", width="large"),
                    "Contact Info": st.column_config.TextColumn("Contact Info", width="medium"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                },
                hide_index=True
            )
    else:
        st.info("No active patients assigned to this coordinator.")

    st.subheader("Daily Task Entries")

    # Fetch task billing codes for the task dropdown
    task_billing_codes = database.get_tasks_billing_codes_by_service_type("Primary Care Visit")
    # Group by task_description to avoid duplicates
    unique_task_descriptions = list(set(task['task_description'] for task in task_billing_codes))
    task_options = sorted(unique_task_descriptions)

    # Initialize session state for tasks if not already present
    if 'daily_tasks_data' not in st.session_state:
        st.session_state.daily_tasks_data = [{}] * 5

    # Add a button to add more task entries dynamically
    if st.button("Add Task Entry"):
        st.session_state.daily_tasks_data.append({})

    # Create task entries
    for i, task_entry in enumerate(st.session_state.daily_tasks_data):
        st.markdown(f"#### Task Entry {i+1}")
        # Create a compact row layout for date, patient, task type, and duration
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

        with col1:
            task_entry['date'] = st.date_input(f"Date {i+1}", value=task_entry.get('date', pd.to_datetime('today')), key=f"date_{i}")
        with col2:
            # Patient selection - only show active patients
            active_patient_names = [f"{p['first_name']} {p['last_name']}" for p in active_patients if 'first_name' in p and 'last_name' in p]
            if active_patient_names:
                task_entry['patient_name'] = st.selectbox(f"Patient {i+1}", active_patient_names, key=f"patient_{i}", index=0 if active_patient_names else -1)
            else:
                task_entry['patient_name'] = st.selectbox(f"Patient {i+1}", ["No active patients available"], key=f"patient_{i}", index=0)
        with col3:
            task_entry['task_type'] = st.selectbox(f"Task Type {i+1}", task_options, key=f"task_type_{i}", index=0 if task_options else -1)
        with col4:
            # Timer functionality for duration - compact layout in one row
            timer_key = f"timer_{i}"
            duration_key = f"duration_{i}"
            
            # Initialize timer state
            if timer_key not in st.session_state:
                st.session_state[timer_key] = 0
                st.session_state[f"{timer_key}_running"] = False
                st.session_state[f"{timer_key}_start_time"] = None
            
            # Create a compact timer layout - timer text next to button, duration next to button too
            timer_display = f"{st.session_state[timer_key] // 60:02d}:{st.session_state[timer_key] % 60:02d}"
            
            # Display everything on same line: timer text, button, duration
            col_timer_text, col_timer_btn, col_duration = st.columns([1, 1, 1])
            
            with col_timer_text:
                st.write(f"Timer: {timer_display}")
            
            with col_timer_btn:
                # Start/Stop timer button (smaller)
                timer_btn_key = f"timer_btn_{i}"
                if st.button("▶/⏹", key=timer_btn_key, use_container_width=True, help="Start/Stop Timer"):
                    if not st.session_state[f"{timer_key}_running"]:
                        st.session_state[f"{timer_key}_running"] = True
                        st.session_state[f"{timer_key}_start_time"] = pd.Timestamp.now()
                    else:
                        st.session_state[f"{timer_key}_running"] = False
                        # When timer stops, update the duration field
                        if st.session_state[f"{timer_key}_start_time"]:
                            current_time = pd.Timestamp.now()
                            elapsed_seconds = int((current_time - st.session_state[f"{timer_key}_start_time"]).total_seconds())
                            st.session_state[timer_key] = elapsed_seconds
                            task_entry['duration'] = elapsed_seconds // 60 + 1  # Convert to minutes, add 1 to avoid 0
                            # Force a refresh to update the display
                            st.experimental_rerun()
            
            with col_duration:
                # Manual duration input (compact) - placed next to timer button
                task_entry['duration'] = st.number_input(f"Duration (min)", min_value=1, value=task_entry.get('duration', 30), key=duration_key, label_visibility="collapsed")
            
            # Update timer in real-time using a rerun approach
            if st.session_state[f"{timer_key}_running"]:
                current_time = pd.Timestamp.now()
                if st.session_state[f"{timer_key}_start_time"]:
                    elapsed_seconds = int((current_time - st.session_state[f"{timer_key}_start_time"]).total_seconds())
                    st.session_state[timer_key] = elapsed_seconds
                    # Update the number input to reflect timer value
                    task_entry['duration'] = elapsed_seconds // 60 + 1  # Convert to minutes, add 1 to avoid 0
                    # Force a refresh to update the display
                    st.experimental_rerun()

        task_entry['notes'] = st.text_area(f"Notes {i+1}", value=task_entry.get('notes', ''), key=f"notes_{i}")

        if st.button(f"Log Task {i+1}", key=f"log_task_{i}"):
            if task_entry.get('patient_name') and task_entry.get('task_type') and task_entry.get('duration'):
                # Save to database using the existing function
                try:
                    # Get patient_id from the selected patient name
                    selected_patient = next((p for p in active_patients if f"{p['first_name']} {p['last_name']}" == task_entry['patient_name']), None)
                    if selected_patient:
                        # Call the database function to save the task
                        success = database.save_coordinator_task(
                            coordinator_id=coordinator_id,
                            patient_id=selected_patient['patient_id'],
                            task_date=task_entry['date'],
                            task_description=task_entry['task_type'],
                            duration_minutes=task_entry['duration'],
                            notes=task_entry['notes']
                        )
                        
                        if success:
                            st.success(f"Task '{task_entry['task_type']}' logged for {task_entry['patient_name']} on {task_entry['date']} with duration {task_entry['duration']} minutes.")
                            # Clear the form after successful save
                            st.session_state.daily_tasks_data[i] = {}
                            st.rerun()
                        else:
                            st.error("Error saving task to database.")
                    else:
                        st.error("Error: Could not find patient ID.")
                except Exception as e:
                    st.error(f"Error saving task to database: {e}")
            else:
                st.warning("Please fill in all fields for the task entry.")
        st.markdown("---")

    # Add a summary section
    st.subheader("Quick Summary")
    st.write(f"Total patients assigned: {total_patients}")
    st.write(f"Active patients: {active_patients_count}")
    st.write(f"Time served this month: {time_string}")
    st.write(f"Available task types: {len(task_options)}")
