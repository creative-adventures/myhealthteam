import streamlit as st
import sqlite3

DB_PATH = 'production.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_users():
    conn = get_db_connection()
    users = conn.execute('SELECT user_id, username, full_name, first_name, last_name, email, status, hire_date FROM users ORDER BY hire_date DESC').fetchall()
    conn.close()
    return users

def get_all_roles():
    conn = get_db_connection()
    roles = conn.execute('SELECT role_id, role_name FROM roles').fetchall()
    conn.close()
    return roles

def get_user_roles_by_user_id(user_id):
    conn = get_db_connection()
    user_roles = conn.execute('SELECT r.role_name, r.role_id, ur.is_primary FROM roles r JOIN user_roles ur ON r.role_id = ur.role_id WHERE ur.user_id = ?', (user_id,)).fetchall()
    conn.close()
    return user_roles

def get_user_role_ids(user_id):
    """Get all role IDs for a specific user"""
    conn = get_db_connection()
    role_ids = conn.execute('SELECT r.role_id FROM roles r JOIN user_roles ur ON r.role_id = ur.role_id WHERE ur.user_id = ?', (user_id,)).fetchall()
    conn.close()
    return [row['role_id'] for row in role_ids]

def get_onboarding_queue_stats():
    """Get onboarding queue statistics"""
    conn = get_db_connection()
    try:
        # Get stats from onboarding_patients table
        onboarding_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_onboarding,
                SUM(CASE WHEN patient_id IS NULL THEN 1 ELSE 0 END) as pending_provider_assignment,
                SUM(CASE WHEN stage1_complete = 0 THEN 1 ELSE 0 END) as pending_initial_contact,
                SUM(CASE WHEN stage2_complete = 0 AND stage1_complete = 1 THEN 1 ELSE 0 END) as pending_tv_visit,
                SUM(CASE WHEN stage3_complete = 0 AND stage2_complete = 1 THEN 1 ELSE 0 END) as pending_documentation,
                SUM(CASE WHEN assigned_pot_user_id IS NULL THEN 1 ELSE 0 END) as unassigned_pot
            FROM onboarding_patients 
            WHERE patient_status = 'Active'
        """).fetchone()
        
        # Get stats from regular patients who might be in onboarding
        patient_stats = conn.execute("""
            SELECT 
                COUNT(CASE WHEN p.status LIKE 'Active%' AND upa.user_id IS NULL THEN 1 END) as unassigned_active_patients,
                COUNT(CASE WHEN p.status = 'Active' AND p.created_date > date('now', '-30 days') THEN 1 END) as new_patients_30_days
            FROM patients p
            LEFT JOIN user_patient_assignments upa ON p.patient_id = upa.patient_id
        """).fetchone()
        
        return {
            'total_onboarding': onboarding_stats['total_onboarding'] or 0,
            'pending_provider_assignment': onboarding_stats['pending_provider_assignment'] or 0,
            'pending_initial_contact': onboarding_stats['pending_initial_contact'] or 0,
            'pending_tv_visit': onboarding_stats['pending_tv_visit'] or 0,
            'pending_documentation': onboarding_stats['pending_documentation'] or 0,
            'unassigned_pot': onboarding_stats['unassigned_pot'] or 0,
            'unassigned_active_patients': patient_stats['unassigned_active_patients'] or 0,
            'new_patients_30_days': patient_stats['new_patients_30_days'] or 0
        }
    finally:
        conn.close()

def get_onboarding_tasks_by_role(role_id, user_id=None):
    """Get onboarding tasks for a specific role or user"""
    conn = get_db_connection()
    try:
        if role_id == 36:  # Care Coordinator
            query = """
                SELECT 
                    op.first_name,
                    op.last_name,
                    op.created_date,
                    CASE 
                        WHEN op.stage1_complete = 0 THEN 'Initial Contact Needed'
                        WHEN op.stage2_complete = 0 THEN 'TV Visit Scheduling'
                        WHEN op.stage3_complete = 0 THEN 'Documentation Review'
                        ELSE 'Ready for Provider Assignment'
                    END as task_status
                FROM onboarding_patients op
                WHERE op.patient_status = 'Active'
                AND (op.assigned_pot_user_id = ? OR op.assigned_pot_user_id IS NULL)
                ORDER BY op.created_date ASC
            """
            tasks = conn.execute(query, (user_id,)).fetchall()
        elif role_id == 33:  # Care Provider
            query = """
                SELECT 
                    op.first_name,
                    op.last_name,
                    op.created_date,
                    'Provider Assignment Needed' as task_status
                FROM onboarding_patients op
                WHERE op.patient_status = 'Active'
                AND op.patient_id IS NULL
                AND op.stage2_complete = 1
                ORDER BY op.created_date ASC
            """
            tasks = conn.execute(query).fetchall()
        else:
            tasks = []
        
        return [dict(task) for task in tasks]
    finally:
        conn.close()

def get_onboarding_patient_details(onboarding_id):
    """Get detailed onboarding patient information for stepper display"""
    conn = get_db_connection()
    try:
        patient = conn.execute("""
            SELECT * FROM onboarding_patients 
            WHERE onboarding_id = ?
        """, (onboarding_id,)).fetchone()
        
        if patient:
            return dict(patient)
        return None
    finally:
        conn.close()

def get_onboarding_queue():
    """Get the current onboarding queue with patient status"""
    conn = get_db_connection()
    try:
        queue = conn.execute("""
            SELECT 
                op.onboarding_id,
                op.first_name || ' ' || op.last_name as patient_name,
                op.stage1_complete,
                op.stage2_complete,
                op.stage3_complete,
                op.stage4_complete,
                op.stage5_complete,
                op.created_date,
                op.updated_date,
                CASE 
                    WHEN NOT op.stage1_complete THEN 'Patient Registration'
                    WHEN NOT op.stage2_complete THEN 'Eligibility Verification'
                    WHEN NOT op.stage3_complete THEN 'Chart Creation'
                    WHEN NOT op.stage4_complete THEN 'Intake Processing'
                    WHEN NOT op.stage5_complete THEN 'TV Visit Scheduling'
                    ELSE 'Workflow Complete'
                END as current_stage,
                CASE 
                    WHEN op.created_date > datetime('now', '-1 day') THEN 'High'
                    WHEN op.created_date > datetime('now', '-3 days') THEN 'Medium'
                    ELSE 'Normal'
                END as priority_status,
                COALESCE(u.full_name, 'Unassigned') as assigned_pot_name
            FROM onboarding_patients op
            LEFT JOIN users u ON op.assigned_pot_user_id = u.user_id
            WHERE op.patient_status = 'Active'
            ORDER BY op.created_date ASC
        """).fetchall()
        
        return [dict(row) for row in queue]
    finally:
        conn.close()

def add_user_role(user_id, role_id):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_id))
        conn.commit()
    except sqlite3.IntegrityError:
        # User already has this role
        pass
    finally:
        conn.close()

def remove_user_role(user_id, role_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM user_roles WHERE user_id = ? AND role_id = ?", (user_id, role_id))
    conn.commit()
    conn.close()

def set_primary_role(user_id, role_id):
    conn = get_db_connection()
    # First, set all roles for the user to not be primary
    conn.execute("UPDATE user_roles SET is_primary = 0 WHERE user_id = ?", (user_id,))
    # Then, set the specified role to be primary
    conn.execute("UPDATE user_roles SET is_primary = 1 WHERE user_id = ? AND role_id = ?", (user_id, role_id))
    conn.commit()
    conn.close()

def get_user_roles():
    conn = get_db_connection()
    roles = conn.execute('SELECT * FROM roles').fetchall()
    conn.close()
    return roles

def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return users

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def get_users_by_role(role_id):
    conn = get_db_connection()
    users = conn.execute("""
        SELECT u.*, r.role_name FROM users u
        JOIN user_roles ur ON u.user_id = ur.user_id
        JOIN roles r ON ur.role_id = r.role_id
        WHERE r.role_id = ?
    """, (role_id,)).fetchall()
    conn.close()
    return users

def get_tasks_by_user(user_id):
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return tasks

def add_user(username, password, first_name, last_name, email, role_name):
    conn = get_db_connection()
    try:
        role = conn.execute('SELECT role_id FROM roles WHERE role_name = ?', (role_name,)).fetchone()
        if role:
            role_id = role['role_id']
            cursor = conn.execute("INSERT INTO users (username, password, first_name, last_name, email, status, hire_date) VALUES (?, ?, ?, ?, ?, 'active', CURRENT_DATE)",
                                  (username, password, first_name, last_name, email))
            user_id = cursor.lastrowid
            conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                         (user_id, role_id))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def get_user_patient_assignments(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            upa.patient_id,
            p.first_name || ' ' || p.last_name AS patient_name,
            upa.role_id,
            upa.user_id,
            p.address_street,
            p.address_city,
            p.address_state,
            p.address_zip,
            p.phone_primary,
            p.email,
            p.status AS patient_status
        FROM
            user_patient_assignments upa
        JOIN
            patients p ON upa.patient_id = p.patient_id
        WHERE
            upa.user_id = ?;
    """, (user_id,))
    assignments = cursor.fetchall()
    conn.close()
    return assignments

