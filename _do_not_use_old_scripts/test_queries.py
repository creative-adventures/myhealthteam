import sqlite3
from src import database

# Test the problematic queries directly
def test_queries():
    # Get a provider_id for testing
    conn = database.get_db_connection()
    cursor = conn.execute("SELECT provider_id FROM providers LIMIT 1")
    result = cursor.fetchone()
    if result:
        provider_id = result[0]
        print(f"Testing with provider_id: {provider_id}")
        
        # Test the first query that was failing
        try:
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
            print(f"Direct region query returned {len(regions)} rows")
        except Exception as e:
            print(f"Error in direct region query: {e}")
        
        # Test the second query that was failing
        try:
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
            print(f"Direct zip code query returned {len(zip_codes)} rows")
        except Exception as e:
            print(f"Error in direct zip code query: {e}")
            
        # Test the summary table queries
        try:
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
            regions_summary = cursor.fetchall()
            print(f"Summary region query returned {len(regions_summary)} rows")
        except Exception as e:
            print(f"Error in summary region query: {e}")
            
        try:
            cursor = conn.execute("""
                SELECT DISTINCT 
                    pzs.zip_code, 
                    pzs.city, 
                    pzs.state,
                    pzs.patient_count
                FROM provider_zip_summary pzs
                WHERE pzs.provider_id = ? AND pzs.zip_code IS NOT NULL AND pzs.zip_code != ''
                ORDER BY pzs.zip_code
            """, (provider_id,))
            zip_codes_summary = cursor.fetchall()
            print(f"Summary zip code query returned {len(zip_codes_summary)} rows")
        except Exception as e:
            print(f"Error in summary zip code query: {e}")
            
    conn.close()

if __name__ == "__main__":
    test_queries()
