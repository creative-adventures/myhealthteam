import streamlit as st
import sqlite3
from src.database import (
    get_db_connection, get_user_roles, get_users, add_user, get_user_by_id,
    get_users_by_role, get_tasks_by_user, get_user_patient_assignments,
    get_coordinator_performance_metrics, get_provider_performance_metrics,
    get_tasks_billing_codes,
    get_care_plan, update_care_plan, get_provider_id_from_user_id, get_patient_details_by_id
)
from src import database
from src.dashboards import admin_dashboard, onboarding_dashboard, data_entry_dashboard, care_provider_dashboard_enhanced, care_coordinator_dashboard_enhanced

def main():
    st.set_page_config(layout="wide")
    st.sidebar.title("ZEN Medical")
    
    # Role selection - exclude management roles since they're integrated into base roles
    roles = database.get_user_roles()
    # Filter out management roles that are now integrated into base roles
    filtered_roles = [role for role in roles if role['role_name'] not in ['LC', 'CPM', 'CM']]
    role_names_to_ids = {role['role_name']: role['role_id'] for role in filtered_roles}
    role_names = list(role_names_to_ids.keys())
    selected_role_name = st.sidebar.selectbox("Select Role", role_names)

    # User selection
    if selected_role_name:
        selected_role_id = role_names_to_ids[selected_role_name]
        users_in_role = database.get_users_by_role(selected_role_id)
        if users_in_role:
            user_names = [user['username'] for user in users_in_role]
            selected_user_name = st.sidebar.selectbox("Select User", user_names)

            if selected_user_name:
                selected_user = next((user for user in users_in_role if user['username'] == selected_user_name), None)
                if selected_user:
                    st.session_state['user_id'] = selected_user['user_id']
                    st.session_state['role_id'] = selected_role_id
                    st.session_state['role_name'] = selected_role_name # Keep role_name for display purposes if needed
                    st.session_state['user_full_name'] = selected_user['full_name']
        else:
            st.sidebar.warning(f"No users found for role: {selected_role_name}")
            # Clear any existing user session state if no users found
            if 'user_id' in st.session_state:
                del st.session_state['user_id']
            if 'role_id' in st.session_state:
                del st.session_state['role_id']
            if 'role_name' in st.session_state:
                del st.session_state['role_name']
            if 'user_full_name' in st.session_state:
                del st.session_state['user_full_name']
    else:
        # Clear session state if no role selected
        if 'user_id' in st.session_state:
            del st.session_state['user_id']
        if 'role_id' in st.session_state:
            del st.session_state['role_id']
        if 'role_name' in st.session_state:
            del st.session_state['role_name']
        if 'user_full_name' in st.session_state:
            del st.session_state['user_full_name']

    # Display dashboard based on role_id and selected version
    if 'role_id' in st.session_state and 'user_id' in st.session_state:
        role_id = st.session_state['role_id']
        user_id = st.session_state['user_id']
        
        # Get all role IDs for the user
        user_role_ids = database.get_user_role_ids(user_id)
        
        if role_id == 33: # Care Provider role_id 
            care_provider_dashboard_enhanced.show(user_id, user_role_ids)
        elif role_id == 34: # ADMIN role_id
            admin_dashboard.show()
        elif role_id == 35: # Onboarding Team role_id
            onboarding_dashboard.show()
        elif role_id == 36: # Care Coordinator role_id
            care_coordinator_dashboard_enhanced.show(user_id, user_role_ids)
        elif role_id == 39: # Data Entry role_id
            data_entry_dashboard.show()
        else:
            st.error(f"Unknown role ID: {role_id}")
            st.info("Please contact your administrator.")
    else:
        st.info("Select a role and user to begin.")

# Initialize the database

if __name__ == "__main__":
    main()
