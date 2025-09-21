# Database Schema Summary

## Overview
This document provides a comprehensive overview of the database schema and how it's used across different dashboards to optimize performance through summary tables.

## Core Tables

### User Management
- **users**: Main user information
- **roles**: Available roles in the system
- **user_roles**: Junction table for user-role relationships
- **providers**: Provider-specific user information
- **coordinators**: Coordinator-specific user information

### Patient Management
- **patients**: Patient information
- **regions**: Geographic regions
- **patient_assignments**: Patient-provider-coordinator assignments
- **user_patient_assignments**: User-patient assignment relationships

### Task Management
- **tasks**: Task information
- **provider_tasks**: Provider-specific tasks
- **coordinator_tasks**: Coordinator-specific tasks
- **daily_tasks**: Daily task entries

## Summary Tables for Enhanced Performance

### 1. provider_region_summary
**Purpose**: Pre-aggregated region-provider relationships
**Used by**: Care Provider Dashboard for region-based filtering
**Fields**: 
- provider_id, region_id, region_name, zip_code, city, state, patient_count

### 2. provider_zip_summary
**Purpose**: Pre-aggregated zip code-provider relationships
**Used by**: Care Provider Dashboard for zip code filtering
**Fields**: 
- provider_id, zip_code, city, state, patient_count, region_count

### 3. patient_region_mapping
**Purpose**: Direct patient-region relationships
**Used by**: Care Provider Dashboard for region-based patient filtering
**Fields**: 
- patient_id, region_id, region_name, zip_code, city, state

### 4. provider_performance_summary
**Purpose**: Aggregated performance metrics for providers
**Used by**: Admin Dashboard, Care Provider Manager Dashboard
**Fields**: 
- provider_id, month, year, total_tasks_completed, total_time_spent_minutes, average_task_completion_time_minutes

### 5. coordinator_performance_summary
**Purpose**: Aggregated performance metrics for coordinators
**Used by**: Admin Dashboard, Coordinator Manager Dashboard
**Fields**: 
- coordinator_id, month, year, total_tasks_completed, total_time_spent_minutes, average_task_completion_time_minutes

### 6. patient_assignment_summary
**Purpose**: Pre-aggregated patient assignment information
**Used by**: Care Coordinator Dashboard
**Fields**: 
- user_id, patient_id, assignment_date, assignment_type, status

### 7. task_summary
**Purpose**: Pre-aggregated task information for reporting
**Used by**: Various dashboards requiring task data
**Fields**: 
- task_id, provider_id, coordinator_id, patient_id, task_date, duration_minutes, billing_code, status

### 8. region_patient_assignment_summary
**Purpose**: Pre-aggregated region-patient relationships
**Used by**: Administrative dashboards requiring region-based patient views
**Fields**: 
- region_id, patient_id, patient_name, patient_status

## Dashboard Usage Patterns

### Admin Dashboard
- Uses provider_performance_summary and coordinator_performance_summary
- Calls get_coordinator_performance_metrics() and get_provider_performance_metrics()

### Care Coordinator Dashboard
- Uses patient_assignment_summary for patient assignments
- Uses get_user_patient_assignments() and get_patient_details_by_id()

### Care Provider Dashboard
- Uses provider_region_summary, provider_zip_summary, and patient_region_mapping
- Uses complex queries with summary tables for filtering and performance
- Uses get_tasks_billing_codes() for task type dropdowns

## Indexes for Performance
All summary tables have appropriate indexes to optimize query performance:
- Primary indexes on foreign keys
- Composite indexes for common query patterns
- Performance-optimized index names

## Implementation Notes
1. Summary tables should be maintained through triggers or scheduled updates
2. Data in summary tables should be kept synchronized with base tables
3. Regular maintenance is required to ensure data accuracy
4. These tables significantly improve dashboard loading times by reducing complex JOIN operations
