# Patient Care Provider Manager (PCPM) Workflow Design

**Document Version:** 1.0  
**Last Updated:** January 17, 2025  
**Author:** System Design Team  
**Purpose:** Comprehensive workflow design for Patient Care Provider Managers with regional provider assignment capabilities

---

## Executive Summary

This document outlines the detailed workflow design for Patient Care Provider Managers (PCPMs) within the ZEN Medical system. PCPMs function as both providers and managers, requiring all standard provider functionality plus additional management capabilities for regional provider assignments during patient onboarding.

**Key Features:**
- All standard provider workflow capabilities (Tabs 1 & 2)
- Third tab for regional provider assignment management
- Initial telehealth visit (TV) assessment workflow
- Automated provider assignment based on geographic and workload factors
- Integration with patient onboarding pipeline

---

## Role Definition and Responsibilities

### 1.1 PCPM Core Functions

**As a Provider (Standard Workflow):**
- Patient care delivery and documentation
- Daily task management and billing
- Care coordination and communication
- All functions outlined in Provider Workflow Design

**As a Manager (Additional Workflow):**
- Conduct initial telehealth visits for new patients
- Assess patient conditions and care requirements
- Assign regional providers based on:
  - Geographic proximity (zip code mapping)
  - Provider specialization and capabilities
  - Current provider workload
  - Patient-specific needs

### 1.2 Patient Onboarding Role

**PCPM Position in Onboarding Workflow:**
```
Patient Intake → Eligibility Check → Chart Creation → PCPM Initial TV → Regional Provider Assignment → Care Handoff
```

**PCPM Specific Tasks:**
1. **Initial TV (Telehealth Visit):** First provider contact with new patient
2. **Condition Assessment:** Check for 4 key conditions:
   - Hypertension
   - Mental Health concerns (depression, anxiety)
   - Dementia
   - Last Annual Wellness Visit (AWV) date
3. **Provider Assignment:** Select appropriate regional provider
4. **Care Handoff:** Transfer patient to assigned regional provider

---

## Tab Structure Overview

### Tab 1: Patient Panel (Standard Provider View)
- All patients assigned to PCPM as primary provider
- Standard provider patient management functionality
- Identical to standard provider workflow

### Tab 2: Daily Tasks (Standard Provider View)
- Task entry and management for PCPM's direct patient care
- Standard provider task recording functionality
- Identical to standard provider workflow

### Tab 3: Regional Provider Assignment (Manager View)
- New patients requiring regional provider assignment
- Initial TV scheduling and completion
- Provider assignment workflow
- Assignment tracking and management

---

## Tab 3: Regional Provider Assignment Workflow

### 3.1 Assignment Queue Dashboard

**Data Source:** ZEN Medical Onboarding (ZMO) + Provider Database

**Queue Structure:**
```javascript
const AssignmentQueue = {
    patientId: String,
    patientName: String,           // Format: "LAST, FIRST"
    dateOfBirth: Date,
    contactInfo: {
        phone: String,
        address: String,
        city: String,
        state: String,
        zipCode: String
    },
    facility: String,              // Patient facility
    insuranceInfo: {
        primary: String,
        policyNumber: String
    },
    onboardingStatus: String,      // "Ready for Initial TV", "TV Scheduled", "TV Completed", "Assignment Pending"
    initialTVDate: Date,
    initialTVCompleted: Boolean,
    assessmentResults: {
        hypertension: Boolean,
        mentalHealth: Boolean,
        dementia: Boolean,
        lastAWVDate: Date
    },
    recommendedProvider: String,   // System recommendation
    assignedProvider: String,      // Final assignment
    assignmentDate: Date,
    priority: String,              // "High", "Medium", "Low"
    notes: String
};
```

### 3.2 Assignment Queue Filters

**Primary Filters:**
- **Status:** Ready for TV, TV Scheduled, TV Completed, Assignment Pending, All
- **Priority:** High, Medium, Low, All
- **Date Range:** Today, This Week, This Month, Custom

**Secondary Filters:**
- **Facility:** Dropdown of all facilities
- **Zip Code:** Geographic filtering
- **Insurance:** Primary insurance type
- **Assessment Status:** Complete, Incomplete, Not Started

### 3.3 Assignment Queue Display

**Color-Coded Priority System:**
```css
.priority-high { background-color: #ffebee; border-left: 4px solid #f44336; }
.priority-medium { background-color: #fff3e0; border-left: 4px solid #ff9800; }
.priority-low { background-color: #e8f5e8; border-left: 4px solid #4caf50; }
.tv-overdue { background-color: #ffcdd2; }
.tv-today { background-color: #fff9c4; }
.assignment-ready { background-color: #c8e6c9; }
```

