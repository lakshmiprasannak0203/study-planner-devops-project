#!/usr/bin/env python
"""
Selenium Test Runner - Run automation tests for Study Planner

This script automates the process of running Selenium tests with proper setup.

Usage:
    python run_selenium_tests.py          # Run all tests
    python run_selenium_tests.py -v       # Verbose output
    python run_selenium_tests.py --help   # Show help
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set environment variables
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_NAME'] = 'study_planner'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASS'] = 'lakshmi'

def check_requirements():
    """Check if required packages are installed"""
    required = ['selenium', 'webdriver_manager']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"[ERROR] Missing required packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    return True

def check_app_running():
    """Check if Flask app is running"""
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 5000))
    sock.close()
    
    if result != 0:
        print("[WARNING] Flask app is not running on http://localhost:5000")
        print("Start it with: python app.py")
        return False
    
    print("[OK] Flask app is running on http://localhost:5000")
    return True

def check_database_connection():
    """Check if database is accessible"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            database='study_planner',
            user='postgres',
            password='lakshmi',
            port='5432'
        )
        conn.close()
        print("[OK] Database connection successful")
        return True
    except Exception as e:
        print(f"[WARNING] Database connection failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Selenium test runner for Study Planner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run_selenium_tests.py            # Run all tests
  python run_selenium_tests.py -v         # Verbose output
  python run_selenium_tests.py --headless # Run in headless mode
        '''
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show detailed test output')
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode (no UI)')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("SELENIUM TEST ENVIRONMENT CHECK")
    print("="*70)
    
    # Check requirements
    if not check_requirements():
        return 1
    
    print("[OK] All required packages installed")
    
    # Check database
    check_database_connection()
    
    # Check app
    if not check_app_running():
        print("\n[ERROR] Flask app must be running before starting tests")
        print("In another terminal, run: python app.py")
        return 1
    
    print("\n" + "="*70)
    print("STARTING SELENIUM TESTS")
    print("="*70 + "\n")
    
    # Import and run tests
    try:
        if args.headless:
            # Modify selenium_tests to use headless mode
            import selenium_tests
            selenium_tests.SeleniumTestBase.HEADLESS = True
        
        from selenium_tests import run_selenium_tests
        verbosity = 2 if args.verbose else 1
        success = run_selenium_tests(verbosity=verbosity)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n[INFO] Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Failed to run tests: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
