#!/usr/bin/env python3
"""
Script to properly fix the regions table in production.db:
1. Remove the region_name column
2. Drop all existing data
3. Reinsert data from zip-codes.csv with proper AUTOINCREMENT handling
"""

import sqlite3
import csv
import os

def fix_regions_table():
    db_path = 'production.db'
    csv_path = 'zip-codes.csv'
    
    # Check if files exist
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} not found")
        return False
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file {csv_path} not found")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Current regions table structure:")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='regions';")
        schema = cursor.fetchone()
        if schema:
            print(schema[0])
        
        print("\nCurrent data count in regions table:")
        cursor.execute("SELECT COUNT(*) as total FROM regions;")
        count_result = cursor.fetchone()
        print(f"Total records: {count_result[0]}")
        
        # Step 1: Create a new table without region_name column (keeping the same structure)
        print("\nCreating new table structure...")
        cursor.execute('''
            CREATE TABLE regions_new (
                region_id INTEGER PRIMARY KEY AUTOINCREMENT,
                zip_code TEXT,
                city TEXT,
                state TEXT,
                county TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Step 2: Drop the old table
        print("Dropping old regions table...")
        cursor.execute('DROP TABLE regions')
        
        # Step 3: Rename the new table to regions
        print("Renaming new table to regions...")
        cursor.execute('ALTER TABLE regions_new RENAME TO regions')
        
        # Step 4: Verify the new structure
        print("\nNew regions table structure:")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='regions';")
        new_schema = cursor.fetchone()
        if new_schema:
            print(new_schema[0])
        
        # Step 5: Clear all existing data from the regions table (should be empty now)
        print("Clearing existing data from regions table...")
        cursor.execute('DELETE FROM regions')
        
        # Step 6: Insert new data from zip-codes.csv using proper AUTOINCREMENT
        print("Inserting data from zip-codes.csv...")
        
        # Read CSV and insert data
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            inserted_count = 0
            
            for row in reader:
                zip_code = row['zip']
                city = row['city']
                county = row['county']
                
                # Insert with explicit column specification to let AUTOINCREMENT handle region_id
                cursor.execute('''
                    INSERT INTO regions (zip_code, city, state, county)
                    VALUES (?, ?, ?, ?)
                ''', (zip_code, city, 'CA', county))
                
                inserted_count += 1
                
                # Commit every 1000 rows to improve performance
                if inserted_count % 1000 == 0:
                    conn.commit()
                    print(f"Inserted {inserted_count} records...")
        
        conn.commit()
        print(f"Successfully inserted {inserted_count} records from zip-codes.csv")
        
        # Step 7: Verify the final result
        print("\nFinal verification:")
        cursor.execute("SELECT COUNT(*) as total FROM regions;")
        final_count = cursor.fetchone()[0]
        print(f"Total records in regions table: {final_count}")
        
        # Show first few records with proper region_id
        cursor.execute("SELECT region_id, zip_code, city, county FROM regions LIMIT 5;")
        sample_records = cursor.fetchall()
        print("Sample records:")
        for record in sample_records:
            print(f"  ID: {record[0]}, ZIP: {record[1]}, City: {record[2]}, County: {record[3]}")
        
        # Check if we have proper AUTOINCREMENT values
        cursor.execute("SELECT region_id FROM regions WHERE region_id IS NOT NULL AND region_id > 0 LIMIT 5;")
        ids = cursor.fetchall()
        print(f"Sample region_ids: {[id[0] for id in ids]}")
        
        conn.close()
        print("\nDatabase update completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    fix_regions_table()
