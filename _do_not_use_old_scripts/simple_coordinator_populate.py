#!/usr/bin/env python3
"""
Simple and direct approach to populate coordinator summary table
"""

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def populate_coordinator_summary_simple():
    """Simple approach to populate dashboard_coordinator_monthly_summary"""
    try:
        conn = sqlite3.connect('production.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        logger.info("Clearing existing data from dashboard_coordinator_monthly_summary...")
        cursor.execute("DELETE FROM dashboard_coordinator_monthly_summary")
        
        # Simple approach - manually parse the date format "01/01/22"
        # and handle the data conversion properly
        query = """
        INSERT INTO dashboard_coordinator_monthly_summary 
        (coordinator_id, month, year, total_minutes, total_minutes_per_patient, 
         total_tasks_completed, average_daily_tasks)
        SELECT 
            CAST(ct.coordinator_id AS INTEGER) as coordinator_id,
            CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER) as month,
            CAST('20' || SUBSTR(ct.task_date, -2) AS INTEGER) as year,
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
        AND ct.coordinator_id GLOB '[0-9]*'
        AND ct.duration_minutes IS NOT NULL
        AND ct.duration_minutes > 0
        GROUP BY 
            CAST(ct.coordinator_id AS INTEGER),
            CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER),
            CAST('20' || SUBSTR(ct.task_date, -2) AS INTEGER)
        HAVING coordinator_id IS NOT NULL AND coordinator_id > 0
        """
        
        logger.info("Executing simple population query...")
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
        logger.error(f"Error in simple populate: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def test_date_parsing():
    """Test the date parsing logic"""
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        # Test our date parsing logic
        test_query = """
        SELECT 
            task_date,
            SUBSTR(task_date, 1, INSTR(task_date, '/') - 1) as month_part,
            SUBSTR(task_date, -2) as year_part,
            '20' || SUBSTR(task_date, -2) as full_year,
            CAST(SUBSTR(task_date, 1, INSTR(task_date, '/') - 1) AS INTEGER) as parsed_month,
            CAST('20' || SUBSTR(task_date, -2) AS INTEGER) as parsed_year
        FROM coordinator_tasks 
        WHERE task_date IS NOT NULL AND task_date != ''
        LIMIT 5
        """
        
        cursor.execute(test_query)
        results = cursor.fetchall()
        logger.info("Date parsing test results:")
        for row in results:
            logger.info(f"  {row}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in date parsing test: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting simple coordinator summary population...")
    
    # First test the date parsing
    test_date_parsing()
    
    # Then populate
    success = populate_coordinator_summary_simple()
    
    if success:
        logger.info("Simple coordinator summary population completed successfully!")
    else:
        logger.error("Simple coordinator summary population failed!")
        
    logger.info("Simple script execution completed")
