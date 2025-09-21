#!/usr/bin/env python3
"""
Script to populate regions table using county data from zip-codes.csv
This will create proper region entries with county information instead of region_name
"""

import sqlite3
import pandas as pd
from src.database import get_db_connection
import re

def create_regions_from_zip_codes():
    """Create regions from zip-codes.csv data with proper county information"""
    print("Creating regions from zip-codes.csv data...")
    
    # Read the zip-codes.csv file
    df = pd.read_csv('zip-codes.csv')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Process the zip codes data
    regions_created = 0
    unique_regions = set()
    
    # Process each row in the zip codes CSV
    for index, row in df.iterrows():
        zip_code = row.get('zip', '').strip()
        city = row.get('city', '').strip()
        county = row.get('county', '').strip()
        
        # Skip rows without proper data
        if not zip_code or not county:
            continue
            
        # Create a unique region identifier (county + city combination)
        region_identifier = f"{county}_{city}"
        
        # Only create region if we haven't created it already
        if region_identifier not in unique_regions:
            # Create or get region with county information
            cursor.execute("""
                INSERT OR REPLACE INTO regions 
                (region_name, city, zip_code, state, county, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f"{county} Region", city, zip_code, 'CA', county, 'active'))
            
            region_id = cursor.lastrowid
            regions_created += 1
            unique_regions.add(region_identifier)
            
            print(f"Created region: {county} Region, City: {city}, Zip: {zip_code}, County: {county}")
    
    conn.commit()
    conn.close()
    
    print(f"Created {regions_created} unique regions with county information")
    
    return regions_created

def main():
    """Main function to process zip-codes.csv and populate database"""
    print("Starting zip-codes based region population...")
    
    try:
        regions = create_regions_from_zip_codes()
        print(f"Successfully processed zip-codes.csv data!")
        print(f"Total regions created: {regions}")
        
    except Exception as e:
        print(f"Error processing zip-codes.csv: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
