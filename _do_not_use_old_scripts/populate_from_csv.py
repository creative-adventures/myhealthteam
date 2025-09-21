#!/usr/bin/env python3
"""
Script to populate provider-region relationships from the combined_region_zip_codes.csv
This script will establish the actual relationships between providers and regions
based on the zip code data provided.
"""

import sqlite3
import pandas as pd
from src.database import get_db_connection
import re

def parse_zip_ranges(zip_string):
    """Parse zip code ranges like '94102–94134' into individual zip codes"""
    if pd.isna(zip_string) or zip_string is None or str(zip_string).strip() == '' or str(zip_string).lower() == 'nan':
        return []
    
    zip_string = str(zip_string).strip()
    zip_codes = []
    
    # Handle ranges like "94102–94134"
    if '–' in zip_string:
        parts = zip_string.split('–')
        if len(parts) == 2:
            start_zip = parts[0].strip()
            end_zip = parts[1].strip()
            # Simple approach: if it's a range, we'll just use the start zip
            # In a real implementation, you'd want to generate all zip codes in range
            zip_codes.append(start_zip)
        else:
            # Handle comma-separated ranges
            for part in zip_string.split(','):
                part = part.strip()
                if '–' in part:
                    range_parts = part.split('–')
                    if len(range_parts) == 2:
                        zip_codes.append(range_parts[0].strip())
                else:
                    zip_codes.append(part)
    else:
        # Handle comma-separated zip codes
        for zip_code in zip_string.split(','):
            zip_code = zip_code.strip()
            if zip_code and zip_code.lower() != 'nan':
                zip_codes.append(zip_code)
    
    return zip_codes

def create_regions_from_csv():
    """Create regions from the CSV data and establish provider relationships"""
    print("Creating regions from CSV data...")
    
    # Read the CSV file
    df = pd.read_csv('combined_region_zip_codes.csv')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, let's see what providers we have
    cursor.execute("SELECT provider_id, first_name, last_name FROM providers")
    providers = cursor.fetchall()
    print(f"Found {len(providers)} providers")
    
    # Create a mapping of provider names to provider IDs
    provider_mapping = {}
    for provider in providers:
        provider_id = provider[0]
        name = f"{provider[1]} {provider[2]}"
        provider_mapping[name] = provider_id
        print(f"  Provider: {name} (ID: {provider_id})")
    
    # Process the CSV data
    regions_created = 0
    relationships_created = 0
    
    # Process each row in the CSV
    for index, row in df.iterrows():
        # Get region information from the main columns
        # The "Region" column in combined_region_zip_codes.csv contains region names
        # We'll use this as the region_name and then we'll need to properly map to counties
        region_name = row.get('Region', '').strip()
        city = row.get('City', '').strip()
        zip_codes_str = row.get('ZIP Codes', '').strip()
        
        # Skip rows without proper data
        if not region_name or not zip_codes_str:
            continue
            
        # Parse zip codes
        zip_codes = parse_zip_ranges(zip_codes_str)
        
        if not zip_codes:
            continue
            
        # Create or get region - we'll use region_name for now, but we'll need to update with proper county info
        # For now, we'll use the region_name as the county since that's what's in the combined CSV
        # In a better implementation, we'd map this to actual county data from zip-codes.csv
        cursor.execute("""
            INSERT OR REPLACE INTO regions 
            (region_name, city, zip_code, state, county, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (region_name, city, zip_codes[0], 'CA', region_name, 'active'))
        
        region_id = cursor.lastrowid
        regions_created += 1
        
        # For each zip code, create a region entry
        for zip_code in zip_codes:
            if zip_code and zip_code.strip():
                # Update the region with the zip code
                cursor.execute("""
                    UPDATE regions 
                    SET zip_code = ?
                    WHERE region_name = ? AND city = ? AND zip_code IS NULL
                """, (zip_code.strip(), region_name, city))
        
        # Now establish relationships with providers
        # Check for provider columns (Malhotra, Anisha, Ethel, etc.)
        provider_columns = ['Malhotra', 'Anisha', 'Ethel', 'Andrew', 'Lourdes', 'Albert', 'Jaspreet', 'Angela']
        
        for provider_col in provider_columns:
            provider_name = row.get(provider_col, '').strip()
            if provider_name and provider_name.lower() != 'nan':
                # Check if this provider exists
                provider_id = provider_mapping.get(provider_name)
                if provider_id:
                    # Create relationship
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO region_providers 
                            (region_id, provider_id)
                            VALUES (?, ?)
                        """, (region_id, provider_id))
                        relationships_created += 1
                        print(f"  - Assigned {provider_name} to {region_name}")
                    except Exception as e:
                        print(f"  - Error assigning {provider_name} to {region_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"Created {regions_created} regions")
    print(f"Created {relationships_created} provider-region relationships")
    
    return regions_created, relationships_created

def main():
    """Main function to process CSV and populate database"""
    print("Starting CSV-based region population...")
    
    try:
        regions, relationships = create_regions_from_csv()
        print(f"Successfully processed CSV data!")
        print(f"Total regions created: {regions}")
        print(f"Total relationships established: {relationships}")
        
    except Exception as e:
        print(f"Error processing CSV: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