def get_coordinator_performance_metrics(user_id):
    conn = get_db_connection()
    try:
        query = """
            SELECT
                u.full_name,
                IFNULL(AVG(t.duration_minutes), 0) AS avg_minutes_per_task,
                IFNULL(COUNT(t.task_id) * 1.0 / COUNT(DISTINCT DATE(t.created_at)), 0) AS avg_tasks_per_day,
                IFNULL(SUM(t.duration_minutes) * 1.0 / COUNT(DISTINCT DATE(t.created_at)), 0) AS avg_minutes_per_day
            FROM users u
            LEFT JOIN tasks t ON u.user_id = t.user_id
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN roles r ON ur.role_id = r.role_id
            WHERE r.role_id IN (36, 40, 39) AND u.user_id = ?
            GROUP BY u.full_name;
        """
        metrics = conn.execute(query, (user_id,)).fetchall()
        return [dict(row) for row in metrics]
    finally:
        conn.close()

def get_care_plan(patient_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT plan_details FROM care_plans WHERE patient_name = ?", (patient_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else ""

def update_care_plan(patient_name, plan_details, updated_by):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO care_plans (patient_name, plan_details, updated_by, last_updated) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                   (patient_name, plan_details, updated_by))
    conn.commit()
    conn.close()


def get_provider_performance_metrics():
    conn = get_db_connection()
    try:
        # Updated to work with existing tables - using provider_tasks instead of patient_visits
        query = """
            SELECT
                u.full_name,
                COALESCE(COUNT(DISTINCT CASE WHEN STRFTIME('%Y-%m', pt.assigned_date) = STRFTIME('%Y-%m', 'now') THEN pt.patient_id END), 0) AS patients_visited_this_month,
                COALESCE(COUNT(DISTINCT upa.patient_id), 0) - COALESCE(COUNT(DISTINCT CASE WHEN STRFTIME('%Y-%m', pt.assigned_date) = STRFTIME('%Y-%m', 'now') THEN pt.patient_id END), 0) AS remaining_visits
            FROM users u
            LEFT JOIN provider_tasks pt ON u.user_id = pt.provider_id
            LEFT JOIN user_patient_assignments upa ON u.user_id = upa.user_id
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN roles r ON ur.role_id = r.role_id
            WHERE r.role_id IN (33, 38)  -- Changed from 37,38 to 33,38 (CP and CPM roles)
            GROUP BY u.full_name;
        """
        metrics = conn.execute(query).fetchall()
        return [dict(row) for row in metrics]
    finally:
        conn.close()

