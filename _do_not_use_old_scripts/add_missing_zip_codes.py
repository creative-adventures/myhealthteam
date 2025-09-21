#!/usr/bin/env python3
"""
Script to add missing zip codes from patients to the regions table
This will ensure all patients can be properly assigned to regions
"""

from src.database import get_db_connection
import sqlite3

def add_missing_zip_codes():
    """Add missing zip codes from patients to regions table"""
    print("Adding missing zip codes to regions table...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, let's see how many patients currently have no region_id
    cursor.execute("SELECT COUNT(*) as missing_count FROM patients WHERE address_zip IS NOT NULL AND address_zip != '' AND region_id IS NULL;")
    missing_count = cursor.fetchone()[0]
    print(f"Patients without region_id: {missing_count}")
    
    # Get all distinct zip codes from patients that don't have region_id
    cursor.execute("""
        SELECT DISTINCT address_zip 
        FROM patients 
        WHERE address_zip IS NOT NULL AND address_zip != '' AND region_id IS NULL
    """)
    missing_zip_codes = [row[0] for row in cursor.fetchall()]
    
    print(f"Found {len(missing_zip_codes)} unique zip codes without regions")
    
    # Add these zip codes to regions table with blank values
    added_count = 0
    
    for zip_code in missing_zip_codes:
        if not zip_code or zip_code.strip() == '':
            continue
            
        # Clean the zip code (handle ranges)
        clean_zip = str(zip_code).strip()
        if '–' in clean_zip:
            clean_zip = clean_zip.split('–')[0].strip()
        
        # Check if this zip code already exists
        cursor.execute("SELECT region_id FROM regions WHERE zip_code = ?", (clean_zip,))
        existing = cursor.fetchone()
        
        if not existing:
            # Add new region with blank values
            try:
                cursor.execute("""
                    INSERT INTO regions 
                    (region_name, city, zip_code, state, county, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ("", "", clean_zip, "", "", "active"))
                added_count += 1
                print(f"  Added zip code: {clean_zip}")
            except Exception as e:
                print(f"  Error adding zip code {clean_zip}: {e}")
    
    conn.commit()
    
    # Verify the addition
    cursor.execute("SELECT COUNT(DISTINCT zip_code) as total_regions FROM regions WHERE zip_code IS NOT NULL AND zip_code != '';")
    total_regions = cursor.fetchone()[0]
    print(f"Total regions after addition: {total_regions}")
    print(f"Added {added_count} new zip codes to regions table")
    
    conn.close()
    
    return added_count

def assign_regions_to_remaining_patients():
    """Assign regions to patients that still don't have region_id"""
    print("\nAssigning regions to remaining patients...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all regions with zip codes
    cursor.execute("""
        SELECT region_id, zip_code 
        FROM regions 
        WHERE zip_code IS NOT NULL AND zip_code != '' AND status = 'active'
    """)
    regions = cursor.fetchall()
    
    print(f"Found {len(regions)} regions with zip codes")
    
    # Create a mapping of zip codes to region_ids
    zip_to_region = {}
    for region_id, zip_code in regions:
        if zip_code and zip_code.strip():
            # Handle zip code ranges (like "94102–94134") by using the first zip code
            if '–' in zip_code:
                zip_code = zip_code.split('–')[0].strip()
            zip_to_region[zip_code.strip()] = region_id
    
    print(f"Created zip code to region mapping for {len(zip_to_region)} zip codes")
    
    # Update patients with matching region_ids
    cursor.execute("SELECT patient_id, address_zip FROM patients WHERE address_zip IS NOT NULL AND address_zip != '' AND region_id IS NULL")
    patients = cursor.fetchall()
    
    print(f"Found {len(patients)} patients without region_id")
    
    updated_count = 0
    
    # Update patients one by one
    for patient_id, address_zip in patients:
        if not address_zip:
            continue
            
        # Clean the zip code (handle ranges)
        clean_zip = str(address_zip).strip()
        if '–' in clean_zip:
            clean_zip = clean_zip.split('–')[0].strip()
        
        # Try exact match first
        if clean_zip in zip_to_region:
            region_id = zip_to_region[clean_zip]
            cursor.execute("UPDATE patients SET region_id = ? WHERE patient_id = ?", (region_id, patient_id))
            updated_count += 1
        else:
            # Try to find a matching zip code prefix (for zip code ranges)
            for zip_code, region_id in zip_to_region.items():
                if clean_zip.startswith(zip_code) or zip_code.startswith(clean_zip):
                    cursor.execute("UPDATE patients SET region_id = ? WHERE patient_id = ?", (region_id, patient_id))
                    updated_count += 1
                    break
    
    conn.commit()
    
    # Check how many patients now have region_id
    cursor.execute("SELECT COUNT(*) as total, COUNT(region_id) as with_region_id FROM patients;")
    total, with_region_id = cursor.fetchone()
    print(f"Patients after assignment: {total} total, {with_region_id} with region_id")
    print(f"Updated {updated_count} patients with region_id")
    
    conn.close()
    
    return updated_count

def main():
    """Main function"""
    try:
        print("Starting missing zip code addition...")
        added = add_missing_zip_codes()
        assigned = assign_regions_to_remaining_patients()
        print(f"Successfully added {added} zip codes and assigned regions to {assigned} patients!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