**Queue Table Layout:**
```
| Patient Name ↓ | Facility | Zip | Status ↓ | TV Date | Priority | Actions |
|----------------|----------|-----|----------|---------|----------|----------|
| SMITH, JOHN    | Acacia   | 90210| TV Ready| -       | High     | [Schedule TV] |
| DOE, JANE      | Violet   | 91325| TV Done | 01/15   | Medium   | [Assign Provider] |
```

### 3.4 Initial TV Scheduling Interface

**TV Scheduling Modal:**
```html
<div class="tv-scheduling-modal">
    <h3>Schedule Initial TV - [Patient Name]</h3>
    
    <div class="patient-summary">
        <p><strong>Patient:</strong> [Name, DOB]</p>
        <p><strong>Contact:</strong> [Phone]</p>
        <p><strong>Facility:</strong> [Facility Name]</p>
        <p><strong>Insurance:</strong> [Primary Insurance]</p>
    </div>
    
    <div class="scheduling-options">
        <label>TV Date:</label>
        <input type="datetime-local" id="tvDate" required>
        
        <label>Duration (minutes):</label>
        <select id="duration">
            <option value="30">30 minutes</option>
            <option value="45">45 minutes</option>
            <option value="60">60 minutes</option>
        </select>
        
        <label>Priority:</label>
        <select id="priority">
            <option value="high">High - Urgent conditions</option>
            <option value="medium">Medium - Standard</option>
            <option value="low">Low - Routine</option>
        </select>
        
        <label>Notes:</label>
        <textarea id="schedulingNotes" placeholder="Special considerations, patient preferences, etc."></textarea>
    </div>
    
    <div class="modal-actions">
        <button onclick="scheduleTV()">Schedule TV</button>
        <button onclick="closeModal()">Cancel</button>
    </div>
</div>
```

### 3.5 Initial TV Assessment Form

**Assessment Interface:**
```html
<div class="tv-assessment-form">
    <h3>Initial TV Assessment - [Patient Name]</h3>
    
    <div class="assessment-checklist">
        <h4>Key Condition Assessment</h4>
        
        <div class="condition-check">
            <label>
                <input type="checkbox" id="hypertension">
                <strong>Hypertension</strong> - Patient has history or current diagnosis
            </label>
            <textarea placeholder="Notes on hypertension status, medications, control..."></textarea>
        </div>
        
        <div class="condition-check">
            <label>
                <input type="checkbox" id="mentalHealth">
                <strong>Mental Health Concerns</strong> - Depression, anxiety, or other mental health conditions
            </label>
            <textarea placeholder="Notes on mental health status, medications, severity..."></textarea>
        </div>
        
        <div class="condition-check">
            <label>
                <input type="checkbox" id="dementia">
                <strong>Dementia</strong> - Cognitive impairment or dementia diagnosis
            </label>
            <textarea placeholder="Notes on cognitive status, stage, support needs..."></textarea>
        </div>
        
        <div class="awv-section">
            <label><strong>Last Annual Wellness Visit (AWV):</strong></label>
            <input type="date" id="lastAWV">
            <textarea placeholder="Notes on AWV status, due date, scheduling needs..."></textarea>
        </div>
    </div>
    
    <div class="general-assessment">
        <h4>General Assessment</h4>
        <textarea placeholder="Overall patient condition, immediate needs, care priorities..."></textarea>
    </div>
    
    <div class="provider-recommendation">
        <h4>Provider Assignment Recommendation</h4>
        <select id="recommendedProvider">
            <option value="">Select Recommended Provider...</option>
            <!-- Populated based on zip code and specialization -->
        </select>
        <textarea placeholder="Rationale for provider recommendation..."></textarea>
    </div>
    
    <div class="assessment-actions">
        <button onclick="saveAssessment()">Save Assessment</button>
        <button onclick="completeAssessment()">Complete & Proceed to Assignment</button>
    </div>
</div>
```

### 3.6 Provider Assignment Interface

**Assignment Decision Support:**
```javascript
const ProviderAssignmentData = {
    availableProviders: [
        {
            providerId: String,
            providerName: String,
            specializations: Array,     // ["Hypertension", "Mental Health", "Dementia"]
            currentCaseload: Number,
            maxCaseload: Number,
            zipCodesServed: Array,
            distanceFromPatient: Number, // Miles
            lastAssignmentDate: Date,
            performanceRating: Number,   // 1-5 scale
            availabilityStatus: String   // "Available", "At Capacity", "Limited"
        }
    ],
    assignmentCriteria: {
        geographicProximity: Number,    // Weight 0-1
        specialization: Number,         // Weight 0-1
        workloadBalance: Number,        // Weight 0-1
        performanceHistory: Number      // Weight 0-1
    }
};
```