def get_tasks_billing_codes():
    conn = get_db_connection()
    try:
        codes = conn.execute("SELECT code, description FROM task_billing_codes").fetchall()
        return [dict(row) for row in codes]
    finally:
        conn.close()

def get_tasks_billing_codes_by_service_type(service_type):
    """Get task billing codes filtered by service type"""
    conn = get_db_connection()
    try:
        codes = conn.execute("""
            SELECT code_id, task_description, billing_code, description 
            FROM task_billing_codes 
            WHERE service_type = ? 
            ORDER BY task_description
        """, (service_type,)).fetchall()
        return [dict(row) for row in codes]
    finally:
        conn.close()

def get_daily_tasks_for_coordinator():
    conn = get_db_connection()
    try:
        # Get all task descriptions for coordinator tasks from coordinator_task_definitions table
        tasks = conn.execute("SELECT task_description FROM coordinator_task_definitions WHERE task_description IS NOT NULL GROUP BY task_description").fetchall()
        return [dict(row) for row in tasks]
    finally:
        conn.close()


def get_provider_id_from_user_id(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT provider_id FROM providers WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def get_patient_details_by_id(patient_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_provider_counties(provider_id):
    """Get counties for a provider using the new dashboard mapping table"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT DISTINCT 
                dpc.county, 
                dpc.state,
                dpc.patient_count
            FROM dashboard_provider_county_map dpc
            WHERE dpc.provider_id = ? AND dpc.county IS NOT NULL AND dpc.county != ''
            ORDER BY dpc.county
        """, (provider_id,))
        counties = cursor.fetchall()
        return [(c[0], f"{c[0]}, {c[1]} [{c[2]}]") for c in counties]
    finally:
        conn.close()

def get_provider_zip_codes(provider_id):
    """Get zip codes for a provider using the new dashboard mapping table"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT DISTINCT 
                dpz.zip_code, 
                dpz.city, 
                dpz.state,
                dpz.patient_count
            FROM dashboard_provider_zip_map dpz
            WHERE dpz.provider_id = ? AND dpz.zip_code IS NOT NULL AND dpz.zip_code != ''
            ORDER BY dpz.zip_code
        """, (provider_id,))
        zip_codes = cursor.fetchall()
        return [(z[0], f"{z[0]} - {z[1]}, {z[2]} [{z[3]}]") for z in zip_codes]
    finally:
        conn.close()

