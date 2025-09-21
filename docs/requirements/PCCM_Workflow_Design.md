# Patient Care Coordinator Manager (PCCM) Workflow Design

**Document Version:** 1.0  
**Last Updated:** January 17, 2025  
**Author:** System Design Team  
**Purpose:** Comprehensive workflow design for Patient Care Coordinator Managers with coordinator assignment and oversight capabilities

---

## Executive Summary

This document outlines the detailed workflow design for Patient Care Coordinator Managers (PCCMs) within the ZEN Medical system. PCCMs function as both coordinators and managers, requiring all standard coordinator functionality plus additional management capabilities for coordinator assignments during patient onboarding and ongoing oversight.

**Key Features:**
- All standard coordinator workflow capabilities (Tabs 1 & 2)
- Third tab for coordinator assignment and oversight management
- Workload balancing and assignment optimization
- Performance monitoring and quality assurance
- Integration with patient onboarding pipeline

---

## Role Definition and Responsibilities

### 1.1 PCCM Core Functions

**As a Coordinator (Standard Workflow):**
- Patient care coordination and documentation
- Daily task management and time tracking
- Care plan management and billing integration
- All functions outlined in Patient Care Coordinator Workflow Design

**As a Manager (Additional Workflow):**
- Assign patient care coordinators to new patients
- Monitor coordinator workloads and performance
- Balance caseloads across coordinator team
- Oversee quality of care coordination
- Manage coordinator scheduling and availability

### 1.2 Patient Onboarding Role

**PCCM Position in Onboarding Workflow:**
```
PCPM Initial TV → Regional Provider Assignment → PCCM Coordinator Assignment → Care Coordination Begins
```

**PCCM Specific Tasks:**
1. **Coordinator Assignment:** Select appropriate coordinator for new patient
2. **Workload Management:** Balance assignments across coordinator team
3. **Specialization Matching:** Match patient needs with coordinator expertise
4. **Quality Oversight:** Monitor assignment outcomes and care quality

---

## Tab Structure Overview

### Tab 1: Patient Panel (Standard Coordinator View)
- All patients assigned to PCCM as primary coordinator
- Standard coordinator patient management functionality
- Identical to standard coordinator workflow

### Tab 2: Daily Tasks (Standard Coordinator View)
- Task entry and management for PCCM's direct patient care
- Standard coordinator task recording functionality
- Identical to standard coordinator workflow

### Tab 3: Coordinator Assignment & Oversight (Manager View)
- New patients requiring coordinator assignment
- Team workload monitoring and balancing
- Coordinator performance oversight
- Assignment tracking and management

---

## Tab 3: Coordinator Assignment & Oversight Workflow

### 3.1 Assignment Queue Dashboard

**Data Source:** ZEN Medical Onboarding (ZMO) + Coordinator Database + Patient Assignment History

**Assignment Queue Structure:**
```javascript
const CoordinatorAssignmentQueue = {
    patientId: String,
    patientName: String,           // Format: "LAST, FIRST"
    dateOfBirth: Date,
    assignedProvider: String,      // Regional provider assigned by PCPM
    facility: String,              // Patient facility
    zipCode: String,
    insuranceInfo: {
        primary: String,
        policyNumber: String
    },
    careRequirements: {
        ccmEligible: Boolean,
        pcmEligible: Boolean,
        specialNeeds: Array,       // ["Mental Health", "Dementia", "Complex Medical"]
        visitFrequency: String,    // "Monthly", "Bi-weekly", "Weekly"
        languagePreference: String
    },
    onboardingStatus: String,      // "Ready for Assignment", "Assignment Pending", "Assigned", "Active"
    assignmentDate: Date,
    assignedCoordinator: String,
    assignmentPriority: String,    // "High", "Medium", "Low"
    notes: String,
    providerHandoffDate: Date
};
```

### 3.2 Team Workload Overview