**Assignment Interface:**
```html
<div class="provider-assignment-interface">
    <h3>Assign Regional Provider - [Patient Name]</h3>
    
    <div class="patient-assessment-summary">
        <h4>Assessment Summary</h4>
        <div class="conditions-summary">
            <span class="condition hypertension">Hypertension: [Yes/No]</span>
            <span class="condition mental-health">Mental Health: [Yes/No]</span>
            <span class="condition dementia">Dementia: [Yes/No]</span>
            <span class="awv-status">Last AWV: [Date]</span>
        </div>
    </div>
    
    <div class="provider-recommendations">
        <h4>Recommended Providers</h4>
        
        <div class="provider-card recommended">
            <div class="provider-header">
                <h5>[Provider Name] - RECOMMENDED</h5>
                <span class="match-score">Match Score: 95%</span>
            </div>
            <div class="provider-details">
                <p><strong>Distance:</strong> 2.3 miles</p>
                <p><strong>Specializations:</strong> Hypertension, Mental Health</p>
                <p><strong>Current Caseload:</strong> 45/60 patients</p>
                <p><strong>Performance Rating:</strong> 4.8/5</p>
                <p><strong>Availability:</strong> Available</p>
            </div>
            <button class="assign-provider" onclick="assignProvider('[ProviderId]')">Assign Provider</button>
        </div>
        
        <!-- Additional provider cards -->
    </div>
    
    <div class="assignment-notes">
        <label><strong>Assignment Notes:</strong></label>
        <textarea placeholder="Rationale for assignment, special considerations..."></textarea>
    </div>
    
    <div class="assignment-actions">
        <button onclick="finalizeAssignment()">Finalize Assignment</button>
        <button onclick="requestManagerReview()">Request Manager Review</button>
    </div>
</div>
```

---

## Automated Assignment Logic

### 4.1 Geographic Assignment Algorithm

```javascript
function calculateGeographicScore(patientZip, providerZipCodes) {
    const patientCoords = getCoordinatesFromZip(patientZip);
    let minDistance = Infinity;
    
    providerZipCodes.forEach(zip => {
        const providerCoords = getCoordinatesFromZip(zip);
        const distance = calculateDistance(patientCoords, providerCoords);
        minDistance = Math.min(minDistance, distance);
    });
    
    // Score decreases with distance (max 100 for same zip, 0 for >50 miles)
    return Math.max(0, 100 - (minDistance * 2));
}
```

### 4.2 Specialization Matching

```javascript
function calculateSpecializationScore(patientConditions, providerSpecializations) {
    let matchCount = 0;
    let totalConditions = 0;
    
    const conditionMap = {
        hypertension: 'Hypertension',
        mentalHealth: 'Mental Health',
        dementia: 'Dementia'
    };
    
    Object.keys(patientConditions).forEach(condition => {
        if (patientConditions[condition]) {
            totalConditions++;
            if (providerSpecializations.includes(conditionMap[condition])) {
                matchCount++;
            }
        }
    });
    
    return totalConditions > 0 ? (matchCount / totalConditions) * 100 : 50;
}
```

### 4.3 Workload Balancing

```javascript
function calculateWorkloadScore(currentCaseload, maxCaseload) {
    const utilizationRate = currentCaseload / maxCaseload;
    
    if (utilizationRate >= 1.0) return 0;      // At capacity
    if (utilizationRate >= 0.9) return 20;     // Near capacity
    if (utilizationRate >= 0.8) return 50;     // High utilization
    if (utilizationRate >= 0.6) return 80;     // Moderate utilization
    return 100;                                 // Low utilization
}
```

### 4.4 Overall Assignment Score

```javascript
function calculateAssignmentScore(patient, provider, weights) {
    const geoScore = calculateGeographicScore(patient.zipCode, provider.zipCodesServed);
    const specScore = calculateSpecializationScore(patient.conditions, provider.specializations);
    const workloadScore = calculateWorkloadScore(provider.currentCaseload, provider.maxCaseload);
    const performanceScore = provider.performanceRating * 20; // Convert 1-5 to 0-100
    
    return (
        geoScore * weights.geographic +
        specScore * weights.specialization +
        workloadScore * weights.workload +
        performanceScore * weights.performance
    );
}
```

---

## Integration with Existing Workflows

### 5.1 Provider Workflow Integration

**Tab 1 & 2 Functionality:**
- PCPMs retain all standard provider capabilities
- Patient panel includes both direct patients and management oversight
- Daily tasks include both clinical and administrative activities

**Shared Data Elements:**
- Patient database integration
- Billing code system
- Time tracking and reporting
- EHR integration

### 5.2 Onboarding Workflow Integration

**Upstream Integration:**
- Receives patients from Patient Onboarding Team
- Integrates with eligibility verification system
- Connects to EMed chart creation process

