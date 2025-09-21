#!/usr/bin/env python3
"""
Script to populate the summary tables with existing data
This script should be run once to initialize the summary tables
with data from the existing database structure.
"""

import sqlite3
import os

def get_db_connection():
    """Get database connection - modified to work with current structure"""
    db_path = 'production.db'
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file {db_path} not found")
    return sqlite3.connect(db_path)

def populate_provider_region_summary():
    """Populate provider_region_summary table with data from existing relationships"""
    print("Populating provider_region_summary table...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM provider_region_summary")
    
    # Insert data using the existing relationships
    # Note: We no longer have region_name in regions table, so we'll use city and county instead
    query = """
    INSERT OR REPLACE INTO provider_region_summary 
    (provider_id, region_id, zip_code, city, state, patient_count)
    SELECT 
        rp.provider_id,
        r.region_id,
        r.zip_code,
        r.city,
        r.state,
        COUNT(DISTINCT p.patient_id) as patient_count
    FROM region_providers rp
    JOIN regions r ON rp.region_id = r.region_id
    LEFT JOIN patients p ON r.region_id = p.region_id
    WHERE r.status = 'active'
    GROUP BY rp.provider_id, r.region_id, r.zip_code, r.city, r.state
    """
    
    cursor.execute(query)
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    
    print(f"Populated {rows_affected} rows in provider_region_summary")
    return rows_affected

def populate_provider_zip_summary():
    """Populate provider_zip_summary table with zip code data"""
    print("Populating provider_zip_summary table...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM provider_zip_summary")
    
    # Insert data using the existing relationships and patient data
    query = """
    INSERT OR REPLACE INTO provider_zip_summary 
    (provider_id, zip_code, city, state, patient_count, region_count)
    SELECT 
        rp.provider_id,
        r.zip_code,
        r.city,
        r.state,
        COUNT(DISTINCT p.patient_id) as patient_count,
        COUNT(DISTINCT r.region_id) as region_count
    FROM region_providers rp
    JOIN regions r ON rp.region_id = r.region_id
    LEFT JOIN patients p ON r.region_id = p.region_id
    WHERE r.status = 'active' AND r.zip_code IS NOT NULL AND r.zip_code != ''
    GROUP BY rp.provider_id, r.zip_code, r.city, r.state
    """
    
    cursor.execute(query)
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    
    print(f"Populated {rows_affected} rows in provider_zip_summary")
    return rows_affected

def populate_patient_region_mapping():
    """Populate patient_region_mapping table with direct patient-region relationships"""
    print("Populating patient_region_mapping table...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM patient_region_mapping")
    
    # Insert data using direct patient-region relationships
    query = """
    INSERT OR REPLACE INTO patient_region_mapping 
    (patient_id, region_id, zip_code, city, state)
    SELECT 
        p.patient_id,
        p.region_id,
        r.zip_code,
        r.city,
        r.state
    FROM patients p
    JOIN regions r ON p.region_id = r.region_id
    WHERE p.region_id IS NOT NULL
    """
    
    cursor.execute(query)
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    
    print(f"Populated {rows_affected} rows in patient_region_mapping")
    return rows_affected

def main():
    """Main function to populate all summary tables"""
    print("Starting summary table population...")
    
    try:
        # Populate all summary tables
        populate_provider_region_summary()
        populate_provider_zip_summary()
        populate_patient_region_mapping()
        
        print("All summary tables populated successfully!")
        
    except Exception as e:
        print(f"Error populating summary tables: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