**Coordinator Team Dashboard:**
```javascript
const CoordinatorTeamData = {
    coordinators: [
        {
            coordinatorId: String,
            coordinatorName: String,
            specializations: Array,     // ["CCM", "PCM", "Mental Health", "Dementia"]
            currentCaseload: Number,
            maxCaseload: Number,
            utilizationRate: Number,    // Percentage
            avgTasksPerDay: Number,
            avgMinutesPerPatient: Number,
            performanceRating: Number,  // 1-5 scale
            availabilityStatus: String, // "Available", "At Capacity", "Limited", "Unavailable"
            lastAssignmentDate: Date,
            workingHours: {
                start: String,          // "08:00"
                end: String,            // "17:00"
                timezone: String
            },
            languagesSpoken: Array,
            facilitiesServed: Array
        }
    ],
    teamMetrics: {
        totalPatients: Number,
        avgUtilization: Number,
        pendingAssignments: Number,
        overdueAssignments: Number
    }
};
```

### 3.3 Assignment Queue Filters

**Primary Filters:**
- **Status:** Ready for Assignment, Assignment Pending, Recently Assigned, All
- **Priority:** High, Medium, Low, All
- **Date Range:** Today, This Week, This Month, Custom
- **Assignment Status:** Unassigned, Assigned Today, Overdue Assignment

**Secondary Filters:**
- **Facility:** Dropdown of all facilities
- **Provider:** Assigned regional provider
- **Care Type:** CCM, PCM, Both, Standard
- **Special Needs:** Mental Health, Dementia, Complex Medical, Language

### 3.4 Assignment Queue Display

**Color-Coded Priority System:**
```css
.priority-high { background-color: #ffebee; border-left: 4px solid #f44336; }
.priority-medium { background-color: #fff3e0; border-left: 4px solid #ff9800; }
.priority-low { background-color: #e8f5e8; border-left: 4px solid #4caf50; }
.assignment-overdue { background-color: #ffcdd2; }
.assignment-today { background-color: #fff9c4; }
.assignment-ready { background-color: #c8e6c9; }
.recently-assigned { background-color: #e1f5fe; }
```

**Queue Table Layout:**
```
| Patient Name ↓ | Provider | Facility | Care Type | Priority | Days Pending | Actions |
|----------------|----------|----------|-----------|----------|--------------|----------|
| SMITH, JOHN    | Szalas   | Acacia   | CCM+PCM   | High     | 2 days       | [Assign] |
| DOE, JANE      | Antonio  | Violet   | CCM       | Medium   | 1 day        | [Assign] |
```

### 3.5 Coordinator Assignment Interface

**Assignment Decision Support:**
```javascript
const CoordinatorAssignmentData = {
    patientRequirements: {
        careType: String,              // "CCM", "PCM", "Both"
        specialNeeds: Array,
        languagePreference: String,
        facility: String,
        complexity: String             // "Low", "Medium", "High"
    },
    availableCoordinators: [
        {
            coordinatorId: String,
            coordinatorName: String,
            matchScore: Number,        // 0-100 calculated match score
            specializations: Array,
            currentUtilization: Number, // Percentage
            availableCapacity: Number, // Number of additional patients
            languageMatch: Boolean,
            facilityExperience: Boolean,
            lastAssignmentDate: Date,
            avgResponseTime: Number,   // Hours
            patientSatisfactionScore: Number
        }
    ],
    assignmentCriteria: {
        workloadBalance: Number,       // Weight 0-1
        specialization: Number,        // Weight 0-1
        experience: Number,            // Weight 0-1
        availability: Number           // Weight 0-1
    }
};
```

