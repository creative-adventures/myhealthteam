# Provider Workflow Detailed Analysis

**Last Updated:** January 17, 2025  
**Author:** System Analyst  
**Status:** Comprehensive Review

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Provider Workflow Structure](#current-provider-workflow-structure)
3. [Provider Google Sheet (PGS) System Analysis](#provider-google-sheet-pgs-system-analysis)
4. [Task Categories and Billing Codes](#task-categories-and-billing-codes)
5. [Daily Workflow Patterns](#daily-workflow-patterns)
6. [Pain Points and Challenges](#pain-points-and-challenges)
7. [Database Requirements for Provider Workflow](#database-requirements-for-provider-workflow)
8. [Recommended System Design](#recommended-system-design)
9. [Implementation Strategy](#implementation-strategy)

## Executive Summary

The provider workflow analysis reveals a complex, spreadsheet-based system managing patient visits, billing, task tracking, and care coordination. Providers currently use a 5-tab Google Sheet system (PGS) with detailed billing codes, patient panels, and time tracking. The system handles multiple visit types (home, telehealth, office) with precise minute-based billing calculations and extensive CPT code management.

### Key Findings:
- **2,218 different task/billing combinations** in the Provider Tasks and Codes system
- **5-tab PGS structure** managing all provider activities
- **Minute-based billing** with automatic CPT code assignment
- **Geographic assignment** through zip code mapping
- **Complex workflow** spanning patient care, documentation, and billing

## Current Provider Workflow Structure

### Provider Google Sheet (PGS) - 5 Tab System

#### Tab 1: PSL (Provider Service Log)
**Purpose:** Primary visit tracking and service documentation

**Provider View Structure:**
- Patient identification (Last, First DOB)
- Date of Service (DOS)
- Service type and location
- Minutes spent
- EHR integration status
- Wound care details (if applicable)
- Service notes and documentation

**Admin-Only Fields (Hidden from Provider):**
- Billing codes (automatically calculated in background)
- Billing status and claim tracking
- Payment information
- Reimbursement details

**Key Visit Types:**
- **NEW HOME VISIT:** 75min → 99345
- **FOLLOW UP HOME VISIT:** 60min → 99350, 40min → 99349
- **NEW TELEVISIT/OFFICE VISIT:** 60min → 99205, 45min → 99024
- **FOLLOW UP TELE/OFFICE VISIT:** 45min → 99215, 30min → 99214
- **ACUTE TELEVISIT:** 15min → 99213

#### Tab 2: Panel Patient List (Patient Panel)
**Purpose:** Patient assignment and status tracking with comprehensive patient overview

**Current Features:**
- Assigned patients with facility/HHC information
- Assigned Patient Care Coordinator (PCC)
- Color-coded status system:
  - **Green:** Newly assigned patients
  - **Red:** Haven't been seen in 2+ months (based on PSL DOS)
  - **Black:** Regular follow-up patients

**Enhanced Tab1 Patient Panel Design Requirements:**

##### Core Data Elements
1. **Patient Name** (from ZMO and PSL data)
   - Format: "Last, First" (consistent with PSL format)
   - Source: ZMO "Patient Last, First" field
   - Backup: PSL "Patient Last, First DOB" field

2. **Chart Code** (if available)
   - Medical record number or internal patient ID
   - Source: ZMO patient tracking system
   - Display: "Chart: [CODE]" or "No Chart" if unavailable

3. **Last Visited Date**
   - Source: Most recent "DOS" (Date of Service) from PSL data
   - Cross-reference: ZMO "Previous Visit" field
   - Format: MM/DD/YYYY
   - Calculation: MAX(DOS) WHERE patient_id = current_patient

##### Color-Coded Status System (Enhanced)
- **🟢 Green (Newly Assigned):** 
  - Last visit within 7 days OR newly assigned patient
  - Criteria: DOS within last 7 days OR assignment_date within 7 days
  
- **🔴 Red (Overdue - Priority):** 
  - Haven't been seen in 60+ days (2+ months)
  - Criteria: MAX(DOS) > 60 days ago
  - Display: "OVERDUE: [X] days" 
  
- **⚫ Black (Active/Regular):** 
  - Regular follow-up patients (8-59 days since last visit)
  - Criteria: 8 ≤ days_since_last_visit ≤ 59
  
- **🟡 Yellow (Due Soon):** 
  - Patients due for visit within next 7 days
  - Criteria: Based on care plan schedule or 30-45 day intervals

##### Data Integration Logic
```sql
-- Patient Panel Query
SELECT 
    p.patient_id,
    COALESCE(zmo.patient_name, psl.patient_name) as patient_name,
    zmo.chart_code,
    MAX(psl.date_of_service) as last_visit_date,
    DATEDIFF(CURDATE(), MAX(psl.date_of_service)) as days_since_visit,
    CASE 
        WHEN DATEDIFF(CURDATE(), MAX(psl.date_of_service)) <= 7 THEN 'newly_assigned'
        WHEN DATEDIFF(CURDATE(), MAX(psl.date_of_service)) >= 60 THEN 'overdue'
        WHEN DATEDIFF(CURDATE(), MAX(psl.date_of_service)) BETWEEN 8 AND 59 THEN 'active'
        ELSE 'unknown'
    END as status,
    pp.assigned_coordinator_id,
    pp.assigned_facility
FROM provider_patient_panel pp
LEFT JOIN patients p ON pp.patient_id = p.patient_id
LEFT JOIN zmo_data zmo ON p.patient_id = zmo.patient_id
LEFT JOIN provider_service_log psl ON p.patient_id = psl.patient_id
WHERE pp.provider_id = [CURRENT_PROVIDER_ID]
GROUP BY p.patient_id
ORDER BY 
    CASE status
        WHEN 'overdue' THEN 1
        WHEN 'newly_assigned' THEN 2
        WHEN 'active' THEN 3
        ELSE 4
    END,
    days_since_visit DESC;
```

##### Enhanced Display Format
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Provider Patient Panel - Dr. Smith                     [Refresh] [Export]    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🔴 Johnson, Mary          Chart: MRN-12345    Last Visit: 11/15/24         │
│    OVERDUE: 67 days      Coordinator: Mike R.  Facility: Sunrise Manor     │
│    [Schedule Visit] [View History] [Contact] [Notes]                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🟢 Smith, John           Chart: MRN-67890     Last Visit: 01/20/25         │
│    Newly Assigned       Coordinator: Sarah J.  Facility: Golden Years      │
│    [Schedule Visit] [View History] [Contact] [Notes]                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ ⚫ Williams, Bob         Chart: No Chart      Last Visit: 01/10/25         │
│    Active (7 days)      Coordinator: Lisa K.   Facility: Home Care         │
│    [Schedule Visit] [View History] [Contact] [Notes]                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

##### Filtering and Sorting Options
- **Status Filter:** All, Overdue Only, Newly Assigned, Active
- **Facility Filter:** By assigned facility/HHC
- **Coordinator Filter:** By assigned care coordinator
- **Sort Options:** 
  - By Status (Overdue first)
  - By Last Visit Date (oldest first)
  - By Patient Name (alphabetical)
  - By Days Since Visit (highest first)

##### Mobile Responsive Design
```
┌─────────────────────────┐
│ 🔴 Johnson, Mary        │
│ Chart: MRN-12345        │
│ Last: 11/15/24 (67d)    │
│ Coord: Mike R.          │
│ [Visit] [Call] [Notes]  │
├─────────────────────────┤
│ 🟢 Smith, John          │
│ Chart: MRN-67890        │
│ Last: 01/20/25 (New)    │
│ Coord: Sarah J.         │
│ [Visit] [Call] [Notes]  │
└─────────────────────────┘
```

#### Tab 3: Preferred Zip Codes
**Purpose:** Geographic service area management

**Current System:**
- Provider-specific zip code assignments
- Regional coverage mapping
- Service area optimization

#### Tab 4: CM Phone Review Log
**Purpose:** Care Management time tracking for providers

**Features:**
- Provider-specific CM Log
- Total minutes tracking for specific patients
- Calendar integration
- Separate from PSL billing

#### Tab 5: Other/Free Text
**Purpose:** Additional notes and miscellaneous information

## Task Categories and Service Types

**Note**: Service types are tracked for time and task management. Billing is handled automatically in a separate system.

**📋 For Billing Information**: All billing codes, rates, and financial reporting are documented separately in the **[Billing System Design](./Billing_System_Design.md)** document. This separation ensures providers can focus on patient care while billing is processed automatically in the background.

### Primary Care Provider (PCP) Visits

#### Home Visits
- **New Patient Home Visits:** Initial comprehensive visits at patient residence
- **Established Patient Home Visits:** Follow-up visits at patient residence
- **Acute/Urgent Home Visits:** Urgent care visits at patient residence
- **Time Tracking:** Automatic start/stop with visit entry
- **Documentation:** Integrated with visit notes

#### Telehealth Visits
- **New Patient Telehealth:** Initial virtual consultations
- **Established Patient Telehealth:** Follow-up virtual visits
- **Acute Telehealth:** Urgent virtual care

#### Office Visits
- **New Patient Office:** Initial in-office consultations
- **Established Patient Office:** Follow-up office visits

### Provider Clinical Tasks

#### Wound Care Services *(Currently Excluded)*
*Note: Wound Care (WC) tasks are excluded from current workflow implementation but will remain in the database schema for future activation. No role assignments are currently made for WC task codes.*

- ~~**WC-Assess/Dressing (Home):** Wound assessment and dressing changes at patient's home~~
- ~~**WC-Assess/Dressing (Office):** Wound assessment and dressing changes in office setting~~
- ~~**WC-Debrid Selective (Home):** Selective wound debridement at patient's home~~
- ~~**WC-Debrid Selective (Office):** Selective wound debridement in office setting~~

#### Preventive Care Services
- **BHI (Behavioral Health Integration):** Mental health screening and intervention
- **AWV (Annual Wellness Visit):** Comprehensive annual health assessments
- **Smoking Cessation:** Tobacco cessation counseling and support
- **TCM (Transitional Care Management):** Post-discharge care coordination

#### Specialized Procedures
- **ELVT:** Endovenous laser vein treatment
- **Foam:** Foam sclerotherapy procedures

#### Administrative Tasks
- **Chart Documentation:** Medical record updates and clinical notes
- **Treatment Planning:** Developing and updating patient care plans
- **Prescription Management:** Medication prescribing and monitoring
- **Clinical Decision Making:** Diagnosis and treatment decisions

*Note: Care coordination tasks (CCM, PCM, communication, data entry) are handled by Patient Care Coordinators (PCC) and documented separately in the PCC workflow.*

## Daily Workflow Patterns

### Morning Routine
1. **Dashboard Review:** Check assigned patients and scheduled visits
2. **Patient Status Check:** Review color-coded patient list
3. **Schedule Planning:** Organize home visits and telehealth appointments
4. **Priority Task Identification:** Focus on overdue patients (red status)

### During Patient Care
1. **Visit Execution:** Conduct home, office, or telehealth visits
2. **Real-time Documentation:** Record visit details in PSL
3. **Time Tracking:** Log exact minutes for billing accuracy
4. **EHR Integration:** Update electronic health records

### Administrative Tasks
1. **Care Coordination:** Phone calls with specialists, facilities, family
2. **Documentation Review:** Process lab results, imaging, specialist notes
3. **Medication Management:** Handle refills, prior authorizations
4. **Care Plan Management:** Monthly CCM/PCM activities

### End-of-Day Activities
1. **PSL Completion:** Finalize all visit entries
2. **Billing Review:** Verify CPT codes and billing amounts
3. **EHR Status Update:** Ensure all notes are downloaded/completed
4. **Next Day Planning:** Review upcoming patient needs

## Pain Points and Challenges

### Current System Limitations

#### 1. Manual Data Entry
- **Issue:** Extensive manual entry in multiple spreadsheet tabs
- **Impact:** Time-consuming, error-prone, inefficient
- **Example:** Providers must manually enter patient info, calculate billing codes, track time

#### 2. Complex Billing Code Management
- **Issue:** 2,218 different task/billing combinations to navigate
- **Impact:** Confusion, billing errors, compliance risks
- **Example:** Minute-based billing requires precise time tracking and code selection

#### 3. Fragmented Information
- **Issue:** Data spread across 5 tabs with limited integration
- **Impact:** Difficulty getting comprehensive patient view
- **Example:** Patient status in Tab 2, billing in Tab 1, notes in Tab 5

#### 4. Limited Automation
- **Issue:** Minimal automated calculations or workflows
- **Impact:** Increased administrative burden
- **Example:** Manual CPT code lookup and billing calculations

#### 5. Geographic Assignment Complexity
- **Issue:** Manual zip code to provider matching
- **Impact:** Inefficient patient assignments, travel time issues
- **Example:** TeleHealth capabilities not factored into assignments

#### 6. EHR Integration Gaps
- **Issue:** Manual tracking of EHR note status
- **Impact:** Documentation delays, compliance concerns
- **Example:** Separate tracking of "EHR Note Downloaded-Done" status

### Workflow Inefficiencies

#### 1. Duplicate Data Entry
- Patient information entered multiple times across tabs
- Visit details recorded in both PSL and EHR systems
- Billing information manually transferred to billing system

#### 2. Time Tracking Challenges
- Manual minute calculation for billing
- Separate time tracking for CM Log vs PSL
- Difficulty aggregating total provider productivity

#### 3. Patient Status Management
- Color-coding system requires manual updates
- No automated alerts for overdue patients
- Limited visibility into patient care continuity

## Database Requirements for Provider Workflow

### Core Tables Needed

#### 1. Providers Table
```sql
CREATE TABLE providers (
    provider_id INT PRIMARY KEY,
    provider_code VARCHAR(20) UNIQUE, -- e.g., 'ZEN-DIA'
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    credentials VARCHAR(100),
    status ENUM('active', 'inactive', 'on_hold'),
    max_patients INT,
    specializations TEXT,
    contact_email VARCHAR(100),
    contact_phone VARCHAR(20),
    created_date TIMESTAMP,
    updated_date TIMESTAMP
);
```

#### 2. Provider_Service_Log Table
```sql
CREATE TABLE provider_service_log (
    psl_id INT PRIMARY KEY,
    provider_id INT,
    patient_id INT,
    date_of_service DATE,
    service_type VARCHAR(100),
    service_location ENUM('home', 'telehealth', 'office', 'facility'),
    patient_type ENUM('new', 'established'),
    minutes_spent INT,
    hospice_patient BOOLEAN,
    notes TEXT,
    ehr_status ENUM('pending', 'downloaded', 'completed'),
    ehr_chief_complaint TEXT,
    ehr_assessment_dx TEXT,
    ehr_staff_initials VARCHAR(10),
    ehr_filename VARCHAR(255),
    created_date TIMESTAMP,
    updated_date TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);
```

**Note:** Billing-related tables and schemas are maintained separately in the **Billing System Design** document to ensure proper separation of concerns.

#### 3. Provider_Zip_Codes Table
```sql
CREATE TABLE provider_zip_codes (
    assignment_id INT PRIMARY KEY,
    provider_id INT,
    zip_code VARCHAR(10),
    region_name VARCHAR(100),
    priority_level INT, -- 1=primary, 2=secondary, etc.
    telehealth_available BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
);
```

#### 4. Provider_Patient_Panel Table
```sql
CREATE TABLE provider_patient_panel (
    panel_id INT PRIMARY KEY,
    provider_id INT,
    patient_id INT,
    assigned_date DATE,
    status ENUM('newly_assigned', 'active', 'overdue', 'inactive'),
    last_visit_date DATE,
    assigned_facility VARCHAR(100),
    assigned_coordinator_id INT,
    notes TEXT,
    created_date TIMESTAMP,
    updated_date TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (assigned_coordinator_id) REFERENCES coordinators(coordinator_id)
);
```

#### 5. Provider_CM_Log Table
```sql
CREATE TABLE provider_cm_log (
    cm_log_id INT PRIMARY KEY,
    provider_id INT,
    patient_id INT,
    log_date DATE,
    activity_type VARCHAR(100),
    minutes_spent INT,
    description TEXT,
    calendar_entry BOOLEAN,
    created_date TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);
```

#### 6. Task_Billing_Codes Table
```sql
CREATE TABLE task_billing_codes (
    code_id INT PRIMARY KEY,
    task_description TEXT,
    service_type VARCHAR(100),
    location_type VARCHAR(50),
    patient_type VARCHAR(50),
    min_minutes INT,
    max_minutes INT,
    primary_cpt_code VARCHAR(10),
    additional_codes TEXT, -- JSON for multiple codes
    billing_rate DECIMAL(10,2),
    effective_date DATE,
    expiration_date DATE,
    created_date TIMESTAMP
);
```

### Key Relationships and Constraints

1. **Provider-Patient Assignment:** Many-to-many through provider_patient_panel
2. **Geographic Coverage:** Provider zip code assignments with priority levels
3. **Billing Code Automation:** Automatic code lookup based on service type, location, patient type, and minutes
4. **Time Tracking:** Separate tracking for billable PSL time and CM Log time
5. **Status Management:** Automated patient status updates based on last visit date

## Recommended System Design

### Provider Dashboard Design

#### 1. Daily Summary Cards
```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Patients      │ │   Visits        │ │   Time Logged   │ │   Tasks         │
│      15         │ │      8          │ │    6.5 hrs      │ │      12         │
│   Assigned      │ │   Completed     │ │    Today        │ │   Pending       │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

#### 2. Patient Panel View
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ My Patient Panel                                    [Filter: All ▼] [Sort ▼] │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🟢 Smith, John (DOB: 01/15/1945)     Last Visit: 01/20/25  Next Due: CCM    │
│    📍 90210 Beverly Hills            Coordinator: Sarah J.   Priority: High  │
│    [Record Visit] [View Chart] [Contact]                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🔴 Johnson, Mary (DOB: 03/22/1938)   Last Visit: 11/15/24  OVERDUE: 67 days │
│    📍 90211 Beverly Hills            Coordinator: Mike R.    Priority: High  │
│    [Record Visit] [View Chart] [Contact]                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ ⚫ Williams, Bob (DOB: 07/08/1942)   Last Visit: 01/10/25  Next Due: F/U    │
│    📍 90212 Beverly Hills            Coordinator: Lisa K.    Priority: Med   │
│    [Record Visit] [View Chart] [Contact]                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3. Quick Visit Entry Form
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Record Patient Visit                                              [Save] [×] │
├─────────────────────────────────────────────────────────────────────────────┤
│ Patient: [Smith, John (DOB: 01/15/1945)        ▼]                           │
│ Date:    [01/17/2025                           ▼]                           │
│ Type:    [🏠 Home Visit ▼] [👤 Established ▼]                               │
│ Minutes: [60                                   ] ⏱️ Auto-tracked            │
│ Notes:   [Follow-up for chronic conditions...                             ] │
│          [                                                                 ] │
│ EHR:     [☐ Note Downloaded] [☐ Assessment Complete]                       │
│ Status:  [✅ Visit Recorded - Processing in background]                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mobile-Responsive Design

#### Provider Mobile App Features
1. **Quick Patient Lookup:** Search by name or scan QR code
2. **Voice-to-Text Notes:** Hands-free documentation
3. **Offline Capability:** Work without internet, sync later
4. **GPS Integration:** Automatic location detection for home visits
5. **Time Tracking:** One-tap start/stop timers

### Automation Features

#### 1. Automatic Task Management
```javascript
function autoUpdatePatientStatus(serviceRecord) {
    const {
        patientName,
        chartCode,
        serviceDate,
        serviceType
    } = serviceRecord;
    
    // Update patient panel status
    const statusUpdate = {
        last_visit_date: serviceDate,
        last_service_type: serviceType,
        status: calculatePatientStatus(serviceDate),
        next_due_date: calculateNextDueDate(serviceDate, serviceType)
    };
    
    ProviderPatientPanel.updateOne(
        { chart_code: chartCode },
        { $set: statusUpdate }
    );
    
    return statusUpdate;
}

function calculatePatientStatus(lastVisitDate) {
    const daysSinceVisit = Math.floor(
        (new Date() - new Date(lastVisitDate)) / (1000 * 60 * 60 * 24)
    );
    
    if (daysSinceVisit <= 7) return 'recent';
    if (daysSinceVisit <= 30) return 'current';
    if (daysSinceVisit <= 60) return 'due_soon';
    return 'overdue';
}
```

#### 2. Geographic Assignment Algorithm
```javascript
function assignPatientToProvider(patientZipCode) {
    // Find providers serving this zip code
    const eligibleProviders = ProviderZipCodes.find({
        zip_code: patientZipCode,
        active_status: true
    }).populate('provider_id');
    
    // Calculate current patient load for each provider
    const providerLoads = eligibleProviders.map(pz => {
        const currentLoad = ProviderPatientPanel.countDocuments({
            provider_id: pz.provider_id,
            status: { $in: ['current', 'due_soon', 'overdue'] }
        });
        
        return {
            provider_id: pz.provider_id,
            provider_name: pz.provider_id.provider_name,
            current_load: currentLoad,
            max_capacity: pz.max_patients || 150
        };
    });
    
    // Assign to provider with lowest load percentage
    const bestProvider = providerLoads.reduce((best, current) => {
        const currentPercentage = current.current_load / current.max_capacity;
        const bestPercentage = best.current_load / best.max_capacity;
        return currentPercentage < bestPercentage ? current : best;
    });
    
    return bestProvider;
}
```

#### 3. Provider Task Management System
```javascript
function getProviderTaskCategories() {
    return {
        'PCP-Visit': {
            locations: ['Home (HO)', 'Office (OF)', 'Telehealth (TE)', 'Board&Care/GroupHome (HO)', 'ILF (HO)', 'Nursing Facility (NU)'],
            patient_types: ['NEW pt', 'ESTAB pt'],
            time_ranges: ['10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90-99', '100-109', '110-119', '120-129']
        },
        'WC-Assess/Dressing': {
            locations: ['Home (HO)', 'Office (OF)'],
            patient_types: ['NEW pt', 'ESTAB pt'],
            time_ranges: ['10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90-99', '100-109', '110-119', '120-129']
        },
        'WC-Debrid Selective': {
            locations: ['Home (HO)', 'Office (OF)'],
            patient_types: ['NEW pt', 'ESTAB pt'],
            parameters: ['time_minutes', 'wound_size_sqcm']
        },
        'PCP-Preventive': {
            services: ['BHI', 'AWV', 'Smoking Cessation', 'ACP', 'TCM'],
            locations: ['Home (HO)', 'Office (OF)', 'Telehealth (TE)']
        },
        'PCP-Administrative': {
            services: ['Home Health CPO Call/Orders', 'Home Health Cert', 'Home Health Recert'],
            note_type: 'NoEHRNote'
        },
        'Procedures': {
            types: ['ELVT', 'Foam']
        }
    };
}

function generateProviderTaskSummary(providerId, date = new Date()) {
    const tasks = ProviderServiceLog.find({
        provider_id: providerId,
        visit_date: date
    });
    
    const summary = {
        total_visits: 0,
        pcp_visits: 0,
        wound_care: 0,
        preventive_care: 0,
        total_time_minutes: 0,
        locations: {
            home: 0,
            office: 0,
            telehealth: 0,
            nursing_facility: 0
        }
    };
    
    tasks.forEach(task => {
        summary.total_visits++;
        summary.total_time_minutes += task.time_spent_minutes;
        
        if (task.service_category.startsWith('PCP-Visit')) {
            summary.pcp_visits++;
            if (task.service_category.includes('(HO)')) summary.locations.home++;
            else if (task.service_category.includes('(OF)')) summary.locations.office++;
            else if (task.service_category.includes('(TE)')) summary.locations.telehealth++;
            else if (task.service_category.includes('(NU)')) summary.locations.nursing_facility++;
        } else if (task.service_category.startsWith('WC-')) {
            summary.wound_care++;
        } else if (task.service_category.includes('Prev')) {
            summary.preventive_care++;
        }
    });
    
    return summary;
}
```

## Implementation Strategy

### Phase 1: Core Provider System (Weeks 1-3)

#### Week 1: Database and Authentication
- Set up cloud database (Google Cloud SQL)
- Create provider, patient, and PSL tables
- Implement user authentication and role management
- Import existing provider and patient data

#### Week 2: Basic PSL Functionality
- Build provider dashboard with patient panel
- Implement visit entry form with auto-billing
- Create basic reporting for daily summaries
- Test with 1-2 providers

#### Week 3: Enhanced Features
- Add EHR status tracking
- Implement patient status automation
- Create mobile-responsive interface
- Add offline capability

### Phase 2: Advanced Features (Weeks 4-6)

#### Week 4: Geographic and Assignment Features
- Implement zip code to provider mapping
- Add patient assignment workflows
- Create coordinator integration points
- Build advanced reporting

#### Week 5: Billing Integration
- Connect to existing billing system
- Implement claim tracking
- Add payment status management
- Create 1099 integration preparation

#### Week 6: CM Log and Time Tracking
- Build provider CM Log functionality
- Implement separate time tracking
- Add calendar integration
- Create productivity analytics

### Phase 3: Full Migration (Weeks 7-8)

#### Week 7: Data Migration
- Complete migration from Google Sheets
- Validate data integrity
- Train all providers on new system
- Run parallel systems for validation

#### Week 8: Go-Live and Optimization
- Switch to new system full-time
- Monitor performance and usage
- Address any issues or feedback
- Optimize workflows based on real usage

### Success Metrics

#### Efficiency Improvements
- **50% reduction** in time spent on administrative tasks
- **90% accuracy** in billing code selection
- **100% real-time** patient status updates
- **Zero data entry duplication**

#### Quality Improvements
- **Complete audit trail** for all provider activities
- **Automated compliance** checking
- **Real-time dashboard** for provider productivity
- **Mobile accessibility** for field work

#### Workflow Benefits
- **Streamlined visit entry** with automatic time tracking
- **Simplified patient panel management** with color-coded status
- **Automated task reminders** and follow-up notifications
- **Mobile-optimized interface** for field work
- **Provider focus on patient care** - administrative complexity removed from provider workflow

---

*This analysis provides the foundation for designing a comprehensive provider workflow system that maintains the familiar structure while adding significant automation, accuracy, and efficiency improvements.*