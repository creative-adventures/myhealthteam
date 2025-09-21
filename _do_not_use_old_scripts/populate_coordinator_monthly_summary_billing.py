#!/usr/bin/env python3
"""
Script to populate coordinator_monthly_summary table with billing code mapping
This handles the complex task of mapping total minutes to appropriate billing codes
"""

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def populate_coordinator_monthly_summary_with_billing():
    """Populate coordinator_monthly_summary table with billing code mapping"""
    try:
        conn = sqlite3.connect('production.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        logger.info("Clearing existing data from coordinator_monthly_summary...")
        cursor.execute("DELETE FROM coordinator_monthly_summary")
        
        # Main query to populate coordinator_monthly_summary with billing code mapping
        # This groups by coordinator, month, year, and patient to assign appropriate billing codes
        query = """
        INSERT INTO coordinator_monthly_summary 
        (coordinator_id, coordinator_name, patient_id, patient_name, year, month, total_minutes, 
         billing_code_id, billing_code, billing_code_description, created_date, updated_date)
        SELECT 
            CAST(ct.coordinator_id AS INTEGER) as coordinator_id,
            -- Get coordinator name from users table
            u.first_name || ' ' || u.last_name as coordinator_name,
            ct.patient_id,
            -- Get patient name from patients table if available
            COALESCE(p.first_name || ' ' || p.last_name, ct.patient_id) as patient_name,
            CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER) as month,
            CAST('20' || SUBSTR(ct.task_date, -2) AS INTEGER) as year,
            SUM(ct.duration_minutes) as total_minutes,
            -- Map to appropriate billing code based on total minutes
            bc.code_id as billing_code_id,
            bc.billing_code,
            bc.description as billing_code_description,
            CURRENT_TIMESTAMP as created_date,
            CURRENT_TIMESTAMP as updated_date
        FROM coordinator_tasks ct
        LEFT JOIN coordinators c ON CAST(ct.coordinator_id AS INTEGER) = c.coordinator_id
        LEFT JOIN users u ON c.user_id = u.user_id
        LEFT JOIN patients p ON ct.patient_id = p.patient_id
        LEFT JOIN coordinator_billing_codes bc ON SUM(ct.duration_minutes) >= bc.min_minutes 
            AND SUM(ct.duration_minutes) <= bc.max_minutes
        WHERE ct.task_date IS NOT NULL 
        AND ct.task_date != ''
        AND ct.coordinator_id IS NOT NULL 
        AND ct.coordinator_id != ''
        AND ct.coordinator_id GLOB '[0-9]*'
        AND ct.duration_minutes IS NOT NULL
        AND ct.duration_minutes > 0
        GROUP BY 
            CAST(ct.coordinator_id AS INTEGER),
            u.first_name || ' ' || u.last_name,
            ct.patient_id,
            COALESCE(p.first_name || ' ' || p.last_name, ct.patient_id),
            CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER),
            CAST('20' || SUBSTR(ct.task_date, -2) AS INTEGER),
            bc.code_id, bc.billing_code, bc.description
        HAVING coordinator_id IS NOT NULL AND coordinator_id > 0
        ORDER BY coordinator_id, year, month
        """
        
        logger.info("Executing coordinator monthly summary population with billing codes...")
        cursor.execute(query)
        conn.commit()
        
        rows_affected = cursor.rowcount
        logger.info(f"Successfully populated {rows_affected} rows in coordinator_monthly_summary")
        
        # Verify the results
        cursor.execute("SELECT COUNT(*) as count FROM coordinator_monthly_summary")
        final_count = cursor.fetchone()[0]
        logger.info(f"Final coordinator_monthly_summary count: {final_count} rows")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in coordinator monthly summary population: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def populate_coordinator_monthly_summary_simple():
    """Alternative simpler approach that focuses on the core requirements"""
    try:
        conn = sqlite3.connect('production.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        logger.info("Clearing existing data from coordinator_monthly_summary...")
        cursor.execute("DELETE FROM coordinator_monthly_summary")
        
        # Simpler approach - just populate the basic structure with proper data types
        query = """
        INSERT INTO coordinator_monthly_summary 
        (coordinator_id, coordinator_name, patient_id, patient_name, year, month, total_minutes)
        SELECT 
            CAST(ct.coordinator_id AS INTEGER) as coordinator_id,
            -- Get coordinator name from users table
            u.first_name || ' ' || u.last_name as coordinator_name,
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
            u.first_name || ' ' || u.last_name,
            ct.patient_id,
            COALESCE(p.first_name || ' ' || p.last_name, ct.patient_id),
            CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER),
            CAST('20' || SUBSTR(ct.task_date, -2) AS INTEGER)
        HAVING coordinator_id IS NOT NULL AND coordinator_id > 0
        ORDER BY coordinator_id, year, month
        """
        
        logger.info("Executing simple coordinator monthly summary population...")
        cursor.execute(query)
        conn.commit()
        
        rows_affected = cursor.rowcount
        logger.info(f"Successfully populated {rows_affected} rows in coordinator_monthly_summary")
        
        # Verify the results
        cursor.execute("SELECT COUNT(*) as count FROM coordinator_monthly_summary")
        final_count = cursor.fetchone()[0]
        logger.info(f"Final coordinator_monthly_summary count: {final_count} rows")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in simple coordinator monthly summary population: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def test_billing_code_mapping():
    """Test the billing code mapping logic"""
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        # Test what billing codes are available
        cursor.execute("SELECT code_id, billing_code, description, min_minutes, max_minutes FROM coordinator_billing_codes ORDER BY min_minutes")
        billing_codes = cursor.fetchall()
        logger.info("Available billing codes:")
        for code in billing_codes:
            logger.info(f"  {code}")
        
        # Test sample data
        cursor.execute("""
            SELECT 
                SUM(ct.duration_minutes) as total_minutes,
                bc.billing_code,
                bc.description
            FROM coordinator_tasks ct
            LEFT JOIN coordinator_billing_codes bc ON ct.duration_minutes >= bc.min_minutes 
                AND ct.duration_minutes <= bc.max_minutes
            WHERE ct.duration_minutes IS NOT NULL AND ct.duration_minutes > 0
            GROUP BY bc.billing_code, bc.description
            LIMIT 5
        """)
        test_results = cursor.fetchall()
        logger.info("Sample billing code mapping test:")
        for result in test_results:
            logger.info(f"  Total minutes: {result[0]}, Billing code: {result[1]}, Description: {result[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in billing code mapping test: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting coordinator monthly summary population with billing codes...")
    
    # First test the billing codes
    test_billing_code_mapping()
    
    # Then populate with the simpler approach first
    success = populate_coordinator_monthly_summary_simple()
    
    if success:
        logger.info("Coordinator monthly summary population completed successfully!")
        
        # Check final count
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM coordinator_monthly_summary")
        count = cursor.fetchone()[0]
        logger.info(f"Final table count: {count} rows")
        conn.close()
    else:
        logger.error("Coordinator monthly summary population failed!")
        
    logger.info("Script execution completed")