**Assignment Interface:**
```html
<div class="coordinator-assignment-interface">
    <h3>Assign Coordinator - [Patient Name]</h3>
    
    <div class="patient-requirements-summary">
        <h4>Patient Requirements</h4>
        <div class="requirements-grid">
            <div class="requirement">
                <label>Care Type:</label>
                <span class="care-type">[CCM/PCM/Both]</span>
            </div>
            <div class="requirement">
                <label>Provider:</label>
                <span class="provider">[Assigned Provider]</span>
            </div>
            <div class="requirement">
                <label>Facility:</label>
                <span class="facility">[Facility Name]</span>
            </div>
            <div class="requirement">
                <label>Special Needs:</label>
                <span class="special-needs">[Mental Health, Dementia, etc.]</span>
            </div>
            <div class="requirement">
                <label>Language:</label>
                <span class="language">[Preferred Language]</span>
            </div>
        </div>
    </div>
    
    <div class="coordinator-recommendations">
        <h4>Recommended Coordinators</h4>
        
        <div class="coordinator-card recommended">
            <div class="coordinator-header">
                <h5>[Coordinator Name] - RECOMMENDED</h5>
                <span class="match-score">Match Score: 92%</span>
            </div>
            <div class="coordinator-details">
                <div class="detail-row">
                    <span class="label">Specializations:</span>
                    <span class="value">CCM, PCM, Mental Health</span>
                </div>
                <div class="detail-row">
                    <span class="label">Current Caseload:</span>
                    <span class="value">28/35 patients (80%)</span>
                </div>
                <div class="detail-row">
                    <span class="label">Available Capacity:</span>
                    <span class="value">7 patients</span>
                </div>
                <div class="detail-row">
                    <span class="label">Performance Rating:</span>
                    <span class="value">4.7/5</span>
                </div>
                <div class="detail-row">
                    <span class="label">Avg Response Time:</span>
                    <span class="value">2.3 hours</span>
                </div>
                <div class="detail-row">
                    <span class="label">Language Match:</span>
                    <span class="value match">✓ English, Spanish</span>
                </div>
                <div class="detail-row">
                    <span class="label">Facility Experience:</span>
                    <span class="value match">✓ Acacia (15 patients)</span>
                </div>
            </div>
            <button class="assign-coordinator" onclick="assignCoordinator('[CoordinatorId]')">Assign Coordinator</button>
        </div>
        
        <!-- Additional coordinator cards with lower match scores -->
    </div>
    
    <div class="assignment-notes">
        <label><strong>Assignment Notes:</strong></label>
        <textarea placeholder="Rationale for assignment, special considerations, handoff instructions..."></textarea>
    </div>
    
    <div class="assignment-actions">
        <button onclick="finalizeAssignment()">Finalize Assignment</button>
        <button onclick="scheduleHandoff()">Schedule Handoff Meeting</button>
        <button onclick="requestReview()">Request Senior Review</button>
    </div>
</div>
```

### 3.6 Team Workload Management

**Workload Balancing Dashboard:**
```html
<div class="workload-management-dashboard">
    <h3>Team Workload Overview</h3>
    
    <div class="team-metrics-summary">
        <div class="metric-card">
            <h4>Team Utilization</h4>
            <div class="metric-value">78%</div>
            <div class="metric-trend">↑ 3% from last week</div>
        </div>
        <div class="metric-card">
            <h4>Pending Assignments</h4>
            <div class="metric-value">12</div>
            <div class="metric-trend">↓ 5 from yesterday</div>
        </div>
        <div class="metric-card">
            <h4>Overdue Assignments</h4>
            <div class="metric-value alert">3</div>
            <div class="metric-trend">⚠ Requires attention</div>
        </div>
    </div>
    
    <div class="coordinator-workload-grid">
        <div class="coordinator-workload-card">
            <div class="coordinator-header">
                <h5>[Coordinator Name]</h5>
                <span class="status available">Available</span>
            </div>
            <div class="workload-details">
                <div class="caseload-bar">
                    <div class="caseload-fill" style="width: 80%"></div>
                    <span class="caseload-text">28/35 patients</span>
                </div>
                <div class="workload-metrics">
                    <div class="metric">
                        <span class="label">Avg Tasks/Day:</span>
                        <span class="value">15.2</span>
                    </div>
                    <div class="metric">
                        <span class="label">Avg Minutes/Patient:</span>
                        <span class="value">45</span>
                    </div>
                    <div class="metric">
                        <span class="label">Last Assignment:</span>
                        <span class="value">2 days ago</span>
                    </div>
                </div>
            </div>
            <div class="coordinator-actions">
                <button onclick="viewCoordinatorDetails('[CoordinatorId]')">View Details</button>
                <button onclick="assignPatient('[CoordinatorId]')">Assign Patient</button>
            </div>
        </div>
        
        <!-- Additional coordinator cards -->
    </div>
</div>
```

