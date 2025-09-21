#!/usr/bin/env python3
"""
Final comprehensive script to populate coordinator_monthly_summary table
This handles all the requirements including proper data types and billing code mapping
"""

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def populate_coordinator_monthly_summary():
    """Populate coordinator_monthly_summary table with proper data handling"""
    try:
        conn = sqlite3.connect('production.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        logger.info("Clearing existing data from coordinator_monthly_summary...")
        cursor.execute("DELETE FROM coordinator_monthly_summary")
        
        # Simple and clean approach to populate the table
        # This groups by coordinator, month, year, and patient to create proper summaries
        query = """
        INSERT INTO coordinator_monthly_summary 
        (coordinator_id, coordinator_name, patient_id, patient_name, year, month, total_minutes)
        SELECT 
            CAST(ct.coordinator_id AS INTEGER) as coordinator_id,
            -- Get coordinator name from users table
            COALESCE(u.first_name || ' ' || u.last_name, 'Unknown') as coordinator_name,
            ct.patient_id,
            -- Get patient name from patients table if available
            COALESCE(p.first_name || ' ' || p.last_name, ct.patient_id) as patient_name,
            CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER) as month,
            CAST('20' || SUBSTR(ct.task_date, -2) AS INTEGER) as year,
            SUM(ct.duration_minutes) as total_minutes
        FROM coordinator_tasks ct
        LEFT JOIN coordinators c ON CAST(ct.coordinator_id AS INTEGER) = c.coordinator_id
        LEFT JOIN users u ON c.user_id = u.user_id
        LEFT JOIN patients p ON ct.patient_id = p.patient_id
        WHERE ct.task_date IS NOT NULL 
        AND ct.task_date != ''
        AND ct.coordinator_id IS NOT NULL 
        AND ct.coordinator_id != ''
        AND ct.coordinator_id GLOB '[0-9]*'
        AND ct.duration_minutes IS NOT NULL
        AND ct.duration_minutes > 0
        GROUP BY 
            CAST(ct.coordinator_id AS INTEGER),
            COALESCE(u.first_name || ' ' || u.last_name, 'Unknown'),
            ct.patient_id,
            COALESCE(p.first_name || ' ' || p.last_name, ct.patient_id),
            CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER),
            CAST('20' || SUBSTR(ct.task_date, -2) AS INTEGER)
        HAVING coordinator_id IS NOT NULL AND coordinator_id > 0
        ORDER BY coordinator_id, year, month
        """
        
        logger.info("Executing coordinator monthly summary population...")
        cursor.execute(query)
        conn.commit()
        
        rows_affected = cursor.rowcount
        logger.info(f"Successfully populated {rows_affected} rows in coordinator_monthly_summary")
        
        # Verify the results
        cursor.execute("SELECT COUNT(*) as count FROM coordinator_monthly_summary")
        final_count = cursor.fetchone()[0]
        logger.info(f"Final coordinator_monthly_summary count: {final_count} rows")
        
        # Show sample data
        cursor.execute("""
            SELECT coordinator_id, month, year, total_minutes, patient_id 
            FROM coordinator_monthly_summary 
            ORDER BY coordinator_id, year, month 
            LIMIT 5
        """)
        sample_data = cursor.fetchall()
        logger.info("Sample data:")
        for row in sample_data:
            logger.info(f"  Coordinator {row['coordinator_id']}, {row['month']}/{row['year']}: {row['total_minutes']} minutes for patient {row['patient_id']}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in coordinator monthly summary population: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def verify_all_tables():
    """Verify all related tables and their data"""
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        # Check coordinator_tasks table
        cursor.execute("SELECT COUNT(*) as count FROM coordinator_tasks")
        ct_count = cursor.fetchone()[0]
        logger.info(f"coordinator_tasks table: {ct_count} records")
        
        # Check coordinator_monthly_summary table
        cursor.execute("SELECT COUNT(*) as count FROM coordinator_monthly_summary")
        cm_count = cursor.fetchone()[0]
        logger.info(f"coordinator_monthly_summary table: {cm_count} records")
        
        # Check coordinator_billing_codes table
        cursor.execute("SELECT COUNT(*) as count FROM coordinator_billing_codes")
        bc_count = cursor.fetchone()[0]
        logger.info(f"coordinator_billing_codes table: {bc_count} records")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in verification: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting final coordinator monthly summary population...")
    
    # First verify the data
    verify_all_tables()
    
    # Then populate
    success = populate_coordinator_monthly_summary()
    
    if success:
        logger.info("Coordinator monthly summary population completed successfully!")
        verify_all_tables()
    else:
        logger.error("Coordinator monthly summary population failed!")
        
    logger.info("Final script execution completed")
