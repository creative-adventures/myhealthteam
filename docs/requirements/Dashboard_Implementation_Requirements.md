# Dashboard Implementation Requirements

## Role IDs
- 33: Care Provider (CP)
- 34: ADMIN
- 35: Onboarding Team (OT)
- 36: Care Coordinator (CC)
- 37: Lead Coordinator (LC) - Note: This role doesn't exist in current DB
- 38: Care Provider Manager (CPM)
- 39: Data Entry
- 40: Coordinator Manager (CM)

## Task Requirements

### 1. Dashboard Tables Setup
- [x] Analyze existing dashboard structure
- [x] Set up dashboard tables with awesome_table components (fallback to standard table)
- [x] Implement elements components for metrics visualization (using standard Streamlit components)
- [x] Ensure tables display properly for all roles
- [x] Enhanced table visualization with metrics cards

### 2. Daily Tasks Entry Forms
- [x] Ensure daily tasks entry forms work for coordinators
- [x] Ensure daily tasks entry forms work for providers
- [x] Implement proper form validation and submission
- [x] Add dynamic task entry capabilities
- [x] Enhanced task entry forms with better UI/UX

### 3. Data Visualization
- [x] Implement awesome_table for enhanced table functionality (fallback to standard table)
- [x] Add elements components for metrics display (using standard Streamlit components)
- [x] Create responsive dashboard layouts
- [x] Ensure cross-role compatibility
- [x] Enhanced metrics display with Streamlit elements

### 4. Cross-Role Compatibility
- [x] Verify coordinator dashboard daily tasks work
- [x] Verify provider dashboard daily tasks work
- [x] Ensure both roles can submit tasks properly
- [x] Test with different user roles and permissions
- [x] Enhanced cross-role functionality

## Technical Implementation Details

### Current Dashboard Structure
- `care_provider_dashboard_awesome_table_fixed.py` - Current provider dashboard with awesome_table
- `care_coordinator_dashboard.py` - Current coordinator dashboard
- `data_entry_dashboard.py` - Basic data entry dashboard
- `app.py` - Main application routing

### Database Tables
- `provider_tasks` - Provider task records
- `tasks` - General task records
- `tasks_billing_codes` - Task billing codes
- `user_patient_assignments` - User-patient assignment mapping
- `patients` - Patient information
- `providers` - Provider information
- `coordinators` - Coordinator information

### Key Functions to Implement
- `save_daily_task()` - Save provider daily tasks
- Enhanced task entry forms for both roles
- Proper patient assignment handling
- Role-based access control for task entries
