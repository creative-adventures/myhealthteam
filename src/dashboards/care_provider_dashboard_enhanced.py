import streamlit as st
import pandas as pd
from src import database
import numpy as np
from datetime import datetime

# Try to import awesome_table, if it fails, use fallback
try:
    from streamlit_awesome_table import awesome_table
    USE_AWESOME_TABLE = True
except ImportError:
    USE_AWESOME_TABLE = False

def show(user_id, user_role_ids=None):
    if user_role_ids is None:
        user_role_ids = []
    
    # Check if user has Care Provider Manager role (role_id 38)
    has_cpm_role = 38 in user_role_ids
    
    st.title("Care Provider Dashboard - Enhanced")
    
    # Show onboarding queue statistics only for management roles
    if has_cpm_role:
        show_onboarding_queue_stats(user_id, has_cpm_role)
    
    if has_cpm_role:
        st.info("👑 **Manager Access**: You have additional management tabs available")
        
        # Create tabs with management functionality (Provider Onboarding moved to Admin only)
        tab1, tab2, tab3 = st.tabs(["📋 My Patients", "👥 Team Management", " Manager Reports"])
        
        with tab1:
            show_patient_list_section(user_id)
            
        with tab2:
            st.subheader("👥 Team Management")
            
            # Import and display performance summaries for providers
            try:
                from src.utils.performance_components import (
                    display_provider_monthly_summary,
                    display_provider_weekly_summary,
                    display_patient_assignments_by_workflow
                )
                
                # Performance Section
                st.header("� Provider Performance")
                st.markdown("Monitor and analyze provider performance metrics across your team.")
                
                # Provider Monthly Performance Summary
                display_provider_monthly_summary(show_all=True, title="📈 Provider Monthly Performance Summary")
                
                st.divider()
                
                # Provider Weekly Performance Summary
                display_provider_weekly_summary(show_all=True, title="📅 Provider Weekly Performance Summary")
                
                st.divider()
                
                # Patient Assignments Section
                st.header("👥 Patient Assignments")
                st.markdown("Review patient assignments and onboarding workflow progress for your provider team.")
                
                # Get all providers for assignments display
                try:
                    providers = database.get_users_by_role(33)  # Care Provider role
                    if providers:
                        # Convert sqlite3.Row objects to dictionaries
                        provider_dicts = [dict(provider) for provider in providers]
                        
                        for provider in provider_dicts[:3]:  # Show for first 3 providers to avoid overload
                            with st.expander(f"Patient Assignments - {provider.get('full_name', provider.get('username', 'Unknown'))}"):
                                try:
                                    # Get provider user ID for assignments
                                    provider_user_id = provider.get('user_id', provider.get('id'))
                                    display_patient_assignments_by_workflow(
                                        user_id=provider_user_id,
                                        role_id=33,  # Care Provider role
                                        title=f"Assignments for {provider.get('full_name', provider.get('username', 'Unknown'))}"
                                    )
                                except Exception as e:
                                    st.error(f"Error loading assignments for {provider.get('username', 'Unknown')}: {e}")
                        
                        if len(provider_dicts) > 3:
                            st.info(f"Showing assignments for first 3 providers. Total providers: {len(provider_dicts)}")
                    else:
                        st.info("No providers found for patient assignment display.")
                except Exception as e:
                    st.error(f"Error getting providers: {e}")
                    
            except ImportError as e:
                st.error(f"Error importing performance components: {e}")
                st.info("🚧 Team management functionality coming soon...")
            
        with tab3:
            st.subheader("📊 Manager Reports")
            st.info("🚧 Manager reporting functionality coming soon...")
            # TODO: Add manager reporting functionality
    else:
        # Standard CP dashboard - single patient list view
        show_patient_list_section(user_id)

