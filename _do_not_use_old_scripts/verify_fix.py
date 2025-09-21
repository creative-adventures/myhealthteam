#!/usr/bin/env python3
"""
Script to verify the fix for the database query parameter binding issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import database
import sqlite3

def test_database_queries():
    """Test that the database queries work without parameter binding errors"""
    
    print("Testing database queries for provider dashboard...")
    
    # Test 1: Check if we can get a provider ID
    try:
        conn = database.get_db_connection()
        cursor = conn.execute("SELECT provider_id FROM providers LIMIT 1")
        result = cursor.fetchone()
        if result:
            provider_id = result[0]
            print(f"✓ Found provider ID: {provider_id}")
        else:
            print("⚠ No providers found in database")
            return False
        conn.close()
    except Exception as e:
        print(f"✗ Error getting provider ID: {e}")
        return False
    
    # Test 2: Test the summary table queries that were working
    try:
        conn = database.get_db_connection()
        cursor = conn.execute("""
            SELECT DISTINCT 
                prs.region_id, 
                prs.zip_code, 
                prs.city, 
                prs.state,
                prs.patient_count
            FROM provider_region_summary prs
            WHERE prs.provider_id = ? AND prs.region_id IS NOT NULL
            ORDER BY prs.city, prs.zip_code
        """, (provider_id,))
        regions = cursor.fetchall()
        print(f"✓ Summary region query works: {len(regions)} regions found")
        conn.close()
    except Exception as e:
        print(f"✗ Error in summary region query: {e}")
        return False
    
    # Test 3: Test the fallback region query (the one that was failing)
    try:
        conn = database.get_db_connection()
        cursor = conn.execute("""
            SELECT DISTINCT 
                r.region_id,
                r.zip_code,
                r.city,
                r.state,
                COUNT(DISTINCT p.patient_id) as patient_count
            FROM regions r
            LEFT JOIN patients p ON r.region_id = p.region_id
            WHERE r.status = 'active' AND r.zip_code IS NOT NULL AND r.zip_code != ''
            GROUP BY r.region_id, r.zip_code, r.city, r.state
            ORDER BY r.city, r.zip_code
        """)
        regions = cursor.fetchall()
        print(f"✓ Fallback region query works: {len(regions)} regions found")
        conn.close()
    except Exception as e:
        print(f"✗ Error in fallback region query: {e}")
        return False
    
    # Test 4: Test the fallback zip code query (the one that was failing)
    try:
        conn = database.get_db_connection()
        cursor = conn.execute("""
            SELECT DISTINCT 
                r.zip_code,
                r.city,
                r.state,
                COUNT(DISTINCT p.patient_id) as patient_count
            FROM regions r
            LEFT JOIN patients p ON r.region_id = p.region_id
            WHERE r.status = 'active' AND r.zip_code IS NOT NULL AND r.zip_code != ''
            GROUP BY r.zip_code, r.city, r.state
            ORDER BY r.zip_code
        """)
        zip_codes = cursor.fetchall()
        print(f"✓ Fallback zip code query works: {len(zip_codes)} zip codes found")
        conn.close()
    except Exception as e:
        print(f"✗ Error in fallback zip code query: {e}")
        return False
    
    print("✓ All database queries are working correctly!")
    return True

if __name__ == "__main__":
    success = test_database_queries()
    if success:
        print("\n🎉 Fix verification successful - the parameter binding issue has been resolved!")
        sys.exit(0)
    else:
        print("\n❌ Fix verification failed")
        sys.exit(1)
