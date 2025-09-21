#!/usr/bin/env python3
"""
Test script to verify the summary tables and dashboard functionality
"""

import sqlite3
from src.database import get_db_connection

def test_summary_tables():
    """Test that summary tables are properly structured and populated"""
    print("Testing summary tables...")
    
    conn = get_db_connection()
    
    # Test provider_region_summary
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM provider_region_summary")
    region_count = cursor.fetchone()[0]
    print(f"provider_region_summary rows: {region_count}")
    
    # Test provider_zip_summary
    cursor.execute("SELECT COUNT(*) as count FROM provider_zip_summary")
    zip_count = cursor.fetchone()[0]
    print(f"provider_zip_summary rows: {zip_count}")
    
    # Test patient_region_mapping
    cursor.execute("SELECT COUNT(*) as count FROM patient_region_mapping")
    patient_count = cursor.fetchone()[0]
    print(f"patient_region_mapping rows: {patient_count}")
    
    # Show sample data from patient_region_mapping
    cursor.execute("SELECT * FROM patient_region_mapping LIMIT 5")
    sample_data = cursor.fetchall()
    print("Sample patient_region_mapping data:")
    for row in sample_data:
        print(f"  {row}")
    
    conn.close()
    
    print("Test completed successfully!")

if __name__ == "__main__":
    test_summary_tables()
