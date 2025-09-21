#!/usr/bin/env python3
"""
Debug CSV processing to see what's actually in the data
"""

import pandas as pd

def debug_csv():
    """Debug what's in the CSV"""
    print("Debugging CSV content...")
    
    # Read the CSV file
    df = pd.read_csv('combined_region_zip_codes.csv')
    
    print("Columns:", df.columns.tolist())
    print("\nFirst few rows:")
    print(df.head(3))
    
    # Check provider columns specifically
    provider_columns = ['Malhotra', 'Anisha', 'Ethel', 'Andrew', 'Lourdes', 'Albert', 'Jaspreet', 'Angela']
    
    print(f"\nProvider columns: {provider_columns}")
    
    # Check first few rows of provider columns
    for col in provider_columns[:3]:  # Just check first 3
        print(f"\n{col} column (first 5 values):")
        for i in range(5):
            if i < len(df):
                val = df.iloc[i][col]
                print(f"  Row {i}: {repr(val)} (type: {type(val)})")

if __name__ == "__main__":
    debug_csv()
