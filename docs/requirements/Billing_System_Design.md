# Billing System Design and Reporting

**Last Updated:** January 17, 2025  
**Author:** System Analyst  
**Status:** Comprehensive Billing Analysis

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Billing Code Structure](#billing-code-structure)
3. [Automated Billing Assignment](#automated-billing-assignment)
4. [Database Schema for Billing](#database-schema-for-billing)
5. [Billing Reports and Analytics](#billing-reports-and-analytics)
6. [Admin Dashboard Design](#admin-dashboard-design)
7. [Integration with Provider Workflow](#integration-with-provider-workflow)

## Executive Summary

The billing system operates as a completely separate module from the provider workflow, automatically processing service records and generating billing codes based on predefined rules. This separation ensures providers focus on patient care while maintaining accurate billing and compliance.

### Key Features:
- **2,218 different task/billing combinations** automatically managed
- **Real-time billing code assignment** based on service type, location, patient type, and time
- **Comprehensive reporting** for financial analysis and compliance
- **Admin-only access** with complete audit trails
- **Integration with existing EHR and practice management systems**

## Billing Code Structure

### Primary Care Provider (PCP) Visits

#### Home Visits (HO)
**New Patients:**
- 10-19 mins: 99341
- 20-29 mins: 99341
- 30-39 mins: 99342
- 40-49 mins: 99342
- 50-59 mins: 99344
- 60-69 mins: 99344
- 70-79 mins: 99345
- 80-89 mins: 99345
- 90-99 mins: 99345 + G0318x1
- 100-109 mins: 99345 + G0318x1
- 110-119 mins: 99345 + G0318x2
- 120-129 mins: 99345 + G0318x3

**Established Patients:**
- 10-19 mins: 99347
- 20-39 mins: 99348
- 40-59 mins: 99349
- 60-79 mins: 99350
- 80-89 mins: 99350 + G0318x1
- 90-99 mins: 99350 + G0318x1
- 100-109 mins: 99350 + G0318x2
- 110-119 mins: 99350 + G0318x2
- 120-129 mins: 99350 + G0318x3

#### Telehealth Visits
**New Patients:**
- 15-29 mins: 99421
- 30-44 mins: 99422
- 45+ mins: 99423

**Established Patients:**
- 15-29 mins: 99421
- 30-44 mins: 99422
- 45+ mins: 99423

#### Office Visits
**New Patients:**
- 15-29 mins: 99201
- 30-44 mins: 99202
- 45-59 mins: 99203
- 60-74 mins: 99204
- 75+ mins: 99205

**Established Patients:**
- 10-19 mins: 99211
- 20-29 mins: 99212
- 30-39 mins: 99213
- 40-54 mins: 99214
- 55+ mins: 99215

### Care Coordination Tasks

#### Communication Tasks
- **Communication-Call Patient**: 99441, 99442, 99443 (time-based)
- **Communication-Call Family**: 99441, 99442, 99443 (time-based)
- **Communication-Call Provider**: 99441, 99442, 99443 (time-based)
- **Communication-Email**: 99421, 99422, 99423 (complexity-based)

#### Care Coordination
- **Care Coordination-Referral**: 99490, 99491, 99495, 99496
- **Care Coordination-Follow-up**: 99490, 99491, 99495, 99496
- **Care Coordination-Scheduling**: 99490, 99491, 99495, 99496

#### Chronic Care Management (CCM)
- **CCM-Assessment**: 99490, 99491
- **CCM-Care Plan**: 99490, 99491
- **CCM-Medication Review**: 99490, 99491

#### Principal Care Management (PCM)
- **PCM-Complex Care**: 99495, 99496
- **PCM-Care Transitions**: 99495, 99496

## Automated Billing Assignment

### Assignment Logic
```javascript
function assignBillingCodeAutomatically(serviceRecord) {
    const {
        serviceType,
        location,
        patientType,
        minutesSpent,
        patientComplexity
    } = serviceRecord;
    
    // Lookup billing code based on parameters
    const codeQuery = {
        service_type: serviceType,
        location_type: location,
        patient_type: patientType,
        min_minutes: { $lte: minutesSpent },
        max_minutes: { $gte: minutesSpent }
    };
    
    const billingCode = TaskBillingCodes.findOne(codeQuery);
    
    // Calculate billing amount
    const billingAmount = calculateBillingAmount(billingCode, minutesSpent, patientComplexity);
    
    // Create billing record
    const billingRecord = {
        psl_id: serviceRecord.psl_id,
        primary_cpt_code: billingCode.primary_cpt_code,
        additional_codes: billingCode.additional_codes,
        billing_amount: billingAmount,
        auto_assigned_timestamp: new Date(),
        billing_status: 'ready_to_bill'
    };
    
    // Save to billing database
    ProviderServiceBilling.create(billingRecord);
    
    // Create audit log
    BillingAuditLog.create({
        action: 'auto_billing_assignment',
        psl_id: serviceRecord.psl_id,
        assigned_code: billingCode.primary_cpt_code,
        calculated_amount: billingAmount,
        assignment_rules_used: codeQuery
    });
    
    return billingRecord;
}
```

### Billing Rate Calculation
```javascript
function calculateBillingAmount(billingCode, minutes, complexity) {
    let baseRate = billingCode.base_rate;
    
    // Time-based adjustments
    if (minutes > billingCode.standard_minutes) {
        const extraMinutes = minutes - billingCode.standard_minutes;
        baseRate += (extraMinutes * billingCode.per_minute_rate);
    }
    
    // Complexity adjustments
    if (complexity === 'high') {
        baseRate *= 1.2; // 20% increase for high complexity
    } else if (complexity === 'low') {
        baseRate *= 0.9; // 10% decrease for low complexity
    }
    
    return Math.round(baseRate * 100) / 100; // Round to 2 decimal places
}
```

## Database Schema for Billing

### Billing Tables

#### `provider_service_billing`
```sql
CREATE TABLE provider_service_billing (
    billing_id INT PRIMARY KEY AUTO_INCREMENT,
    psl_id INT NOT NULL,
    primary_cpt_code VARCHAR(10) NOT NULL,
    additional_codes JSON,
    billing_amount DECIMAL(10,2) NOT NULL,
    paid_by_patient BOOLEAN DEFAULT FALSE,
    billing_status ENUM('ready_to_bill', 'billed', 'paid', 'denied', 'skip') DEFAULT 'ready_to_bill',
    claim_number VARCHAR(50),
    date_billed DATE,
    billed_amount DECIMAL(10,2),
    payment_received DECIMAL(10,2),
    payment_date DATE,
    denial_reason TEXT,
    auto_assigned_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    admin_reviewed BOOLEAN DEFAULT FALSE,
    admin_notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (psl_id) REFERENCES provider_service_log(psl_id)
);
```

#### `task_billing_codes`
```sql
CREATE TABLE task_billing_codes (
    code_id INT PRIMARY KEY AUTO_INCREMENT,
    task_description TEXT NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    location_type ENUM('home', 'telehealth', 'office', 'facility') NOT NULL,
    patient_type ENUM('new', 'established') NOT NULL,
    min_minutes INT NOT NULL,
    max_minutes INT NOT NULL,
    primary_cpt_code VARCHAR(10) NOT NULL,
    additional_codes JSON,
    base_rate DECIMAL(10,2) NOT NULL,
    per_minute_rate DECIMAL(10,2) DEFAULT 0.00,
    standard_minutes INT NOT NULL,
    complexity_multiplier DECIMAL(3,2) DEFAULT 1.00,
    effective_date DATE NOT NULL,
    expiration_date DATE,
    active_status BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### `billing_audit_log`
```sql
CREATE TABLE billing_audit_log (
    audit_id INT PRIMARY KEY AUTO_INCREMENT,
    action VARCHAR(100) NOT NULL,
    psl_id INT,
    billing_id INT,
    user_id INT,
    assigned_code VARCHAR(10),
    calculated_amount DECIMAL(10,2),
    assignment_rules_used JSON,
    previous_values JSON,
    new_values JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);
```

## Billing Reports and Analytics

### Standard Reports

#### 1. Daily Billing Summary
- Total services provided
- Total billing amount generated
- Breakdown by service type
- Provider productivity metrics
- Pending billing items

#### 2. Monthly Financial Report
- Revenue by provider
- Revenue by service type
- Payment collection rates
- Outstanding claims
- Denial analysis

#### 3. Provider Performance Report
- Services per provider
- Average billing per service
- Time efficiency metrics
- Patient complexity distribution

#### 4. Compliance Report
- Billing code accuracy
- Documentation completeness
- Audit trail verification
- Regulatory compliance metrics

### Report Generation Queries

#### Daily Billing Summary
```sql
SELECT 
    DATE(psl.service_date) as service_date,
    COUNT(psl.psl_id) as total_services,
    SUM(psb.billing_amount) as total_billing,
    AVG(psb.billing_amount) as avg_billing_per_service,
    COUNT(CASE WHEN psb.billing_status = 'ready_to_bill' THEN 1 END) as pending_billing
FROM provider_service_log psl
JOIN provider_service_billing psb ON psl.psl_id = psb.psl_id
WHERE psl.service_date = CURDATE()
GROUP BY DATE(psl.service_date);
```

#### Provider Performance
```sql
SELECT 
    p.provider_name,
    COUNT(psl.psl_id) as total_services,
    SUM(psl.minutes_spent) as total_minutes,
    AVG(psl.minutes_spent) as avg_minutes_per_service,
    SUM(psb.billing_amount) as total_revenue,
    AVG(psb.billing_amount) as avg_revenue_per_service
FROM providers p
JOIN provider_service_log psl ON p.provider_id = psl.provider_id
JOIN provider_service_billing psb ON psl.psl_id = psb.psl_id
WHERE psl.service_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY p.provider_id, p.provider_name
ORDER BY total_revenue DESC;
```

## Admin Dashboard Design

### Billing Dashboard Layout
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Billing Administration Dashboard                                    [Admin] │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │   Today's       │ │   Pending       │ │   Monthly       │ │   Collection    │ │
│ │   Revenue       │ │   Claims        │ │   Target        │ │   Rate          │ │
│ │   $12,450       │ │      23         │ │   $285,000      │ │     94.2%       │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ Recent Billing Activity                                    [View All] [Export] │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🟢 Smith, John - Home Visit (99350) - $150.00 - Ready to Bill         │ │
│ │ 🟡 Johnson, Mary - CCM Review (99490) - $75.00 - Pending Review       │ │
│ │ 🔴 Williams, Bob - Telehealth (99422) - $85.00 - Claim Denied         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ Quick Actions                                                               │
│ [Generate Daily Report] [Review Pending Claims] [Update Billing Codes]     │
│ [Export for 1099] [Audit Trail] [Provider Performance]                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Billing Code Management Interface
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Billing Code Management                                           [Add New] │
├─────────────────────────────────────────────────────────────────────────────┤
│ Search: [Home Visit] [Filter: Active ▼] [Sort: Code ▼]                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Code    │ Description           │ Type │ Minutes │ Rate    │ Status │ Actions │
│ 99350   │ Home Visit Est.      │ Home │ 60-79   │ $150.00 │ Active │ [Edit]  │
│ 99349   │ Home Visit Est.      │ Home │ 40-59   │ $125.00 │ Active │ [Edit]  │
│ 99490   │ CCM Care Plan        │ CCM  │ 20+     │ $75.00  │ Active │ [Edit]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Integration with Provider Workflow

### Data Flow
1. **Provider enters service data** in Provider Workflow system
2. **Service record saved** to `provider_service_log` table
3. **Billing system triggered** automatically via database trigger or API
4. **Billing code assigned** based on service type, location, patient type, and time
5. **Billing record created** in `provider_service_billing` table
6. **Audit log updated** with assignment details
7. **Admin notified** of any billing exceptions or manual review requirements

### API Integration Points
```javascript
// Provider Workflow → Billing System
POST /api/billing/process-service
{
    "psl_id": 12345,
    "service_type": "home_visit",
    "location": "home",
    "patient_type": "established",
    "minutes_spent": 65,
    "complexity": "standard"
}

// Response
{
    "billing_id": 67890,
    "assigned_code": "99350",
    "billing_amount": 150.00,
    "status": "ready_to_bill",
    "auto_assigned": true
}
```

### Error Handling
- **Missing billing codes**: Alert admin for manual assignment
- **Unusual time patterns**: Flag for review
- **Complex cases**: Route to billing specialist
- **System errors**: Maintain service record, retry billing assignment

---

*This billing system operates independently from the provider workflow while maintaining seamless integration for accurate financial management and reporting.*