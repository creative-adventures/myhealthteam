#!/usr/bin/env python3
"""
Script to populate region_id values in patients table based on zip codes
This will link patients to regions so the dashboard can work properly
"""

from src.database import get_db_connection
import sqlite3

def populate_patient_region_ids():
    """Populate region_id values in patients table based on zip code matching"""
    print("Populating region_id values in patients table...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, let's see how many patients currently have region_id
    cursor.execute("SELECT COUNT(*) as total, COUNT(region_id) as with_region_id FROM patients;")
    total, with_region_id = cursor.fetchone()
    print(f"Patients before: {total} total, {with_region_id} with region_id")
    
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
    updated_count = 0
    
    # Process patients in batches to avoid memory issues
    cursor.execute("SELECT patient_id, address_zip FROM patients WHERE address_zip IS NOT NULL AND address_zip != ''")
    patients = cursor.fetchall()
    
    print(f"Found {len(patients)} patients with zip codes")
    
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
    print(f"Patients after: {total} total, {with_region_id} with region_id")
    print(f"Updated {updated_count} patients with region_id")
    
    conn.close()
    
    return updated_count

def verify_region_assignment():
    """Verify that region assignments were successful"""
    print("\nVerifying region assignments...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check some sample patients
    cursor.execute("""
        SELECT p.patient_id, p.first_name, p.last_name, p.address_zip, p.region_id, r.county
        FROM patients p
        LEFT JOIN regions r ON p.region_id = r.region_id
        WHERE p.region_id IS NOT NULL
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    print("Sample patients with region assignments:")
    for row in results:
        print(f"  Patient {row[0]} ({row[1]} {row[2]}): Zip {row[3]}, Region ID {row[4]}, County {row[5]}")
    
    # Check how many patients have regions now
    cursor.execute("SELECT COUNT(*) as count FROM patients WHERE region_id IS NOT NULL")
    count = cursor.fetchone()[0]
    print(f"\nTotal patients with region_id: {count}")
    
    conn.close()

def main():
    """Main function"""
    try:
        print("Starting patient region ID population...")
        updated = populate_patient_region_ids()
        verify_region_assignment()
        print(f"Successfully populated region IDs for {updated} patients!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
