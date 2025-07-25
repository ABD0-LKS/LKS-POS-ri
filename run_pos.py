#!/usr/bin/env python3
"""
Store Manager POS System
Professional Point of Sale Application

Run this script to start the POS system.
Make sure to run database_setup.py first if this is your first time.
"""

import sys
import os
import subprocess

def check_requirements():
    """Check if required packages are installed"""
    try:
        import PyQt5
        print("✓ PyQt5 is installed")
    except ImportError:
        print("✗ PyQt5 is not installed")
        print("Please install it with: pip install PyQt5")
        return False
    
    return True

def check_database():
    """Check if database exists"""
    if not os.path.exists('pos_database.db'):
        print("✗ Database not found")
        print("Creating database...")
        try:
            import database_setup
            database_setup.create_database()
            print("✓ Database created successfully")
        except Exception as e:
            print(f"✗ Failed to create database: {e}")
            return False
    else:
        print("✓ Database found")
    
    return True

def main():
    """Main function to run the POS system"""
    print("=" * 50)
    print("    STORE MANAGER POS SYSTEM")
    print("    Professional Point of Sale")
    print("=" * 50)
    print()
    
    # Check requirements
    print("Checking system requirements...")
    if not check_requirements():
        input("Press Enter to exit...")
        return
    
    # Check database
    print("Checking database...")
    if not check_database():
        input("Press Enter to exit...")
        return
    
    print()
    print("Starting POS System...")
    print("Default login: admin / admin123")
    print()
    
    # Run the main application
    try:
        import main
    except Exception as e:
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()