---

## Automated Assignment Logic

### 4.1 Workload Balancing Algorithm

```javascript
function calculateWorkloadScore(coordinator) {
    const utilizationRate = coordinator.currentCaseload / coordinator.maxCaseload;
    const taskLoad = coordinator.avgTasksPerDay;
    const timeLoad = coordinator.avgMinutesPerPatient;
    
    // Prefer coordinators with lower utilization
    let score = 100 - (utilizationRate * 100);
    
    // Adjust for task complexity
    if (taskLoad > 20) score -= 10;
    if (timeLoad > 60) score -= 10;
    
    // Bonus for availability
    if (coordinator.availabilityStatus === 'Available') score += 10;
    
    return Math.max(0, score);
}
```

### 4.2 Specialization Matching

```javascript
function calculateSpecializationScore(patientNeeds, coordinatorSpecializations) {
    let matchCount = 0;
    let totalNeeds = 0;
    
    // Care type matching
    if (patientNeeds.careType === 'CCM' && coordinatorSpecializations.includes('CCM')) {
        matchCount++;
    }
    if (patientNeeds.careType === 'PCM' && coordinatorSpecializations.includes('PCM')) {
        matchCount++;
    }
    if (patientNeeds.careType === 'Both') {
        if (coordinatorSpecializations.includes('CCM')) matchCount++;
        if (coordinatorSpecializations.includes('PCM')) matchCount++;
        totalNeeds = 2;
    } else {
        totalNeeds = 1;
    }
    
    // Special needs matching
    patientNeeds.specialNeeds.forEach(need => {
        totalNeeds++;
        if (coordinatorSpecializations.includes(need)) {
            matchCount++;
        }
    });
    
    return totalNeeds > 0 ? (matchCount / totalNeeds) * 100 : 50;
}
```

### 4.3 Experience and Performance Scoring

```javascript
function calculateExperienceScore(coordinator, patientFacility) {
    let score = coordinator.performanceRating * 20; // Convert 1-5 to 0-100
    
    // Facility experience bonus
    if (coordinator.facilitiesServed.includes(patientFacility)) {
        score += 15;
    }
    
    // Response time factor
    if (coordinator.avgResponseTime <= 2) score += 10;
    else if (coordinator.avgResponseTime <= 4) score += 5;
    
    // Patient satisfaction factor
    score += coordinator.patientSatisfactionScore * 10;
    
    return Math.min(100, score);
}
```

### 4.4 Language and Cultural Matching

```javascript
function calculateLanguageScore(patientLanguage, coordinatorLanguages) {
    if (patientLanguage === 'English' || !patientLanguage) {
        return coordinatorLanguages.includes('English') ? 100 : 50;
    }
    
    return coordinatorLanguages.includes(patientLanguage) ? 100 : 0;
}
```

### 4.5 Overall Assignment Score

```javascript
function calculateCoordinatorAssignmentScore(patient, coordinator, weights) {
    const workloadScore = calculateWorkloadScore(coordinator);
    const specializationScore = calculateSpecializationScore(patient.careRequirements, coordinator.specializations);
    const experienceScore = calculateExperienceScore(coordinator, patient.facility);
    const languageScore = calculateLanguageScore(patient.careRequirements.languagePreference, coordinator.languagesSpoken);
    
    return (
        workloadScore * weights.workloadBalance +
        specializationScore * weights.specialization +
        experienceScore * weights.experience +
        languageScore * weights.language
    );
}
```

---

## Performance Monitoring and Quality Assurance

### 5.1 Coordinator Performance Metrics

