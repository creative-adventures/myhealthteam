#!/usr/bin/env python3
"""
Final script to populate dashboard_coordinator_monthly_summary table
This directly handles the data type conversion issue between coordinator_tasks and dashboard summary
"""

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def populate_coordinator_summary():
    """Populate the dashboard_coordinator_monthly_summary table"""
    try:
        conn = sqlite3.connect('production.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        logger.info("Clearing existing data from dashboard_coordinator_monthly_summary...")
        cursor.execute("DELETE FROM dashboard_coordinator_monthly_summary")
        
        # Direct SQL approach to populate the table
        # This handles the coordinator_id conversion properly
        query = """
        INSERT INTO dashboard_coordinator_monthly_summary 
        (coordinator_id, month, year, total_minutes, total_minutes_per_patient, 
         total_tasks_completed, average_daily_tasks)
        SELECT 
            CAST(ct.coordinator_id AS INTEGER) as coordinator_id,
            CAST(strftime('%m', ct.task_date) AS INTEGER) as month,
            CAST(strftime('%Y', ct.task_date) AS INTEGER) as year,
            SUM(ct.duration_minutes) as total_minutes,
            CASE 
                WHEN COUNT(DISTINCT ct.patient_id) > 0 
                THEN SUM(ct.duration_minutes) * 1.0 / COUNT(DISTINCT ct.patient_id) 
                ELSE 0 
            END as total_minutes_per_patient,
            COUNT(*) as total_tasks_completed,
            COUNT(*) * 1.0 / 30.0 as average_daily_tasks
        FROM coordinator_tasks ct
        WHERE ct.task_date IS NOT NULL 
        AND ct.task_date != ''
        AND ct.coordinator_id IS NOT NULL 
        AND ct.coordinator_id != ''
        AND ct.coordinator_id GLOB '[0-9]*'  -- Only numeric coordinator_ids
        AND ct.duration_minutes IS NOT NULL
        AND ct.duration_minutes > 0
        GROUP BY 
            CAST(ct.coordinator_id AS INTEGER),
            CAST(strftime('%m', ct.task_date) AS INTEGER),
            CAST(strftime('%Y', ct.task_date) AS INTEGER)
        HAVING coordinator_id IS NOT NULL AND coordinator_id > 0
        """
        
        logger.info("Executing population query...")
        cursor.execute(query)
        conn.commit()
        
        rows_affected = cursor.rowcount
        logger.info(f"Successfully populated {rows_affected} rows in dashboard_coordinator_monthly_summary")
        
        # Verify the results
        cursor.execute("SELECT COUNT(*) as count FROM dashboard_coordinator_monthly_summary")
        final_count = cursor.fetchone()[0]
        logger.info(f"Final table count: {final_count} rows")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error populating coordinator summary: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def verify_data():
    """Verify what data we have in the tables"""
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        # Check sample data from coordinator_tasks
        cursor.execute("""
            SELECT coordinator_id, task_date, duration_minutes 
            FROM coordinator_tasks 
            WHERE coordinator_id IS NOT NULL AND coordinator_id != '' 
            AND task_date IS NOT NULL AND task_date != ''
            AND duration_minutes IS NOT NULL AND duration_minutes > 0
            LIMIT 3
        """)
        sample_data = cursor.fetchall()
        logger.info("Sample coordinator_tasks data:")
        for row in sample_data:
            logger.info(f"  coordinator_id='{row[0]}', task_date='{row[1]}', duration_minutes={row[2]}")
        
        # Check what we have in the summary table
        cursor.execute("SELECT COUNT(*) as count FROM dashboard_coordinator_monthly_summary")
        summary_count = cursor.fetchone()[0]
        logger.info(f"dashboard_coordinator_monthly_summary has {summary_count} rows")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in verify_data: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting final coordinator summary population...")
    
    # First verify the data
    verify_data()
    
    # Then populate
    success = populate_coordinator_summary()
    
    if success:
        logger.info("Coordinator summary population completed successfully!")
        verify_data()
    else:
        logger.error("Coordinator summary population failed!")
        
    logger.info("Final script execution completed")
