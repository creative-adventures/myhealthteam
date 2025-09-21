-- Clear existing data
DELETE FROM coordinator_tasks;

-- Insert data with proper derivations
INSERT INTO coordinator_tasks (
    patient_id,
    coordinator_id,
    task_date,
    duration_minutes,
    task_type,
    notes
)
SELECT 
    COALESCE(p.patient_id, sch."Pt Name") as patient_id,
    COALESCE(c.coordinator_id, sch."Staff") as coordinator_id,
    sch."Date Only" as task_date,
    sch."Mins B" as duration_minutes,
    sch."Type" as task_type,
    sch."Notes" as notes
FROM "SOURCE_COORDINATOR_TASKS_HISTORY" sch
LEFT JOIN patients p ON TRIM(UPPER(sch."Pt Name")) = TRIM(UPPER(p.last_first_dob))
LEFT JOIN staff_code_mapping scm ON sch."Staff" = scm.staff_code
LEFT JOIN coordinators c ON scm.user_id = c.user_id
WHERE sch."Pt Name" IS NOT NULL 
    AND sch."Pt Name" != ''
    AND sch."Staff" IS NOT NULL 
    AND sch."Staff" != ''
    AND sch."Date Only" IS NOT NULL 
    AND sch."Date Only" != ''
    AND sch."Mins B" IS NOT NULL;