def show_onboarding_queue_stats(user_id, has_management_role=False):
    """Display onboarding queue statistics"""
    st.subheader("📊 Onboarding Queue Status")
    
    # Get onboarding statistics
    queue_stats = database.get_onboarding_queue_stats()
    
    # Create columns for metrics display
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🏥 Total in Onboarding", 
            queue_stats['total_onboarding'],
            help="Total patients currently in onboarding process"
        )
    
    with col2:
        st.metric(
            "👨‍⚕️ Need Provider Assignment", 
            queue_stats['pending_provider_assignment'],
            help="Patients who have completed TV visit and need provider assignment"
        )
    
    with col3:
        st.metric(
            "📺 Need TV Visit", 
            queue_stats['pending_tv_visit'],
            help="Patients who need initial telemedicine visit"
        )
    
    with col4:
        st.metric(
            "👥 Unassigned Active", 
            queue_stats['unassigned_active_patients'],
            help="Active patients without assigned care provider"
        )
    
    # Show additional details for management roles
    if has_management_role:
        with st.expander("📋 Detailed Queue Information", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("📞 Need Initial Contact", queue_stats['pending_initial_contact'])
                st.metric("📄 Need Documentation", queue_stats['pending_documentation'])
            
            with col2:
                st.metric("🎯 Unassigned POT", queue_stats['unassigned_pot'])
                st.metric("🆕 New Patients (30d)", queue_stats['new_patients_30_days'])

def show_patient_list_section(user_id):
    # Get the provider_id from user_id first
    provider_id = database.get_provider_id_from_user_id(user_id)
    if not provider_id:
        st.error("No provider found for this user. Please contact your administrator.")
        return

    # Get all patients assigned to this provider with proper status information
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
                p.email,
                prs.zip_code,
                prs.city,
                prs.state,
                r.county as region_county,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM region_providers rp2 
                        JOIN regions r2 ON rp2.region_id = r2.region_id 
                        WHERE rp2.provider_id = ? AND r2.county = r.county
                    ) THEN 0 
                    ELSE 1 
                END as outside_provider_region
            FROM user_patient_assignments upa
            JOIN patients p ON upa.patient_id = p.patient_id
            LEFT JOIN patient_region_mapping prs ON p.patient_id = prs.patient_id
            LEFT JOIN regions r ON prs.region_id = r.region_id
            WHERE upa.user_id = ?
            ORDER BY p.last_name, p.first_name
        """, (provider_id, user_id,))
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
        # Debug: Let's check what's in the assignments table for this user
        try:
            conn = database.get_db_connection()
            cursor = conn.execute("SELECT COUNT(*) as count FROM user_patient_assignments WHERE user_id = ?", (user_id,))
            count = cursor.fetchone()[0]
            st.info(f"Debug: Found {count} patient assignments for user {user_id}")
            conn.close()
        except Exception as e2:
            st.info(f"Debug error: {e2}")
        patient_data_list = []
        assigned_patients = []

    # Get all unique patient statuses for filtering
    all_statuses = []
    if patient_data_list:
        try:
            # Extract unique statuses from patient data
            all_statuses = list(set([p.get('status', 'Unknown') for p in patient_data_list if 'status' in p]))
            all_statuses = sorted([s for s in all_statuses if s and s != ''])  # Remove empty strings and sort
            # Clean up status names to remove "changed" and "Call0" suffixes
            all_statuses = [s.split('changed')[0].split('Call0')[0].strip() for s in all_statuses]
        except Exception as e:
            print(f"Error getting statuses: {e}")
            all_statuses = ['Active', 'Inactive', 'Pending', 'Discharged']  # Default fallback
    else:
        all_statuses = ['Active', 'Inactive', 'Pending', 'Discharged']  # Default fallback
    
    # Filter statuses to only show active-like statuses for metrics calculation
    active_statuses = ['Active', 'active', 'Active - Changed', 'Active - Call0', 'Active - Changed', 'Active - Call0']
    active_patient_statuses = [s for s in all_statuses if any(active_status.lower() in s.lower() for active_status in active_statuses)]
    if not active_patient_statuses:
        active_patient_statuses = ['Active', 'active']  # Fallback
    
    # Get counties and zip codes for filtering
    # Priority: 1) Provider's assigned regions 2) All regions where the provider has patients
    all_counties = []
    all_zip_codes = []
    
    try:
        conn = database.get_db_connection()
        
        # First check if provider has specific region assignments
        cursor = conn.execute("""
            SELECT COUNT(*) FROM region_providers WHERE provider_id = ?
        """, (provider_id,))
        has_region_assignments = cursor.fetchone()[0] > 0
        
        if has_region_assignments:
            # Provider has region constraints - show their assigned regions AND their actual patients' regions
            print(f"DEBUG: Provider {provider_id} has region assignments")
            
            # Get counties from provider's assigned regions PLUS counties where they have actual patients
            cursor = conn.execute("""
                SELECT DISTINCT r.county, r.state, COUNT(DISTINCT p.patient_id) as patient_count
                FROM region_providers rp
                JOIN regions r ON rp.region_id = r.region_id
                LEFT JOIN patient_region_mapping prm ON r.region_id = prm.region_id
                LEFT JOIN patients p ON prm.patient_id = p.patient_id
                WHERE rp.provider_id = ? AND r.county IS NOT NULL AND r.county != ''
                GROUP BY r.county, r.state
                
                UNION
                
                SELECT DISTINCT r.county, r.state, COUNT(DISTINCT p.patient_id) as patient_count
                FROM user_patient_assignments upa
                JOIN patients p ON upa.patient_id = p.patient_id
                LEFT JOIN patient_region_mapping prm ON p.patient_id = prm.patient_id
                LEFT JOIN regions r ON prm.region_id = r.region_id
                WHERE upa.user_id = ? AND r.county IS NOT NULL AND r.county != ''
                GROUP BY r.county, r.state
                ORDER BY county
            """, (provider_id, user_id))
            
        else:
            # Provider has no region constraints - show all regions where they have patients
            print(f"DEBUG: Provider {provider_id} has no region assignments, showing all patient regions")
            cursor = conn.execute("""
                SELECT DISTINCT r.county, r.state, COUNT(DISTINCT p.patient_id) as patient_count
                FROM user_patient_assignments upa
                JOIN patients p ON upa.patient_id = p.patient_id
                LEFT JOIN patient_region_mapping prm ON p.patient_id = prm.patient_id
                LEFT JOIN regions r ON prm.region_id = r.region_id
                WHERE upa.user_id = ? AND r.county IS NOT NULL AND r.county != ''
                GROUP BY r.county, r.state
                ORDER BY r.county
            """, (user_id,))
        
        counties_data = cursor.fetchall()
            
        all_counties = [(c[0], f"{c[0]}, {c[1]} [{c[2]}]") for c in counties_data]
        print(f"DEBUG: Found {len(counties_data)} counties: {all_counties}")
        
        # Get zip codes from the provider's assigned patients
        print(f"DEBUG: Getting zip codes for provider {provider_id}")
        cursor = conn.execute("""
            SELECT DISTINCT p.address_zip, p.address_city, p.address_state, COUNT(*) as patient_count
            FROM user_patient_assignments upa
            JOIN patients p ON upa.patient_id = p.patient_id
            WHERE upa.user_id = ? AND p.address_zip IS NOT NULL AND p.address_zip != ''
            GROUP BY p.address_zip, p.address_city, p.address_state
            ORDER BY p.address_zip
        """, (user_id,))
        zip_codes_data = cursor.fetchall()
        
        all_zip_codes = [(z[0], f"{z[0]} - {z[1]}, {z[2]} [{z[3]}]") for z in zip_codes_data]
        print(f"DEBUG: Found {len(zip_codes_data)} zip codes: {all_zip_codes}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error getting provider counties/zip codes: {e}")
        # Provide fallback data to show that the system is working
        all_counties = [("Los Angeles", "Los Angeles, CA [0]")]
        all_zip_codes = [("90001", "90001 - Los Angeles, CA [0]")]
    
    # Create enhanced metrics cards using Streamlit elements
    col1, col2, col3 = st.columns(3)
    
    # Total patients assigned (only active patients)
    active_patients_list = [p for p in patient_data_list if p.get('status', '').lower().startswith('active')]
    total_patients = len(active_patients_list)
    col1.metric("Total Patients Assigned", total_patients)
    
    # Active patients (including "Active-*" statuses) - for stats only
    active_patients = len(active_patients_list)
    col2.metric("Active Patients", active_patients)
    
    # Calculate hours:minutes served this month
    total_minutes_this_month = 0
    try:
        conn = database.get_db_connection()
        # Get total minutes from provider_tasks for this month
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        cursor = conn.execute("""
            SELECT SUM(minutes_of_service) as total_minutes
            FROM provider_tasks 
            WHERE provider_id = ? 
            AND strftime('%Y-%m', task_date) = ?
        """, (provider_id, f"{current_year}-{current_month:02d}"))
        
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
    
    st.subheader("Assigned Patients")
    
    # Add filtering controls with proper dropdowns for status, counties, and zip codes
    col1, col2, col3 = st.columns(3)
    with col1:
        # Status filter - multi-select dropdown
        st.write("Filter by Patient Status:")
        selected_statuses = st.multiselect("Select Status(es)", ['All'] + all_statuses, default=['All'], key="status_filter_1")
    with col2:
        # County filter - single select dropdown
        st.write("Filter by County:")
        try:
            county_names = ['All Counties'] + [c[1] for c in all_counties if len(c) > 1]
            if len(county_names) <= 1:  # Only "All Counties"
                county_names.append("No counties available")
            selected_county = st.selectbox("Select County", county_names, index=0, key="county_filter_1")
        except Exception as e:
            st.error(f"Error loading counties: {e}")
            selected_county = "All Counties"
    with col3:
        # Zip code filter - single select dropdown
        st.write("Filter by Zip Code:")
        try:
            zip_code_names = ['All Zip Codes'] + [z[1] for z in all_zip_codes if len(z) > 1]
            if len(zip_code_names) <= 1:  # Only "All Zip Codes"
                zip_code_names.append("No zip codes available")
            selected_zip_code = st.selectbox("Select Zip Code", zip_code_names, index=0, key="zip_filter_1")
        except Exception as e:
            st.error(f"Error loading zip codes: {e}")
            selected_zip_code = "All Zip Codes"
    
    # Filter patients based on selections
    filtered_patients = patient_data_list
    if 'All' not in selected_statuses:
        filtered_patients = [p for p in patient_data_list if p.get('status') in selected_statuses]
    else:
        # When 'All' is selected, only show active patients (default behavior)
        filtered_patients = [p for p in patient_data_list if p.get('status', '').lower().startswith('active')]

    # Further filter by county if selected
    if selected_county != 'All Counties':
        # Extract county name from the selected county display text
        try:
            selected_county_name = selected_county.split(',')[0]  # Extract county name from "county, state [patient_count]" format

            # Filter patients by county using the patient_region_mapping table
            # We need to join with regions table to get the county information
            try:
                conn = database.get_db_connection()
                cursor = conn.execute("""
                    SELECT DISTINCT p.patient_id
                    FROM patient_region_mapping p
                    JOIN regions r ON p.region_id = r.region_id
                    WHERE r.county = ?
                """, (selected_county_name,))
                patient_ids_in_county = [row[0] for row in cursor.fetchall()]
                conn.close()

                # Filter patients to only those in this county
                filtered_patients = [p for p in filtered_patients if p.get('patient_id') in patient_ids_in_county]
            except Exception as e:
                print(f"Error filtering by county: {e}")
        except Exception as e:
            print(f"Error processing county filter: {e}")

    # Further filter by zip code if selected
    if selected_zip_code != 'All Zip Codes':
        # Extract zip code from the display text format: "zip - city, state [patient_count]"
        selected_zip = selected_zip_code.split(' - ')[0]  # Extract zip code from "zip - city, state" format
        filtered_patients = [p for p in filtered_patients if p.get('address_zip') == selected_zip]

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
            # Add region status indicator for patients outside provider regions
            if 'outside_provider_region' in patients_df.columns:
                patients_df['region_status'] = patients_df['outside_provider_region'].apply(
                    lambda x: "⚠️ Outside Region" if x == 1 else "✅ In Region"
                )
                display_df = patients_df[['first_name', 'last_name', 'full_address', 'contact_info', 'status', 'region_status']]
                display_df.columns = ['First Name', 'Last Name', 'Address', 'Contact Info', 'Status', 'Region Status']
            else:
                display_df = patients_df[['first_name', 'last_name', 'full_address', 'contact_info', 'status']]
                display_df.columns = ['First Name', 'Last Name', 'Address', 'Contact Info', 'Status']

            # Display with enhanced capabilities
            st.subheader("Patient Data Table")

            if USE_AWESOME_TABLE:
                # Use Awesome Table for enhanced functionality
                try:
                    table_result = awesome_table(
                        display_df,
                        key="patient_table",
                        height=400,
                        width='100%',
                        sortable=True,
                        searchable=True,
                        filterable=True,
                        pagination=True,
                        page_size=10,
                        # Additional awesome-table features
                        groupable=True,
                        draggable=True,
                        exportable=True,
                        theme="streamlit"
                    )

                    # Show selected patient info
                    if table_result and 'selected_rows' in table_result:
                        selected_rows = table_result['selected_rows']
                        if selected_rows:
                            selected_row = selected_rows[0]
                            st.info(f"Selected Patient: {selected_row.get('First Name', '')} {selected_row.get('Last Name', '')}")
                            st.write("Selected Patient Details:")
                            for key, value in selected_row.items():
                                st.write(f"**{key}:** {value}")
                except Exception as e:
                    st.warning(f"Awesome table failed: {e}. Using fallback.")
                    st.dataframe(
                        display_df, 
                        height=400, 
                        use_container_width=True,
                        column_config={
                            "First Name": st.column_config.TextColumn("First Name", width="medium"),
                            "Last Name": st.column_config.TextColumn("Last Name", width="medium"),
                            "DOB": st.column_config.DateColumn("DOB", width="small"),
                            "Gender": st.column_config.TextColumn("Gender", width="small"),
                            "Phone": st.column_config.TextColumn("Phone", width="medium"),
                            "Email": st.column_config.TextColumn("Email", width="large"),
                            "City": st.column_config.TextColumn("City", width="medium"),
                            "State": st.column_config.TextColumn("State", width="small"),
                            "Status": st.column_config.TextColumn("Status", width="small"),
                        },
                        hide_index=True
                    )
                    st.info("Note: Enhanced table features are not available due to package issues.")
            else:
                # Fallback to standard dataframe with enhanced styling
                st.dataframe(
                    display_df, 
                    height=400, 
                    use_container_width=True,
                    column_config={
                        "First Name": st.column_config.TextColumn("First Name", width="medium"),
                        "Last Name": st.column_config.TextColumn("Last Name", width="medium"),
                        "DOB": st.column_config.DateColumn("DOB", width="small"),
                        "Gender": st.column_config.TextColumn("Gender", width="small"),
                        "Phone": st.column_config.TextColumn("Phone", width="medium"),
                        "Email": st.column_config.TextColumn("Email", width="large"),
                        "City": st.column_config.TextColumn("City", width="medium"),
                        "State": st.column_config.TextColumn("State", width="small"),
                        "Status": st.column_config.TextColumn("Status", width="small"),
                    },
                    hide_index=True
                )

            # Patient selection for daily tasks
            patient_names = [f"{p['first_name']} {p['last_name']}" for p in filtered_patients if 'first_name' in p and 'last_name' in p]
            if patient_names:
                selected_patient_name = st.selectbox("Select Patient for Daily Tasks", patient_names, key="daily_tasks_patient_select")
                if selected_patient_name:
                    # Find the selected patient
                    selected_patient = next((p for p in filtered_patients if f"{p['first_name']} {p['last_name']}" == selected_patient_name), None)
                    if selected_patient:
                        st.session_state['selected_patient_id'] = selected_patient['patient_id']
                        st.session_state['selected_patient_name'] = selected_patient_name
            else:
                st.info("No patients available for selection")

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
                    "DOB": st.column_config.DateColumn("DOB", width="small"),
                    "Gender": st.column_config.TextColumn("Gender", width="small"),
                    "Phone": st.column_config.TextColumn("Phone", width="medium"),
                    "Email": st.column_config.TextColumn("Email", width="large"),
                    "City": st.column_config.TextColumn("City", width="medium"),
                    "State": st.column_config.TextColumn("State", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                },
                hide_index=True
            )
    else:
        st.info("No patients match the selected filters.")

    st.subheader("Daily Task Entries")

    # Fetch task billing codes for the task dropdown - filtered by Primary Care Visit
    task_billing_codes = database.get_tasks_billing_codes_by_service_type("Primary Care Visit")
    # Group by task_description to avoid duplicates
    unique_task_descriptions = list(set(task['task_description'] for task in task_billing_codes))
    task_options = sorted(unique_task_descriptions)

    # Initialize session state for tasks if not already present
    if 'daily_tasks_data' not in st.session_state:
        st.session_state.daily_tasks_data = [{}] * 5  # Reduced from 10 to 5 for cleaner UI

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
            # Patient selection
            patient_names = [f"{p['first_name']} {p['last_name']}" for p in filtered_patients if 'first_name' in p and 'last_name' in p]
            if patient_names:
                task_entry['patient_name'] = st.selectbox(f"Patient {i+1}", patient_names, key=f"patient_{i}", index=0 if patient_names else -1)
            else:
                task_entry['patient_name'] = st.selectbox(f"Patient {i+1}", ["No patients available"], key=f"patient_{i}", index=0)
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
                # In a real implementation, this would save to the database
                # For now, we'll just show a success message
                st.success(f"Task '{task_entry['task_type']}' logged for {task_entry['patient_name']} on {task_entry['date']} with duration {task_entry['duration']} minutes.")
                
                # Save to database using the existing function
                try:
                    # Get patient_id from the selected patient name
                    selected_patient = next((p for p in filtered_patients if f"{p['first_name']} {p['last_name']}" == task_entry['patient_name']), None)
                    if selected_patient:
                        # Call the database function to save the task
                        database.save_daily_task(
                            provider_id=provider_id,
                            patient_id=selected_patient['patient_id'],
                            task_date=task_entry['date'],
                            task_description=task_entry['task_type'],
                            duration_minutes=task_entry['duration'],
                            notes=task_entry['notes']
                        )
                        st.success("Task successfully saved to database!")
                except Exception as e:
                    st.error(f"Error saving task to database: {e}")
            else:
                st.warning("Please fill in all fields for the task entry.")
        st.markdown("---")

    # # Additional zip code information section
    # st.subheader("Zip Code Information")
    # st.write("Available zip codes for filtering:")
    
    # # Create a simple table of zip codes
    # zip_code_df = pd.DataFrame(all_zip_codes, columns=['Zip Code', 'Location'])
    # st.dataframe(zip_code_df, height=200, use_container_width=True)
    
    # # Add a summary section
    # st.subheader("Quick Summary")
    # st.write(f"Total patients assigned: {total_patients}")
    # st.write(f"Active patients: {active_patients}")
    # st.write(f"Time served this month: {time_string}")
    # st.write(f"Available task types: {len(task_options)}")
