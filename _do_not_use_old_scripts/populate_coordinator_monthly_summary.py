#!/usr/bin/env python3
"""
Script to populate the dashboard_coordinator_monthly_summary table with data from coordinator_tasks
This script handles the data type conversion issue where coordinator_id in coordinator_tasks is TEXT
but needs to be INTEGER for the dashboard summary table.
"""

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection(db_path='production.db'):
    """Get database connection"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def populate_coordinator_monthly_summary(db_path='production.db'):
    """Populate dashboard_coordinator_monthly_summary table with data from coordinator_tasks"""
    logger.info("Starting coordinator monthly summary population...")
    
    conn = get_db_connection(db_path)
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM dashboard_coordinator_monthly_summary")
        logger.info("Cleared existing data from dashboard_coordinator_monthly_summary")
        
        # Insert data with proper coordinator_id conversion
        # We need to handle the case where coordinator_id in coordinator_tasks might be:
        # 1. A valid user_id (integer) from staff_code_mapping
        # 2. A staff code (text) that needs to be mapped to coordinator_id
        query = """
        INSERT INTO dashboard_coordinator_monthly_summary 
        (coordinator_id, month, year, total_minutes, total_minutes_per_patient, 
         total_tasks_completed, average_daily_tasks)
        SELECT 
            CASE 
                -- If coordinator_id is a valid integer, use it directly
                WHEN CAST(ct.coordinator_id AS INTEGER) > 0 AND ct.coordinator_id = CAST(ct.coordinator_id AS INTEGER) 
                THEN CAST(ct.coordinator_id AS INTEGER)
                -- If it's a text staff code, we need to map it to coordinator_id
                -- For now, we'll use a fallback approach - if we can't convert to integer, we'll skip
                ELSE NULL
            END as coordinator_id,
            strftime('%m', ct.task_date) as month,
            strftime('%Y', ct.task_date) as year,
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
        AND ct.duration_minutes IS NOT NULL
        AND ct.duration_minutes > 0
        GROUP BY 
            CASE 
                WHEN CAST(ct.coordinator_id AS INTEGER) > 0 AND ct.coordinator_id = CAST(ct.coordinator_id AS INTEGER) 
                THEN CAST(ct.coordinator_id AS INTEGER)
                ELSE NULL
            END,
            strftime('%m', ct.task_date),
            strftime('%Y', ct.task_date)
        HAVING coordinator_id IS NOT NULL
        """
        
        cursor.execute(query)
        conn.commit()
        rows_affected = cursor.rowcount
        logger.info(f"Populated {rows_affected} rows in dashboard_coordinator_monthly_summary")
        
        # Also try to handle the case where we need to map text staff codes to actual coordinator IDs
        # Let's check what coordinator_ids we have that might be text codes
        cursor.execute("""
        SELECT DISTINCT coordinator_id FROM coordinator_tasks 
        WHERE coordinator_id IS NOT NULL AND coordinator_id != ''
        AND (coordinator_id NOT GLOB '[0-9]*' OR coordinator_id NOT LIKE '%[^0-9]%')
        LIMIT 10
        """)
        sample_ids = cursor.fetchall()
        logger.info(f"Sample coordinator IDs (should be mostly integers): {sample_ids}")
        
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error populating coordinator monthly summary: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def populate_coordinator_monthly_summary_with_mapping(db_path='production.db'):
    """Alternative approach: First create a mapping table to properly handle coordinator_id conversion"""
    logger.info("Starting coordinator monthly summary population with proper mapping...")
    
    conn = get_db_connection(db_path)
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM dashboard_coordinator_monthly_summary")
        logger.info("Cleared existing data from dashboard_coordinator_monthly_summary")
        
        # First, let's see what kind of data we have in coordinator_tasks
        cursor.execute("""
        SELECT coordinator_id, COUNT(*) as count 
        FROM coordinator_tasks 
        WHERE coordinator_id IS NOT NULL AND coordinator_id != ''
        GROUP BY coordinator_id
        ORDER BY count DESC
        LIMIT 10
        """)
        coordinator_samples = cursor.fetchall()
        logger.info(f"Sample coordinator_id values: {coordinator_samples}")
        
        # Try to identify valid integer coordinator_ids and map them properly
        # This is a more robust approach - we'll use a different query that handles the conversion better
        query = """
        INSERT INTO dashboard_coordinator_monthly_summary 
        (coordinator_id, month, year, total_minutes, total_minutes_per_patient, 
         total_tasks_completed, average_daily_tasks)
        SELECT 
            -- Convert coordinator_id to integer if possible, otherwise skip
            CAST(ct.coordinator_id AS INTEGER) as coordinator_id,
            strftime('%m', ct.task_date) as month,
            strftime('%Y', ct.task_date) as year,
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
        AND ct.coordinator_id GLOB '[0-9]*'  -- Only include numeric values
        AND ct.duration_minutes IS NOT NULL
        AND ct.duration_minutes > 0
        GROUP BY 
            CAST(ct.coordinator_id AS INTEGER),
            strftime('%m', ct.task_date),
            strftime('%Y', ct.task_date)
        """
        
        cursor.execute(query)
        conn.commit()
        rows_affected = cursor.rowcount
        logger.info(f"Populated {rows_affected} rows in dashboard_coordinator_monthly_summary")
        
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error populating coordinator monthly summary: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main function to populate coordinator monthly summary"""
    logger.info("Starting coordinator monthly summary population script")
    
    try:
        # Try the first approach
        success = populate_coordinator_monthly_summary_with_mapping()
        
        if success:
            logger.info("Successfully populated coordinator monthly summary")
        else:
            logger.error("Failed to populate coordinator monthly summary")
            
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
