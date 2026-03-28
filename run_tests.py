#!/usr/bin/env python
"""
Test Runner Script - Runs unit tests for Study Planner Project

This comprehensive test runner executes all unit tests and generates a detailed report.
Run with: python run_tests.py
"""

import sys
import os
import unittest
from io import StringIO

# Set environment variables before importing app
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_NAME'] = 'study_planner'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASS'] = 'lakshmi'

# Suppress database connection warnings during testing
import warnings
warnings.filterwarnings("ignore")

def run_all_tests():
    """
    Discover and run all unit tests
    Returns  exit code (0 = success, 1 = failure)
    """
    
    # Discover all test files
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run with verbosity
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    
    # Print output
    output = stream.getvalue()
    print(output)
    
    # Print summary report
    print("\n" + "="*75)
    print(" "*20 + "UNIT TEST SUMMARY REPORT")
    print("="*75)
    
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    failed = len(result.failures)
    errors = len(result.errors)
    
    print(f"\nTotal Tests Run:     {total:>5}")
    print(f"✓ Passed:            {passed:>5}")
    print(f"✗ Failed:            {failed:>5}")
    print(f"✗ Errors:            {errors:>5}")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"Success Rate:        {success_rate:>5.1f}%")
    
    print("="*75)
    
    # Print test categories
    print("\nTest Coverage:")
    print("  • Authentication (Register, Login, Logout)")
    print("  • Authorization & Session Security")
    print("  • Subject Management (CRUD)")
    print("  • Study Session Management (CRUD)")
    print("  • Study Streak Calculation")
    print("  • Pomodoro Timer Access Control")
    print("  • Input Validation & Error Handling")
    print("  • Database Operations & Transactions")
    print("  • Redirects & Navigation")
    print("  • Home Page Analytics")
    
    print("\n" + "="*75)
    
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
    else:
        if failed > 0:
            print(f"\n❌ {failed} test(s) FAILED")
        if errors > 0:
            print(f"⚠️  {errors} test(s) had ERRORS")
    
    print("="*75 + "\n")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except ImportError as e:
        print(f"Error: {e}")
        print("\nMake sure to install dependencies:")
        print("  pip install Flask==3.0.0 psycopg2-binary==2.9.9 pytest")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
