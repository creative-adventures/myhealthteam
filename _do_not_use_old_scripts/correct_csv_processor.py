#!/usr/bin/env python3
"""
Correct CSV processor that understands the actual CSV structure
The header row contains provider names, and subsequent rows contain their zip code regions
"""

import pandas as pd
from src.database import get_db_connection
import sqlite3

def create_correct_region_provider_mapping():
    """Create provider-region relationships from the actual CSV structure"""
    print("Processing CSV with correct structure understanding...")
    
    # Read the CSV file without headers first to see the structure
    df = pd.read_csv('combined_region_zip_codes.csv', header=0)
    
    print("CSV structure analysis:")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print("\nFirst 3 rows:")
    print(df.head(3))
    
    # Get existing providers
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT provider_id, first_name, last_name FROM providers")
    providers = cursor.fetchall()
    print(f"\nFound {len(providers)} providers")
    
    # Create provider name mapping (exact match)
    provider_mapping = {}
    for provider in providers:
        provider_id = provider[0]
        name = f"{provider[1]} {provider[2]}"
        provider_mapping[name] = provider_id
        print(f"  Provider: {name} (ID: {provider_id})")
    
    # The CSV structure: 
    # Row 0: Headers (provider names)
    # Row 1+: Data (zip codes for each provider)
    
    # Get the header row (first row) which contains provider names
    headers = df.columns.tolist()
    print(f"\nHeaders: {headers}")
    
    # Count of relationships we'll create
    relationships_created = 0
    
    # Process each provider from the headers
    for i, header in enumerate(headers):
        if pd.isna(header) or str(header).strip() == '' or str(header).lower() == 'nan':
            continue
            
        provider_name = str(header).strip()
        
        # Check if this is a valid provider name (not empty, not unnamed columns)
        if provider_name in ['Region', 'City', 'ZIP Codes', 'Unnamed: 3', 'Region.1', 'City.1', 'ZIP Codes.1', 
                            'Unnamed: 7', 'Region.2', 'City.2', 'ZIP Codes.2', 'Unnamed: 11', 'Region.3', 
                            'City.3', 'ZIP Codes.3', 'SCC LIST OF PROVIDERS', 'UNASSIGNED', 'Unnamed: 14', 
                            'Unnamed: 15', 'Region.4', 'City.4', 'ZIP Codes.4']:
            continue
            
        print(f"\nProcessing provider: '{provider_name}'")
        
        # Check if this provider exists in our database
        if provider_name in provider_mapping:
            provider_id = provider_mapping[provider_name]
            print(f"  Found matching provider with ID: {provider_id}")
            
            # Process each row of data for this provider
            for row_idx, row in df.iterrows():
                # Get the zip code value for this provider in this row
                zip_code_value = row.iloc[i]  # Get the value from the provider's column
                
                if pd.isna(zip_code_value) or str(zip_code_value).strip() == '' or str(zip_code_value).lower() == 'nan':
                    continue
                    
                zip_code_str = str(zip_code_value).strip()
                if not zip_code_str:
                    continue
                    
                print(f"    Row {row_idx}: {zip_code_str}")
                
                # Create regions for each zip code
                zip_codes = zip_code_str.split(',')
                for zip_code in zip_codes:
                    zip_code = zip_code.strip()
                    if not zip_code:
                        continue
                        
                    # Create or get region
                    cursor.execute("""
                        INSERT OR REPLACE INTO regions 
                        (region_name, city, zip_code, state, status)
                        VALUES (?, ?, ?, ?, ?)
                    """, (f"Provider Region - {provider_name}", "Unknown", zip_code, 'CA', 'active'))
                    
                    region_id = cursor.lastrowid
                    
                    # Create the relationship
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO region_providers 
                            (region_id, provider_id)
                            VALUES (?, ?)
                        """, (region_id, provider_id))
                        relationships_created += 1
                        print(f"      Assigned {zip_code} to {provider_name}")
                    except Exception as e:
                        print(f"      Error assigning {zip_code} to {provider_name}: {e}")
        else:
            print(f"  No matching provider found for: '{provider_name}'")
    
    conn.commit()
    conn.close()
    
    print(f"\nSuccessfully created {relationships_created} provider-region relationships")
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
        print("Starting correct CSV processing...")
        relationships = create_correct_region_provider_mapping()
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