**Downstream Integration:**
- Hands off patients to assigned regional providers
- Triggers coordinator assignment process
- Updates ZMO status tracking

### 5.3 Coordinator Workflow Integration

**PCCM Coordination:**
- Provides patient data for coordinator assignment
- Shares assessment results for care planning
- Coordinates care transition activities

---

## Reporting and Analytics

### 6.1 PCPM Performance Metrics

**Assignment Efficiency:**
- Average time from TV to assignment: Target <24 hours
- Assignment accuracy rate: Target >95%
- Provider satisfaction with assignments: Target >4.5/5

**Clinical Assessment Quality:**
- Condition identification accuracy
- Assessment completeness rate
- Follow-up care coordination effectiveness

**Workload Management:**
- Number of initial TVs per day/week
- Assignment queue processing time
- Provider workload distribution balance

### 6.2 Assignment Analytics Dashboard

```javascript
const AssignmentAnalytics = {
    dailyMetrics: {
        newPatients: Number,
        tvsCompleted: Number,
        assignmentsCompleted: Number,
        averageAssignmentTime: Number // Hours
    },
    weeklyMetrics: {
        totalAssignments: Number,
        providerUtilization: Object, // {providerId: utilizationRate}
        geographicDistribution: Object, // {zipCode: patientCount}
        conditionBreakdown: Object // {condition: patientCount}
    },
    qualityMetrics: {
        assignmentAccuracy: Number,
        patientSatisfaction: Number,
        providerSatisfaction: Number,
        careTransitionSuccess: Number
    }
};
```

### 6.3 Reporting Interface

**Dashboard Components:**
- Real-time assignment queue status
- Daily/weekly assignment volume
- Provider workload distribution
- Geographic coverage analysis
- Quality metrics tracking

---

## Security and Compliance

### 7.1 Data Access Controls

**PCPM Access Levels:**
- **Full Access:** Own patient panel and assignment queue
- **Read Access:** Regional provider information and availability
- **Limited Access:** Patient assessment data (HIPAA compliant)

**Audit Trail Requirements:**
- All assignment decisions logged
- Assessment data access tracked
- Provider selection rationale documented

### 7.2 HIPAA Compliance

**Protected Health Information (PHI):**
- Secure transmission of patient data
- Role-based access controls
- Audit logging for all PHI access
- Data encryption at rest and in transit

---

## Implementation Roadmap

### Phase 1: Core PCPM Infrastructure (Weeks 1-2)
- Extend provider database schema for PCPM role
- Create assignment queue data structure
- Implement basic Tab 3 interface
- Set up initial TV scheduling system

### Phase 2: Assessment and Assignment (Weeks 3-4)
- Build TV assessment form and workflow
- Implement provider assignment algorithm
- Create assignment decision support interface
- Integrate with existing provider data

### Phase 3: Automation and Integration (Weeks 5-6)
- Implement automated assignment recommendations
- Integrate with onboarding workflow
- Build reporting and analytics dashboard
- Create notification and alert system

### Phase 4: Testing and Optimization (Weeks 7-8)
- User acceptance testing with PCPMs
- Performance optimization
- Security audit and compliance verification
- Training material development

---

## Success Metrics

### 8.1 Efficiency Metrics
- **Assignment Speed:** <24 hours from TV to assignment
- **Queue Processing:** <2 hours average queue time
- **Provider Utilization:** 80-90% optimal range
- **Geographic Coverage:** <10 miles average patient-provider distance

### 8.2 Quality Metrics
- **Assignment Accuracy:** >95% appropriate assignments
- **Patient Satisfaction:** >4.5/5 with assigned provider
- **Provider Satisfaction:** >4.5/5 with assignment quality
- **Care Continuity:** >90% successful care transitions

### 8.3 Business Impact
- **Onboarding Efficiency:** 50% reduction in assignment time
- **Provider Workload Balance:** <10% variance in caseloads
- **Patient Access:** 100% of patients assigned within SLA
- **System Scalability:** Support 3x patient volume growth

---

## Conclusion

The PCPM workflow design provides a comprehensive solution for managing both clinical care delivery and regional provider assignments. By extending the standard provider workflow with specialized management capabilities, PCPMs can efficiently handle patient onboarding while maintaining their clinical responsibilities.

The three-tab interface ensures seamless integration between provider and manager functions, while automated assignment algorithms optimize provider utilization and patient care quality. The design emphasizes efficiency, accuracy, and scalability while maintaining compliance with healthcare regulations.

---

**Next Steps:**
1. Review and approve PCPM workflow design
2. Begin Phase 1 implementation
3. Coordinate with PCCM workflow development
4. Plan integration with existing provider and coordinator systems
5. Establish success metrics tracking and reporting