"""
Test script for dashboard summary utilities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dashboard_summary_utils import DashboardSummaryUtils
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    utils = DashboardSummaryUtils()
    
    if utils.connect():
        print("✓ Database connection successful")
        utils.disconnect()
        return True
    else:
        print("✗ Database connection failed")
        return False

def test_table_discovery():
    """Test table discovery functions"""
    print("\nTesting table discovery...")
    utils = DashboardSummaryUtils()
    
    if not utils.connect():
        print("Failed to connect to database")
        return False
    
    try:
        # Get dashboard tables
        dashboard_tables = utils.get_dashboard_tables()
        print(f"✓ Found {len(dashboard_tables)} dashboard tables:")
        for table in dashboard_tables:
            print(f"  - {table}")
        
        # Get non-dashboard tables
        non_dashboard_tables = utils.get_non_dashboard_tables()
        print(f"✓ Found {len(non_dashboard_tables)} non-dashboard tables to preserve")
        
        return True
    except Exception as e:
        print(f"✗ Error in table discovery: {e}")
        return False
    finally:
        utils.disconnect()

def test_create_tables():
    """Test creating dashboard tables"""
    print("\nTesting dashboard table creation...")
    utils = DashboardSummaryUtils()
    
    if not utils.connect():
        print("Failed to connect to database")
        return False
    
    try:
        if utils.create_dashboard_tables():
            print("✓ Dashboard tables created/verified successfully")
            return True
        else:
            print("✗ Failed to create dashboard tables")
            return False
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False
    finally:
        utils.disconnect()

def test_table_info():
    """Test getting table information"""
    print("\nTesting table information retrieval...")
    utils = DashboardSummaryUtils()
    
    if not utils.connect():
        print("Failed to connect to database")
        return False
    
    try:
        dashboard_tables = utils.get_dashboard_tables()
        if dashboard_tables:
            table_info = utils.get_table_info(dashboard_tables[0])
            if table_info:
                print(f"✓ Table info retrieved for {dashboard_tables[0]}:")
                print(f"  - Rows: {table_info['row_count']}")
                print(f"  - Columns: {len(table_info['columns'])}")
                return True
            else:
                print("✗ Failed to get table info")
                return False
        else:
            print("No dashboard tables found to test")
            return False
    except Exception as e:
        print(f"✗ Error getting table info: {e}")
        return False
    finally:
        utils.disconnect()

def main():
    """Run all tests"""
    print("Dashboard Summary Utilities - Test Suite")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_table_discovery,
        test_create_tables,
        test_table_info
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
