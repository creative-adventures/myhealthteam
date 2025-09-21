#!/usr/bin/env python3
"""
Simple test script to debug coordinator summary population
"""

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_data():
    """Test what data we have in coordinator_tasks"""
    try:
        conn = sqlite3.connect('production.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check sample data
        logger.info("Checking sample coordinator_tasks data...")
        cursor.execute("""
            SELECT coordinator_id, task_date, duration_minutes 
            FROM coordinator_tasks 
            WHERE coordinator_id IS NOT NULL AND coordinator_id != '' 
            AND task_date IS NOT NULL AND task_date != ''
            AND duration_minutes IS NOT NULL AND duration_minutes > 0
            LIMIT 5
        """)
        rows = cursor.fetchall()
        for i, row in enumerate(rows):
            logger.info(f"Row {i+1}: coordinator_id='{row['coordinator_id']}', task_date='{row['task_date']}', duration_minutes={row['duration_minutes']}")
        
        # Check how many records match our criteria
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM coordinator_tasks 
            WHERE coordinator_id GLOB '[0-9]*' 
            AND task_date IS NOT NULL AND task_date != ''
            AND duration_minutes IS NOT NULL AND duration_minutes > 0
        """)
        count = cursor.fetchone()[0]
        logger.info(f"Records matching criteria: {count}")
        
        # Check what the GLOB pattern finds
        cursor.execute("""
            SELECT DISTINCT coordinator_id 
            FROM coordinator_tasks 
            WHERE coordinator_id IS NOT NULL AND coordinator_id != ''
            LIMIT 10
        """)
        sample_ids = cursor.fetchall()
        logger.info(f"Sample coordinator_id values: {[row['coordinator_id'] for row in sample_ids]}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in test_data: {e}")
        return False

def test_simple_query():
    """Test a simple query to see if we can get data"""
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        # Test the exact query that should work
        query = """
        SELECT 
            CASE 
                WHEN CAST(ct.coordinator_id AS INTEGER) > 0 AND ct.coordinator_id = CAST(ct.coordinator_id AS INTEGER) 
                THEN CAST(ct.coordinator_id AS INTEGER)
                ELSE NULL
            END as coordinator_id,
            strftime('%m', ct.task_date) as month,
            strftime('%Y', ct.task_date) as year,
            SUM(ct.duration_minutes) as total_minutes
        FROM coordinator_tasks ct
        WHERE ct.task_date IS NOT NULL AND ct.task_date != ''
        AND ct.coordinator_id IS NOT NULL AND ct.coordinator_id != ''
        AND ct.duration_minutes IS NOT NULL AND ct.duration_minutes > 0
        AND ct.coordinator_id GLOB '[0-9]*'
        GROUP BY 
            CASE 
                WHEN CAST(ct.coordinator_id AS INTEGER) > 0 AND ct.coordinator_id = CAST(ct.coordinator_id AS INTEGER) 
                THEN CAST(ct.coordinator_id AS INTEGER)
                ELSE NULL
            END,
            strftime('%m', ct.task_date),
            strftime('%Y', ct.task_date)
        HAVING coordinator_id IS NOT NULL
        LIMIT 5
        """
        
        logger.info("Testing simple query...")
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info(f"Query returned {len(rows)} rows")
        for i, row in enumerate(rows):
            logger.info(f"Result {i+1}: {row}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in test_simple_query: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting test...")
    test_data()
    test_simple_query()