**Individual Performance Tracking:**
```javascript
const CoordinatorPerformanceMetrics = {
    coordinatorId: String,
    monthlyMetrics: {
        patientsAssigned: Number,
        tasksCompleted: Number,
        avgTaskCompletionTime: Number, // Hours
        billableMinutes: Number,
        patientSatisfactionScore: Number,
        careGapsResolved: Number,
        communicationResponseTime: Number // Hours
    },
    qualityMetrics: {
        documentationAccuracy: Number,  // Percentage
        careplanCompletionRate: Number, // Percentage
        billingAccuracy: Number,        // Percentage
        patientRetentionRate: Number    // Percentage
    },
    workloadMetrics: {
        currentCaseload: Number,
        utilizationRate: Number,
        overtimeHours: Number,
        burnoutRiskScore: Number        // 1-10 scale
    }
};
```

### 5.2 Quality Assurance Dashboard

```html
<div class="quality-assurance-dashboard">
    <h3>Team Quality Metrics</h3>
    
    <div class="quality-metrics-grid">
        <div class="quality-metric-card">
            <h4>Documentation Quality</h4>
            <div class="metric-chart">
                <!-- Chart showing documentation accuracy trends -->
            </div>
            <div class="metric-details">
                <span class="current-value">94.2%</span>
                <span class="target">Target: >95%</span>
            </div>
        </div>
        
        <div class="quality-metric-card">
            <h4>Patient Satisfaction</h4>
            <div class="metric-chart">
                <!-- Chart showing satisfaction scores -->
            </div>
            <div class="metric-details">
                <span class="current-value">4.6/5</span>
                <span class="target">Target: >4.5</span>
            </div>
        </div>
        
        <div class="quality-metric-card">
            <h4>Care Plan Completion</h4>
            <div class="metric-chart">
                <!-- Chart showing completion rates -->
            </div>
            <div class="metric-details">
                <span class="current-value">97.8%</span>
                <span class="target">Target: >95%</span>
            </div>
        </div>
    </div>
    
    <div class="performance-alerts">
        <h4>Performance Alerts</h4>
        <div class="alert warning">
            <span class="alert-icon">⚠</span>
            <span class="alert-message">Coordinator Smith: Documentation accuracy below target (92%)</span>
            <button class="alert-action">Review</button>
        </div>
        <div class="alert info">
            <span class="alert-icon">ℹ</span>
            <span class="alert-message">Coordinator Johnson: Approaching capacity (33/35 patients)</span>
            <button class="alert-action">Monitor</button>
        </div>
    </div>
</div>
```

---

## Integration with Existing Workflows

### 6.1 Coordinator Workflow Integration

**Tab 1 & 2 Functionality:**
- PCCMs retain all standard coordinator capabilities
- Patient panel includes both direct patients and management oversight
- Daily tasks include both coordination and administrative activities

**Shared Data Elements:**
- Patient database integration
- Task tracking and billing system
- Time tracking and reporting
- Care plan management

### 6.2 Onboarding Workflow Integration

**Upstream Integration:**
- Receives patients from PCPM after provider assignment
- Integrates with provider handoff process
- Connects to patient assessment data

**Downstream Integration:**
- Assigns coordinators to begin care coordination
- Triggers initial care plan creation
- Updates patient status in onboarding system

### 6.3 Provider Workflow Integration

**PCPM Coordination:**
- Receives patient data and assessment results
- Coordinates care transition from provider to coordinator
- Shares patient care requirements and priorities

---

## Reporting and Analytics

### 7.1 PCCM Management Reports

**Assignment Efficiency Reports:**
- Average time from handoff to assignment
- Assignment accuracy and patient satisfaction
- Coordinator workload distribution
- Assignment criteria effectiveness

**Team Performance Reports:**
- Individual coordinator performance metrics
- Team productivity and efficiency trends
- Quality assurance metrics
- Patient outcome correlations

**Workload Analysis Reports:**
- Caseload distribution and balance
- Utilization rates and capacity planning
- Burnout risk assessment
- Staffing optimization recommendations

### 7.2 Analytics Dashboard

