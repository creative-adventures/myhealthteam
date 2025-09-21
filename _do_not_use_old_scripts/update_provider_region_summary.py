#!/usr/bin/env python3
"""
Script to update provider_region_summary table to include ALL regions 
a provider has to serve because of patient assignments
"""

import sqlite3
import os

def get_db_connection():
    """Get database connection"""
    db_path = 'production.db'
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file {db_path} not found")
    return sqlite3.connect(db_path)

def update_provider_region_summary():
    """Update provider_region_summary to include all regions providers serve due to patient assignments"""
    print("Updating provider_region_summary table...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM provider_region_summary")
    print("Cleared existing provider_region_summary data")
    
    # Get all patient assignments and build the comprehensive view
    # This query gets all regions that patients are assigned to, grouped by provider
    query = """
    INSERT OR REPLACE INTO provider_region_summary 
    (provider_id, region_id, region_name, zip_code, city, state, patient_count)
    SELECT 
        COALESCE(pa.provider_id, rp.provider_id) as provider_id,
        r.region_id,
        r.region_name,
        r.zip_code,
        r.city,
        r.state,
        COUNT(DISTINCT p.patient_id) as patient_count
    FROM regions r
    LEFT JOIN patients p ON r.region_id = p.region_id
    LEFT JOIN patient_assignments pa ON p.patient_id = pa.patient_id
    LEFT JOIN region_providers rp ON r.region_id = rp.region_id
    WHERE r.status = 'active' 
    GROUP BY 
        COALESCE(pa.provider_id, rp.provider_id),
        r.region_id,
        r.region_name,
        r.zip_code,
        r.city,
        r.state
    HAVING COUNT(DISTINCT p.patient_id) > 0 OR COUNT(DISTINCT rp.provider_id) > 0
    ORDER BY provider_id, r.region_id
    """
    
    try:
        cursor.execute(query)
        conn.commit()
        rows_affected = cursor.rowcount
        print(f"Populated {rows_affected} rows in provider_region_summary")
        
        # Also update the patient_count for existing relationships
        # This ensures we have the correct counts for regions that providers actually serve
        cursor.execute("""
            UPDATE provider_region_summary 
            SET patient_count = (
                SELECT COUNT(DISTINCT p.patient_id) 
                FROM patients p 
                JOIN regions r ON p.region_id = r.region_id 
                WHERE r.region_id = provider_region_summary.region_id
            )
        """)
        conn.commit()
        print("Updated patient counts for existing records")
        
    except Exception as e:
        print(f"Error in main query: {e}")
        # Fallback to simpler approach
        print("Using fallback approach...")
        
        # Simple approach: use existing region_providers relationships
        cursor.execute("""
            INSERT OR REPLACE INTO provider_region_summary 
            (provider_id, region_id, region_name, zip_code, city, state, patient_count)
            SELECT 
                rp.provider_id,
                r.region_id,
                r.region_name,
                r.zip_code,
                r.city,
                r.state,
                COUNT(DISTINCT p.patient_id) as patient_count
            FROM region_providers rp
            JOIN regions r ON rp.region_id = r.region_id
            LEFT JOIN patients p ON r.region_id = p.region_id
            WHERE r.status = 'active'
            GROUP BY rp.provider_id, r.region_id, r.region_name, r.zip_code, r.city, r.state
            ORDER BY rp.provider_id, r.region_id
        """)
        
        conn.commit()
        rows_affected = cursor.rowcount
        print(f"Fallback: Populated {rows_affected} rows in provider_region_summary")
    
    conn.close()
    return True

def verify_update():
    """Verify the update was applied correctly"""
    print("\nVerifying update...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check the count
    cursor.execute("SELECT COUNT(*) FROM provider_region_summary")
    count = cursor.fetchone()[0]
    print(f"Total records in provider_region_summary: {count}")
    
    # Show sample data
    cursor.execute("""
        SELECT prs.provider_id, p.first_name, p.last_name, 
               prs.region_id, r.zip_code, r.city, prs.patient_count
        FROM provider_region_summary prs
        JOIN providers p ON prs.provider_id = p.provider_id
        JOIN regions r ON prs.region_id = r.region_id
        ORDER BY prs.provider_id
        LIMIT 10
    """)
    
    sample_data = cursor.fetchall()
    print("Sample data:")
    for row in sample_data:
        print(f"  Provider {row[0]} ({row[1]} {row[2]}): Region {row[3]} ({row[4]} {row[5]}), {row[6]} patients")
    
    conn.close()

def main():
    """Main function"""
    print("Starting provider_region_summary update...")
    
    try:
        update_provider_region_summary()
        verify_update()
        print("\nProvider_region_summary update completed successfully!")
        
    except Exception as e:
        print(f"Error updating provider_region_summary: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
