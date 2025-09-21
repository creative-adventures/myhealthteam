#!/usr/bin/env python3
"""
Simple CSV processor to establish provider-region relationships
Focuses on the meaningful columns and ignores unnamed columns
"""

import pandas as pd
from src.database import get_db_connection
import sqlite3

def create_simple_region_provider_mapping():
    """Create a simple mapping from CSV data to establish provider-region relationships"""
    print("Processing CSV to establish provider-region relationships...")
    
    # Read the CSV file
    df = pd.read_csv('combined_region_zip_codes.csv')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get existing providers
    cursor.execute("SELECT provider_id, first_name, last_name FROM providers")
    providers = cursor.fetchall()
    print(f"Found {len(providers)} providers")
    
    # Create provider name mapping
    provider_mapping = {}
    for provider in providers:
        provider_id = provider[0]
        name = f"{provider[1]} {provider[2]}"
        provider_mapping[name] = provider_id
        print(f"  Provider: {name} (ID: {provider_id})")
    
    # Count of relationships we'll create
    relationships_created = 0
    
    # Process the main region data (first 3 columns)
    for index, row in df.iterrows():
        # Get main region information
        region_name = row.get('Region', None)
        city = row.get('City', None)
        zip_codes_str = row.get('ZIP Codes', None)
        
        # Skip if any required field is missing
        if pd.isna(region_name) or pd.isna(city) or pd.isna(zip_codes_str):
            continue
            
        region_name = str(region_name).strip()
        city = str(city).strip()
        zip_codes_str = str(zip_codes_str).strip()
        
        if not region_name or not city or not zip_codes_str:
            continue
            
        print(f"Processing: {region_name}, {city} - {zip_codes_str}")
        
        # Create or get region
        cursor.execute("""
            INSERT OR REPLACE INTO regions 
            (region_name, city, zip_code, state, status)
            VALUES (?, ?, ?, ?, ?)
        """, (region_name, city, zip_codes_str.split(',')[0].strip(), 'CA', 'active'))
        
        region_id = cursor.lastrowid
        
        # Check for provider assignments in the provider columns
        # These are the actual provider name columns we care about
        provider_columns = ['Malhotra', 'Anisha', 'Ethel', 'Andrew', 'Lourdes', 'Albert', 'Jaspreet', 'Angela']
        
        for col in provider_columns:
            provider_name = row.get(col, None)
            if not pd.isna(provider_name) and provider_name and str(provider_name).strip().lower() != 'nan':
                provider_name = str(provider_name).strip()
                if provider_name in provider_mapping:
                    provider_id = provider_mapping[provider_name]
                    try:
                        # Create the relationship
                        cursor.execute("""
                            INSERT OR REPLACE INTO region_providers 
                            (region_id, provider_id)
                            VALUES (?, ?)
                        """, (region_id, provider_id))
                        relationships_created += 1
                        print(f"  Assigned {provider_name} to {region_name}")
                    except Exception as e:
                        print(f"  Error assigning {provider_name} to {region_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"Successfully created {relationships_created} provider-region relationships")
    return relationships_created

def test_relationships():
    """Test that relationships were created properly"""
    print("\nTesting relationships...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check region_providers table
    cursor.execute("SELECT COUNT(*) as count FROM region_providers")
    count = cursor.fetchone()[0]
    print(f"Region-providers relationships: {count}")
    
    # Show some sample relationships
    cursor.execute("""
        SELECT rp.region_id, r.region_name, p.first_name, p.last_name
        FROM region_providers rp
        JOIN regions r ON rp.region_id = r.region_id
        JOIN providers p ON rp.provider_id = p.provider_id
        LIMIT 10
    """)
    
    relationships = cursor.fetchall()
    print("Sample relationships:")
    for rel in relationships:
        print(f"  {rel[1]} -> {rel[2]} {rel[3]}")
    
    conn.close()

def main():
    """Main function"""
    try:
        print("Starting simple CSV processing...")
        relationships = create_simple_region_provider_mapping()
        test_relationships()
        print(f"Successfully processed CSV and created {relationships} relationships!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
