#!/usr/bin/env python3
"""
Simple script to populate the coordinator_monthly_summary table with data from coordinator_tasks.
This script processes existing coordinator tasks and creates monthly summaries with proper billing codes.
"""

import sqlite3
from datetime import datetime

# Direct database connection
DB_PATH = 'production.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def populate_coordinator_monthly_summary():
    """
    Populate the coordinator_monthly_summary table with aggregated data from coordinator_tasks.
    """
    print("Starting coordinator monthly summary population...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing data in coordinator_monthly_summary table
        print("Clearing existing data from coordinator_monthly_summary...")
        cursor.execute("DELETE FROM coordinator_monthly_summary")
        
        # Get all coordinator billing codes to map minutes to billing codes
        print("Fetching billing codes...")
        billing_codes = cursor.execute("""
            SELECT code_id, billing_code, description, min_minutes, max_minutes 
            FROM coordinator_billing_codes 
            ORDER BY min_minutes
        """).fetchall()
        
        # Create a mapping of minute ranges to billing codes for efficient lookup
        billing_code_mapping = {}
        for bc in billing_codes:
            billing_code_mapping[(bc['min_minutes'], bc['max_minutes'])] = {
                'code_id': bc['code_id'],
                'billing_code': bc['billing_code'],
                'description': bc['description']
            }
        
        print(f"Loaded {len(billing_codes)} billing codes")
        
        # Process coordinator tasks and create monthly summaries
        print("Processing coordinator tasks...")
        
        # Query to get all coordinator tasks with necessary information
        query = """
        SELECT 
            ct.coordinator_id,
            ct.patient_id,
            strftime('%Y', ct.task_date) as year,
            strftime('%m', ct.task_date) as month,
            SUM(ct.duration_minutes) as total_minutes
        FROM coordinator_tasks ct
        WHERE ct.task_date IS NOT NULL AND ct.task_date != '' AND ct.coordinator_id IS NOT NULL
        GROUP BY ct.coordinator_id, ct.patient_id, strftime('%Y', ct.task_date), strftime('%m', ct.task_date)
        """
        
        tasks_data = cursor.execute(query).fetchall()
        print(f"Found {len(tasks_data)} unique coordinator-monthly-patient combinations")
        
        # Process each group and insert into summary table
        inserted_count = 0
        for task in tasks_data:
            try:
                coordinator_id = task['coordinator_id']
                patient_id = task['patient_id']
                # patient_name will be set to patient_id as fallback since we don't have it in coordinator_tasks
                patient_name = patient_id
                
                # Handle potential None values
                year_str = task['year']
                month_str = task['month']
                total_minutes = task['total_minutes']
                
                if year_str is None or month_str is None:
                    print(f"Skipping record with None date values: coordinator_id={coordinator_id}, patient_id={patient_id}")
                    continue
                    
                year = int(year_str)
                month = int(month_str)
                
                # Determine billing code based on total minutes
                billing_code_id = None
                billing_code = None
                billing_code_description = None
                
                # Find appropriate billing code based on minute ranges
                for (min_minutes, max_minutes), bc_info in billing_code_mapping.items():
                    if min_minutes <= total_minutes <= max_minutes:
                        billing_code_id = bc_info['code_id']
                        billing_code = bc_info['billing_code']
                        billing_code_description = bc_info['description']
                        break
                
                # Get coordinator name from users table
                coordinator_name = None
                if coordinator_id:
                    user_query = """
                    SELECT u.first_name, u.last_name 
                    FROM users u
                    JOIN coordinators c ON u.user_id = c.user_id
                    WHERE c.coordinator_id = ?
                    """
                    user_result = cursor.execute(user_query, (coordinator_id,)).fetchone()
                    if user_result:
                        coordinator_name = f"{user_result[0]} {user_result[1]}"
                
                # Insert into coordinator_monthly_summary table
                insert_query = """
                INSERT INTO coordinator_monthly_summary (
                    coordinator_id,
                    coordinator_name,
                    patient_id,
                    patient_name,
                    year,
                    month,
                    total_minutes,
                    billing_code_id,
                    billing_code,
                    billing_code_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_query, (
                    coordinator_id,
                    coordinator_name,
                    patient_id,
                    patient_name,
                    year,
                    month,
                    total_minutes,
                    billing_code_id,
                    billing_code,
                    billing_code_description
                ))
                
                inserted_count += 1
                
                # Print progress every 1000 records
                if inserted_count % 1000 == 0:
                    print(f"Processed {inserted_count} records...")
                    
            except Exception as e:
                print(f"Error processing task record: {e}")
                print(f"Task data: {task}")
                continue
        
        conn.commit()
        print(f"Successfully populated {inserted_count} records into coordinator_monthly_summary")
        
        # Verify the results
        final_count = cursor.execute("SELECT COUNT(*) as total FROM coordinator_monthly_summary").fetchone()['total']
        print(f"Total records in coordinator_monthly_summary: {final_count}")
        
        return inserted_count
        
    except Exception as e:
        print(f"Error populating coordinator monthly summary: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def main():
    """Main function to run the population script."""
    print("Coordinator Monthly Summary Population Script")
    print("=" * 50)
    
    try:
        count = populate_coordinator_monthly_summary()
        print(f"\nSuccessfully populated {count} records in coordinator_monthly_summary table!")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
