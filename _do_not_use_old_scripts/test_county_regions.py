#!/usr/bin/env python3
"""
Test script to verify county-based region creation
"""

import sqlite3
from src.database import get_db_connection

def test_county_regions():
    """Test that regions table has county information"""
    print("Testing county-based regions in database...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check the structure of regions table
    cursor.execute("SELECT * FROM regions LIMIT 5;")
    rows = cursor.fetchall()
    
    print("Sample regions from database:")
    for row in rows:
        print(f"  ID: {row[0]}, Name: {row[1]}, City: {row[3]}, Zip: {row[2]}, County: {row[5]}")
    
    # Count regions with county data
    cursor.execute("SELECT COUNT(*) as total, COUNT(county) as with_county FROM regions;")
    total, with_county = cursor.fetchone()
    print(f"\nRegions total: {total}, with county data: {with_county}")
    
    # Show some counties
    cursor.execute("SELECT DISTINCT county FROM regions WHERE county IS NOT NULL AND county != '' LIMIT 10;")
    counties = cursor.fetchall()
    print("Sample counties:")
    for county in counties:
        print(f"  {county[0]}")
    
    conn.close()

if __name__ == "__main__":
    test_county_regions()
