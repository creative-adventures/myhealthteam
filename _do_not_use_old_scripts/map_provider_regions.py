#!/usr/bin/env python3
"""
Script to map providers to regions based on provider_regions.txt
This will create the necessary relationships in the region_providers table
"""

import sqlite3
import csv
import os

def get_db_connection():
    """Get database connection"""
    db_path = 'production.db'
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file {db_path} not found")
    return sqlite3.connect(db_path)

def map_provider_regions():
    """Map providers to regions based on provider_regions.txt"""
    print("Mapping providers to regions...")
    
    # Read provider_regions.txt
    provider_regions_file = 'provider_regions.txt'
    
    if not os.path.exists(provider_regions_file):
        print(f"Error: {provider_regions_file} not found")
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing region_providers relationships (optional - be careful)
    # cursor.execute("DELETE FROM region_providers")
    # print("Cleared existing region_providers relationships")
    
    # Read the provider regions file
    with open(provider_regions_file, 'r') as f:
        lines = f.readlines()
    
    # Parse the file
    current_provider = None
    zip_codes = []
    mappings = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a provider name (first word in line)
        if not line.startswith('9') and not line.startswith('0') and line != '99027':
            # This is a provider name
            if current_provider and zip_codes:
                mappings[current_provider] = zip_codes.copy()
            current_provider = line
            zip_codes = []
        else:
            # This is a zip code
            if line == '99027':  # Special case - this is a zip code
                zip_codes.append(line)
            elif line.startswith('9') and len(line) == 5:
                zip_codes.append(line)
    
    # Don't forget the last provider
    if current_provider and zip_codes:
        mappings[current_provider] = zip_codes.copy()
    
    print(f"Found {len(mappings)} providers with zip code mappings")
    
    # Get all providers from database
    cursor.execute("SELECT provider_id, first_name, last_name FROM providers")
    providers = cursor.fetchall()
    
    provider_lookup = {}
    for provider in providers:
        provider_id, first_name, last_name = provider
        # Create a lookup key that matches the format in the text file
        provider_name = first_name.strip().lower() if first_name else ''
        provider_lookup[provider_name] = provider_id
    
    print(f"Database has {len(providers)} providers")
    print("Provider lookup keys:", list(provider_lookup.keys()))
    
    # Process each mapping
    total_mappings = 0
    for provider_name, zip_list in mappings.items():
        # Find the provider ID
        provider_id = None
        # Try exact match first
        if provider_name.lower() in provider_lookup:
            provider_id = provider_lookup[provider_name.lower()]
        # Try partial match
        elif provider_name.lower() in ['ethel', 'genevieive', 'eden', 'ugochi', 'angela']:
            # Try to match by first letter or common pattern
            for db_name, db_id in provider_lookup.items():
                if provider_name.lower() in db_name or db_name in provider_name.lower():
                    provider_id = db_id
                    break
        
        if provider_id:
            print(f"Mapping {provider_name} (ID: {provider_id}) to {len(zip_list)} zip codes")
            
            # For each zip code, find the region_id and create the relationship
            for zip_code in zip_list:
                # Find region_id for this zip code
                cursor.execute("SELECT region_id FROM regions WHERE zip_code = ?", (zip_code,))
                region_result = cursor.fetchone()
                
                if region_result:
                    region_id = region_result[0]
                    # Insert the relationship
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO region_providers (region_id, provider_id)
                            VALUES (?, ?)
                        """, (region_id, provider_id))
                        total_mappings += 1
                        print(f"  -> Mapped ZIP {zip_code} to region {region_id} for provider {provider_id}")
                    except Exception as e:
                        print(f"  -> Error mapping ZIP {zip_code}: {e}")
                else:
                    print(f"  -> No region found for ZIP {zip_code}")
        else:
            print(f"Warning: Provider '{provider_name}' not found in database")
    
    conn.commit()
    conn.close()
    
    print(f"\nSuccessfully created {total_mappings} provider-region relationships")
    return True

def verify_mappings():
    """Verify the mappings were created correctly"""
    print("\nVerifying mappings...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check how many relationships we have
    cursor.execute("SELECT COUNT(*) FROM region_providers")
    count = cursor.fetchone()[0]
    print(f"Total provider-region relationships: {count}")
    
    # Show some sample mappings
    cursor.execute("""
        SELECT rp.provider_id, p.first_name, p.last_name, r.zip_code, r.city
        FROM region_providers rp
        JOIN providers p ON rp.provider_id = p.provider_id
        JOIN regions r ON rp.region_id = r.region_id
        LIMIT 10
    """)
    
    sample_mappings = cursor.fetchall()
    print("Sample mappings:")
    for mapping in sample_mappings:
        print(f"  Provider {mapping[0]} ({mapping[1]} {mapping[2]}): ZIP {mapping[3]} in {mapping[4]}")
    
    conn.close()

def main():
    """Main function"""
    print("Starting provider-region mapping...")
    
    try:
        map_provider_regions()
        verify_mappings()
        print("\nProvider-region mapping completed successfully!")
        
    except Exception as e:
        print(f"Error in provider-region mapping: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