def get_patient_counties(patient_id):
    """Get counties for a patient using the new dashboard mapping table"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT DISTINCT 
                dpc.county, 
                dpc.state
            FROM dashboard_patient_county_map dpc
            WHERE dpc.patient_id = ? AND dpc.county IS NOT NULL AND dpc.county != ''
            ORDER BY dpc.county
        """, (patient_id,))
        counties = cursor.fetchall()
        return [(c[0], f"{c[0]}, {c[1]}") for c in counties]
    finally:
        conn.close()

def get_patient_zip_codes(patient_id):
    """Get zip codes for a patient using the new dashboard mapping table"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT DISTINCT 
                dpz.zip_code, 
                dpz.city, 
                dpz.state
            FROM dashboard_patient_zip_map dpz
            WHERE dpz.patient_id = ? AND dpz.zip_code IS NOT NULL AND dpz.zip_code != ''
            ORDER BY dpz.zip_code
        """, (patient_id,))
        zip_codes = cursor.fetchall()
        return [(z[0], f"{z[0]} - {z[1]}, {z[2]}") for z in zip_codes]
    finally:
        conn.close()

def save_daily_task(provider_id, patient_id, task_date, task_description, duration_minutes, notes):
    """Save a daily task for a provider to the provider_tasks table"""
    conn = get_db_connection()
    try:
        # Get billing code description from task billing codes table
        billing_code_description = f"{task_description} - {duration_minutes} minutes"
        
        # Insert into provider_tasks table - using correct column names
        # Let SQLite auto-generate the task_id (it's the second column)
        conn.execute("""
            INSERT INTO provider_tasks 
            (task_id, provider_id, patient_id, task_date, notes, minutes_of_service, task_description, billing_code_description)
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
        """, (provider_id, patient_id, task_date, notes, duration_minutes, task_description, billing_code_description))
        
        # Also insert into tasks table for compatibility
        conn.execute("""
            INSERT INTO tasks 
            (patient_name, patient_id, user_id, full_name, staff_code, role_id, task_date, task_type, duration_minutes, service_code, notes, task_state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("", patient_id, provider_id, "", "", 33, task_date, task_description, duration_minutes, "", notes, "completed"))
        
        conn.commit()
        print(f"Task saved successfully for provider {provider_id}")
        return True
    except Exception as e:
        print(f"Error saving task: {e}")
        return False
    finally:
        conn.close()

def save_coordinator_task(coordinator_id, patient_id, task_date, task_description, duration_minutes, notes):
    """Save a daily task for a coordinator to the coordinator_tasks table"""
    conn = get_db_connection()
    try:
        # Get billing code description from task billing codes table
        billing_code_description = f"{task_description} - {duration_minutes} minutes"
        
        # Insert into coordinator_tasks table
        conn.execute("""
            INSERT INTO coordinator_tasks 
            (coordinator_task_id, coordinator_id, patient_id, task_date, notes, duration_minutes, task_description, billing_code_description)
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
        """, (coordinator_id, patient_id, task_date, notes, duration_minutes, task_description, billing_code_description))
        
        conn.commit()
        print(f"Coordinator task saved successfully for coordinator {coordinator_id}")
        return True
    except Exception as e:
        print(f"Error saving coordinator task: {e}")
        return False
    finally:
        conn.close()

def get_all_patients():
    """Get all patients from the database with their status type"""
    conn = get_db_connection()
    try:
        patients = conn.execute("""
            SELECT 
                p.patient_id,
                p.first_name,
                p.last_name,
                p.date_of_birth,
                p.gender,
                p.phone_primary,
                p.phone_secondary,
                p.email,
                p.address_street,
                p.address_city,
                p.address_state,
                p.address_zip,
                p.emergency_contact_name,
                p.emergency_contact_phone,
                p.emergency_contact_relationship,
                p.insurance_primary,
                p.insurance_policy_number,
                p.insurance_secondary,
                p.medical_record_number,
                p.status,
                p.enrollment_date,
                p.discharge_date,
                p.notes,
                p.created_date,
                p.updated_date,
                p.created_by,
                p.updated_by,
                p.current_facility_id,
                p.hypertension,
                p.mental_health_concerns,
                p.dementia,
                p.last_annual_wellness_visit,
                p.last_first_dob,
                pst.status_name,
                pst.description as status_description
            FROM patients p
            LEFT JOIN patient_status_types pst ON p.status = pst.status_name
        """).fetchall()
        return [dict(row) for row in patients]
    finally:
        conn.close()

def get_all_patient_status_types():
    """Get all available patient status types"""
    conn = get_db_connection()
    try:
        status_types = conn.execute("""
            SELECT status_id, status_name, description 
            FROM patient_status_types 
            ORDER BY status_name
        """).fetchall()
        return [dict(row) for row in status_types]
    finally:
        conn.close()

def update_patient_status(patient_id, status):
    """Update the status of a patient"""
    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE patients 
            SET status = ?, updated_date = CURRENT_TIMESTAMP 
            WHERE patient_id = ?
        """, (status, patient_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating patient status: {e}")
        return False
    finally:
        conn.close()


# Onboarding Workflow Functions

def get_onboarding_queue():
    """Get all active onboarding patients with their current status"""
    conn = get_db_connection()
    try:
        query = """
        SELECT 
            op.onboarding_id,
            op.first_name || ' ' || op.last_name AS patient_name,
            op.patient_status,
            op.assigned_pot_user_id,
            u.full_name AS assigned_pot_name,
            wi.status AS workflow_status,
            CASE 
                WHEN op.stage5_complete = 1 THEN 'Completed - Ready for Handoff'
                WHEN op.stage4_complete = 1 THEN 'Stage 5: TV Scheduling'
                WHEN op.stage3_complete = 1 THEN 'Stage 4: Intake Processing'
                WHEN op.stage2_complete = 1 THEN 'Stage 3: Chart Creation'
                WHEN op.stage1_complete = 1 THEN 'Stage 2: Eligibility Verification'
                ELSE 'Stage 1: Patient Registration'
            END AS current_stage,
            CASE
                WHEN op.completed_date IS NOT NULL THEN 'Completed'
                WHEN op.stage5_complete = 1 THEN 'Ready for Handoff'
                ELSE 'In Progress'
            END AS priority_status,
            op.created_date,
            op.updated_date,
            op.completed_date
        FROM onboarding_patients op
        LEFT JOIN workflow_instances wi ON op.workflow_instance_id = wi.instance_id
        LEFT JOIN users u ON op.assigned_pot_user_id = u.user_id
        WHERE op.completed_date IS NULL
        ORDER BY 
            CASE 
                WHEN op.stage5_complete = 1 THEN 1  -- Ready for handoff (highest priority)
                WHEN op.stage4_complete = 1 THEN 2  -- Almost done
                WHEN op.stage3_complete = 1 THEN 3
                WHEN op.stage2_complete = 1 THEN 4
                WHEN op.stage1_complete = 1 THEN 5
                ELSE 6  -- Just started (lowest priority)
            END,
            op.created_date DESC
        """
        result = conn.execute(query).fetchall()
        return [dict(row) for row in result]
    finally:
        conn.close()

def create_onboarding_workflow_instance(patient_data, pot_user_id):
    """Create a new workflow instance and onboarding patient record"""
    conn = get_db_connection()
    try:
        # Create workflow instance
        conn.execute("""
            INSERT INTO workflow_instances (template_id, status, created_at)
            VALUES (14, 'In Progress', datetime('now'))
        """)
        
        workflow_instance_id = conn.lastrowid
        
        # Create onboarding patient record
        conn.execute("""
            INSERT INTO onboarding_patients (
                workflow_instance_id, first_name, last_name, date_of_birth,
                phone_primary, email, gender, emergency_contact_name, emergency_contact_phone,
                address_street, address_city, address_state, address_zip,
                insurance_provider, policy_number, group_number,
                referral_source, referring_provider, referral_date,
                patient_status, facility_assignment, assigned_pot_user_id,
                created_date, updated_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            workflow_instance_id,
            patient_data['first_name'], patient_data['last_name'], patient_data['date_of_birth'],
            patient_data.get('phone_primary'), patient_data.get('email'), patient_data.get('gender'),
            patient_data.get('emergency_contact_name'), patient_data.get('emergency_contact_phone'),
            patient_data.get('address_street'), patient_data.get('address_city'), 
            patient_data.get('address_state'), patient_data.get('address_zip'),
            patient_data.get('insurance_provider'), patient_data.get('policy_number'), 
            patient_data.get('group_number'),
            patient_data.get('referral_source'), patient_data.get('referring_provider'), 
            patient_data.get('referral_date'),
            patient_data.get('patient_status', 'Active'), 
            patient_data.get('facility_assignment'), pot_user_id
        ))
        
        onboarding_id = conn.lastrowid
        
        # Create initial tasks for all workflow steps
        workflow_steps = conn.execute("""
            SELECT step_id, step_order, task_name FROM workflow_steps 
            WHERE template_id = 14 ORDER BY step_order
        """).fetchall()
        
        for step in workflow_steps:
            stage = ((step['step_order'] - 1) // 3) + 1  # Group steps into stages (3 steps per stage roughly)
            if step['step_order'] > 15:  # Handle stage 5 which has more steps
                stage = 5
            
            conn.execute("""
                INSERT INTO onboarding_tasks (
                    onboarding_id, workflow_step_id, task_name, task_stage, 
                    task_order, status, created_date, updated_date
                ) VALUES (?, ?, ?, ?, ?, 'Pending', datetime('now'), datetime('now'))
            """, (onboarding_id, step['step_id'], step['task_name'], stage, step['step_order']))
        
        conn.commit()
        return onboarding_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_onboarding_patient_details(onboarding_id):
    """Get detailed information for a specific onboarding patient"""
    conn = get_db_connection()
    try:
        # Get patient details
        patient = conn.execute("""
            SELECT * FROM onboarding_patients WHERE onboarding_id = ?
        """, (onboarding_id,)).fetchone()
        
        if not patient:
            return None
            
        patient_dict = dict(patient)
        
        # Get tasks for this patient
        tasks = conn.execute("""
            SELECT ot.*, ws.deliverable 
            FROM onboarding_tasks ot
            JOIN workflow_steps ws ON ot.workflow_step_id = ws.step_id
            WHERE ot.onboarding_id = ?
            ORDER BY ot.task_order
        """, (onboarding_id,)).fetchall()
        
        patient_dict['tasks'] = [dict(task) for task in tasks]
        return patient_dict
        
    finally:
        conn.close()

def update_onboarding_stage_completion(onboarding_id, stage_number, completed=True):
    """Update stage completion status"""
    conn = get_db_connection()
    try:
        stage_field = f"stage{stage_number}_complete"
        conn.execute(f"""
            UPDATE onboarding_patients 
            SET {stage_field} = ?, updated_date = datetime('now')
            WHERE onboarding_id = ?
        """, (completed, onboarding_id))
        conn.commit()
    finally:
        conn.close()

def update_onboarding_task_status(task_id, status, user_id, checkbox_data=None):
    """Update individual task status and checkbox data"""
    conn = get_db_connection()
    try:
        query = """
            UPDATE onboarding_tasks 
            SET status = ?, completed_by_user_id = ?, updated_date = datetime('now')
        """
        params = [status, user_id]
        
        if status == 'Complete':
            query += ", completed_date = datetime('now')"
        
        # Update checkbox fields if provided
        if checkbox_data:
            for field, value in checkbox_data.items():
                if hasattr(checkbox_data, field):
                    query += f", {field} = ?"
                    params.append(value)
        
        query += " WHERE task_id = ?"
        params.append(task_id)
        
        conn.execute(query, params)
        conn.commit()
    finally:
        conn.close()

def update_onboarding_patient_assignment(onboarding_id, pot_user_id):
    """Assign an onboarding patient to a POT user"""
    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE onboarding_patients 
            SET assigned_pot_user_id = ?, updated_date = datetime('now')
            WHERE onboarding_id = ?
        """, (pot_user_id, onboarding_id))
        conn.commit()
    finally:
        conn.close()

def update_onboarding_checkbox_data(onboarding_id, checkbox_data):
    """Update checkbox data for an onboarding patient"""
    conn = get_db_connection()
    try:
        # Build dynamic query based on provided checkbox data
        update_fields = []
        params = []
        
        for field, value in checkbox_data.items():
            update_fields.append(f"{field} = ?")
            params.append(value)
        
        if update_fields:
            update_fields.append("updated_date = datetime('now')")
            params.append(onboarding_id)
            
            query = f"""
                UPDATE onboarding_patients 
                SET {', '.join(update_fields)}
                WHERE onboarding_id = ?
            """
            
            conn.execute(query, params)
            conn.commit()
    finally:
        conn.close()

def transfer_onboarding_to_patient_table(onboarding_id):
    """Transfer completed onboarding data to the main patients table"""
    conn = get_db_connection()
    try:
        # Get onboarding data
        onboarding = conn.execute("""
            SELECT * FROM onboarding_patients WHERE onboarding_id = ?
        """, (onboarding_id,)).fetchone()
        
        if not onboarding:
            return None
            
        onboarding_dict = dict(onboarding)
        
        # Check if patient already exists in main table
        existing_patient = None
        if onboarding_dict['patient_id']:
            existing_patient = conn.execute("""
                SELECT patient_id FROM patients WHERE patient_id = ?
            """, (onboarding_dict['patient_id'],)).fetchone()
        
        if existing_patient:
            # Update existing patient with onboarding checkbox data
            conn.execute("""
                UPDATE patients SET
                    medical_records_requested = ?,
                    referral_documents_received = ?,
                    insurance_cards_received = ?,
                    emed_signature_received = ?,
                    hypertension = ?,
                    mental_health_concerns = ?,
                    dementia = ?,
                    updated_date = datetime('now')
                WHERE patient_id = ?
            """, (
                onboarding_dict.get('medical_records_requested', False),
                onboarding_dict.get('referral_documents_received', False),
                onboarding_dict.get('insurance_cards_received', False),
                onboarding_dict.get('emed_signature_received', False),
                onboarding_dict.get('hypertension', False),
                onboarding_dict.get('mental_health_concerns', False),
                onboarding_dict.get('dementia', False),
                onboarding_dict['patient_id']
            ))
            patient_id = onboarding_dict['patient_id']
        else:
            # Create new patient record
            cursor = conn.execute("""
                INSERT INTO patients (
                    first_name, last_name, date_of_birth, gender, phone_primary, email,
                    address_street, address_city, address_state, address_zip,
                    emergency_contact_name, emergency_contact_phone,
                    insurance_primary, insurance_policy_number,
                    medical_records_requested, referral_documents_received,
                    insurance_cards_received, emed_signature_received,
                    hypertension, mental_health_concerns, dementia,
                    enrollment_date, created_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 'Active')
            """, (
                onboarding_dict['first_name'],
                onboarding_dict['last_name'],
                onboarding_dict['date_of_birth'],
                onboarding_dict.get('gender'),
                onboarding_dict.get('phone_primary'),
                onboarding_dict.get('email'),
                onboarding_dict.get('address_street'),
                onboarding_dict.get('address_city'),
                onboarding_dict.get('address_state'),
                onboarding_dict.get('address_zip'),
                onboarding_dict.get('emergency_contact_name'),
                onboarding_dict.get('emergency_contact_phone'),
                onboarding_dict.get('insurance_provider'),
                onboarding_dict.get('policy_number'),
                onboarding_dict.get('medical_records_requested', False),
                onboarding_dict.get('referral_documents_received', False),
                onboarding_dict.get('insurance_cards_received', False),
                onboarding_dict.get('emed_signature_received', False),
                onboarding_dict.get('hypertension', False),
                onboarding_dict.get('mental_health_concerns', False),
                onboarding_dict.get('dementia', False)
            ))
            patient_id = cursor.lastrowid
            
            # Update onboarding record with patient_id
            conn.execute("""
                UPDATE onboarding_patients SET patient_id = ? WHERE onboarding_id = ?
            """, (patient_id, onboarding_id))
        
        # Mark onboarding as complete
        conn.execute("""
            UPDATE onboarding_patients 
            SET completed_date = datetime('now'), updated_date = datetime('now')
            WHERE onboarding_id = ?
        """, (onboarding_id,))
        
        conn.commit()
        return patient_id
        
    finally:
        conn.close()

def get_users_by_role_name(role_name):
    """Get all users with a specific role by role name"""
    conn = get_db_connection()
    try:
        users = conn.execute("""
            SELECT u.user_id, u.username, u.full_name 
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN roles r ON ur.role_id = r.role_id
            WHERE r.role_name = ?
        """, (role_name,)).fetchall()
        return [dict(user) for user in users]
    finally:
        conn.close()