```javascript
const PCCMAnalyticsDashboard = {
    assignmentMetrics: {
        dailyAssignments: Number,
        avgAssignmentTime: Number,      // Hours
        assignmentAccuracy: Number,     // Percentage
        pendingAssignments: Number
    },
    teamMetrics: {
        totalCoordinators: Number,
        avgUtilization: Number,
        teamProductivity: Number,
        qualityScore: Number
    },
    patientMetrics: {
        totalPatients: Number,
        newPatients: Number,
        patientSatisfaction: Number,
        careOutcomes: Number
    },
    trends: {
        assignmentVolume: Array,        // Historical data
        utilizationTrends: Array,
        qualityTrends: Array,
        satisfactionTrends: Array
    }
};
```

---

## Security and Compliance

### 8.1 Data Access Controls

**PCCM Access Levels:**
- **Full Access:** Own patient panel and team assignment data
- **Read Access:** Coordinator performance and workload data
- **Limited Access:** Patient care requirements (HIPAA compliant)
- **Administrative Access:** Team management and reporting

**Audit Trail Requirements:**
- All assignment decisions logged with rationale
- Performance data access tracked
- Patient data access monitored
- Management actions documented

### 8.2 HIPAA Compliance

**Protected Health Information (PHI):**
- Secure transmission of patient assignment data
- Role-based access controls for team management
- Audit logging for all PHI access
- Data encryption at rest and in transit
- Minimum necessary access principle

---

## Implementation Roadmap

### Phase 1: Core PCCM Infrastructure (Weeks 1-2)
- Extend coordinator database schema for PCCM role
- Create assignment queue and team management data structure
- Implement basic Tab 3 interface
- Set up coordinator assignment system

### Phase 2: Assignment and Workload Management (Weeks 3-4)
- Build coordinator assignment algorithm and interface
- Implement workload balancing and monitoring
- Create team performance dashboard
- Integrate with existing coordinator data

### Phase 3: Quality Assurance and Analytics (Weeks 5-6)
- Implement performance monitoring system
- Build quality assurance dashboard
- Create reporting and analytics interface
- Set up automated alerts and notifications

### Phase 4: Integration and Testing (Weeks 7-8)
- Integrate with PCPM and provider workflows
- User acceptance testing with PCCMs
- Performance optimization and security audit
- Training material development and deployment

---

## Success Metrics

### 9.1 Assignment Efficiency Metrics
- **Assignment Speed:** <4 hours from handoff to assignment
- **Assignment Accuracy:** >95% appropriate assignments
- **Workload Balance:** <15% variance in coordinator utilization
- **Patient Satisfaction:** >4.5/5 with assigned coordinator

### 9.2 Team Performance Metrics
- **Team Utilization:** 75-85% optimal range
- **Quality Scores:** >95% documentation accuracy
- **Response Time:** <2 hours average coordinator response
- **Retention Rate:** >90% coordinator retention

### 9.3 Business Impact Metrics
- **Assignment Efficiency:** 60% reduction in assignment time
- **Quality Improvement:** 20% improvement in care outcomes
- **Cost Optimization:** 15% reduction in coordinator overtime
- **Scalability:** Support 2x patient volume with current team

---

## Conclusion

The PCCM workflow design provides a comprehensive solution for managing both direct patient care coordination and team oversight responsibilities. By extending the standard coordinator workflow with specialized management capabilities, PCCMs can efficiently handle coordinator assignments while maintaining their clinical coordination duties.

The three-tab interface ensures seamless integration between coordinator and manager functions, while automated assignment algorithms optimize team utilization and patient care quality. The design emphasizes efficiency, quality assurance, and team performance while maintaining compliance with healthcare regulations.

The system supports scalable team management, data-driven decision making, and continuous quality improvement, positioning the organization for sustainable growth and enhanced patient care outcomes.

---

**Next Steps:**
1. Review and approve PCCM workflow design
2. Begin Phase 1 implementation
3. Coordinate with PCPM workflow integration
4. Plan team training and change management
5. Establish success metrics tracking and quality assurance processes