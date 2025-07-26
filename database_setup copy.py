"""
Database Setup and Initialization for POS System
Creates all necessary tables and inserts sample data
"""

import sqlite3
import os
from datetime import datetime
import json

def create_database():
    """Create and initialize the POS database"""
    
    # Database file path
    db_path = "pos_database.db"
    
    # Remove existing database if it exists (for fresh start)
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    # Create new database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating database tables...")
    
    # Users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'cashier',
            full_name TEXT,
            email TEXT,
            active INTEGER DEFAULT 1,
            last_login TIMESTAMP,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code_bar TEXT UNIQUE,
            price_buy REAL DEFAULT 0.0,
            price_sell REAL NOT NULL,
            quantity INTEGER DEFAULT 0,
            category TEXT DEFAULT 'General',
            description TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Customers table
    cursor.execute('''
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_purchases REAL DEFAULT 0.0
        )
    ''')
    
    # Tickets/Sales table
    cursor.execute('''
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_price REAL NOT NULL,
            remis REAL DEFAULT 0.0,
            payment_method TEXT DEFAULT 'Cash',
            customer_name TEXT DEFAULT 'Walk-in Customer',
            items TEXT NOT NULL,
            status TEXT DEFAULT 'Completed',
            cashier_id INTEGER,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cashier_id) REFERENCES users (id)
        )
    ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Categories table
    cursor.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Suppliers table
    cursor.execute('''
        CREATE TABLE suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Barcode scans log table
    cursor.execute('''
        CREATE TABLE barcode_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL,
            product_id INTEGER,
            success BOOLEAN,
            scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    print("Inserting default data...")
    
    # Insert default users
    users_data = [
        ('admin', 'admin123', 'admin', 'System Administrator', 'admin@lksstore.com', 1),
        ('cashier', 'cashier123', 'cashier', 'Default Cashier', 'cashier@lksstore.com', 1),
        ('manager', 'manager123', 'manager', 'Store Manager', 'manager@lksstore.com', 1)
    ]
    
    cursor.executemany('''
        INSERT INTO users (username, password, role, full_name, email, active)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', users_data)
    
    # Insert default categories
    categories_data = [
        ('Beverages', 'Soft drinks, juices, water'),
        ('Food', 'Snacks, canned goods, fresh food'),
        ('Dairy', 'Milk, cheese, yogurt'),
        ('Bakery', 'Bread, pastries, cakes'),
        ('Meat', 'Fresh meat, poultry, seafood'),
        ('Fruits', 'Fresh fruits and vegetables'),
        ('Household', 'Cleaning supplies, toiletries'),
        ('Electronics', 'Small electronics, batteries'),
        ('Stationery', 'Office supplies, school items'),
        ('Health', 'Pharmacy items, first aid')
    ]
    
    cursor.executemany('''
        INSERT INTO categories (name, description)
        VALUES (?, ?)
    ''', categories_data)
    
    # Insert sample products with barcodes
    products_data = [
        ('Coca Cola 330ml', '5449000000996', 1.20, 2.50, 100, 'Beverages', 'Classic Coca Cola 330ml can'),
        ('Pepsi 330ml', '5449000001003', 1.15, 2.40, 80, 'Beverages', 'Pepsi Cola 330ml can'),
        ('Mineral Water 1.5L', '3274080005003', 0.80, 1.50, 150, 'Beverages', 'Natural mineral water 1.5L bottle'),
        ('White Bread', '3560070462014', 1.00, 2.25, 50, 'Bakery', 'Fresh white bread loaf'),
        ('Whole Milk 1L', '3033710074617', 1.50, 3.00, 60, 'Dairy', 'Fresh whole milk 1 liter'),
        ('Bananas (per kg)', '4011', 2.00, 4.50, 25, 'Fruits', 'Fresh bananas sold per kilogram'),
        ('Chicken Breast (per kg)', '2001234567890', 6.00, 12.99, 15, 'Meat', 'Fresh chicken breast per kg'),
        ('Tomatoes (per kg)', '4664', 1.80, 3.50, 30, 'Fruits', 'Fresh tomatoes per kilogram'),
        ('Cheese Slices 200g', '7622210951557', 2.50, 4.99, 40, 'Dairy', 'Processed cheese slices 200g pack'),
        ('Orange Juice 1L', '5449000131805', 2.00, 3.99, 35, 'Beverages', 'Fresh orange juice 1 liter'),
        ('Pasta 500g', '8076809513726', 1.20, 2.49, 70, 'Food', 'Italian pasta 500g package'),
        ('Rice 1kg', '8901030895562', 2.50, 4.99, 45, 'Food', 'Basmati rice 1kg bag'),
        ('Toilet Paper 4-pack', '3017760755597', 3.00, 5.99, 25, 'Household', 'Soft toilet paper 4-roll pack'),
        ('Shampoo 400ml', '3600541078239', 4.50, 8.99, 20, 'Household', 'Hair shampoo 400ml bottle'),
        ('Batteries AA 4-pack', '7638900024067', 3.50, 6.99, 30, 'Electronics', 'Alkaline AA batteries 4-pack'),
        ('Notebook A4', '4006381333634', 1.50, 2.99, 50, 'Stationery', 'A4 lined notebook 80 pages'),
        ('Pen Blue', '3086123456789', 0.50, 0.99, 100, 'Stationery', 'Blue ballpoint pen'),
        ('Aspirin 20 tablets', '4005808123456', 2.00, 3.99, 15, 'Health', 'Pain relief tablets 20-pack'),
        ('Hand Sanitizer 250ml', '1234567890123', 2.50, 4.99, 40, 'Health', 'Antibacterial hand sanitizer'),
        ('Coffee 250g', '7622210998477', 4.00, 7.99, 25, 'Beverages', 'Ground coffee 250g package')
    ]
    
    cursor.executemany('''
        INSERT INTO products (name, code_bar, price_buy, price_sell, quantity, category, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', products_data)
    
    # Insert default customers
    customers_data = [
        ('John Smith', '+1234567890', 'john.smith@email.com', '123 Main St, City'),
        ('Mary Johnson', '+1234567891', 'mary.j@email.com', '456 Oak Ave, City'),
        ('Robert Brown', '+1234567892', 'r.brown@email.com', '789 Pine St, City'),
        ('Lisa Davis', '+1234567893', 'lisa.davis@email.com', '321 Elm St, City'),
        ('Michael Wilson', '+1234567894', 'm.wilson@email.com', '654 Maple Ave, City')
    ]
    
    cursor.executemany('''
        INSERT INTO customers (name, phone, email, address)
        VALUES (?, ?, ?, ?)
    ''', customers_data)
    
    # Insert default settings
    settings_data = [
        ('store_name', 'LKS Store'),
        ('store_address', '123 Business Street, City, State 12345'),
        ('store_phone', '+1 (555) 123-4567'),
        ('store_email', 'info@lksstore.com'),
        ('currency', 'DA'),
        ('tax_rate', '19'),
        ('low_stock_threshold', '10'),
        ('receipt_footer', 'Thank you for shopping with us!\nVisit us again soon!'),
        ('backup_enabled', 'true'),
        ('print_receipt_auto', 'false'),
        ('sound_enabled', 'true'),
        ('camera_enabled', 'true'),
        ('auto_focus_enabled', 'true'),
        ('scan_timeout', '30'),
        ('duplicate_scan_prevention', 'true')
    ]
    
    cursor.executemany('''
        INSERT INTO settings (key, value)
        VALUES (?, ?)
    ''', settings_data)
    
    # Insert sample suppliers
    suppliers_data = [
        ('ABC Distributors', 'John Manager', '+1555123001', 'john@abcdist.com', '100 Warehouse Blvd'),
        ('Fresh Foods Co.', 'Sarah Supply', '+1555123002', 'sarah@freshfoods.com', '200 Farm Road'),
        ('Beverage Solutions', 'Mike Drinks', '+1555123003', 'mike@bevsol.com', '300 Liquid Lane'),
        ('Household Supplies Inc.', 'Lisa Clean', '+1555123004', 'lisa@household.com', '400 Clean Street')
    ]
    
    cursor.executemany('''
        INSERT INTO suppliers (name, contact_person, phone, email, address)
        VALUES (?, ?, ?, ?, ?)
    ''', suppliers_data)
    
    # Insert some sample sales data
    sample_sales = [
        {
            'ticket_number': 'TKT000001',
            'total_price': 15.47,
            'customer_name': 'John Smith',
            'items': [
                {'name': 'Coca Cola 330ml', 'quantity': 2, 'price': 2.50, 'total': 5.00},
                {'name': 'White Bread', 'quantity': 1, 'price': 2.25, 'total': 2.25},
                {'name': 'Whole Milk 1L', 'quantity': 1, 'price': 3.00, 'total': 3.00},
                {'name': 'Bananas (per kg)', 'quantity': 1, 'price': 4.50, 'total': 4.50},
                {'name': 'Pen Blue', 'quantity': 1, 'price': 0.99, 'total': 0.99}
            ],
            'cashier_id': 2
        },
        {
            'ticket_number': 'TKT000002',
            'total_price': 23.96,
            'customer_name': 'Mary Johnson',
            'items': [
                {'name': 'Chicken Breast (per kg)', 'quantity': 1, 'price': 12.99, 'total': 12.99},
                {'name': 'Tomatoes (per kg)', 'quantity': 2, 'price': 3.50, 'total': 7.00},
                {'name': 'Orange Juice 1L', 'quantity': 1, 'price': 3.99, 'total': 3.99}
            ],
            'cashier_id': 2
        }
    ]
    
    for sale in sample_sales:
        cursor.execute('''
            INSERT INTO tickets (ticket_number, total_price, customer_name, items, cashier_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            sale['ticket_number'],
            sale['total_price'],
            sale['customer_name'],
            json.dumps(sale['items']),
            sale['cashier_id']
        ))
    
    # Commit all changes
    conn.commit()
    
    print(f"Database created successfully: {db_path}")
    print(f"Total users: {len(users_data)}")
    print(f"Total products: {len(products_data)}")
    print(f"Total customers: {len(customers_data)}")
    print(f"Total categories: {len(categories_data)}")
    print(f"Total suppliers: {len(suppliers_data)}")
    print(f"Sample sales: {len(sample_sales)}")
    
    # Close connection
    conn.close()
    
    return db_path

def verify_database(db_path):
    """Verify database was created correctly"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\nDatabase verification for: {db_path}")
        print(f"Tables created: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} records")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database verification failed: {e}")
        return False

if __name__ == "__main__":
    # Create the database
    db_path = create_database()
    
    # Verify it was created correctly
    verify_database(db_path)
    
    print("\nDatabase setup complete!")
    print("You can now run the POS application with: python main.py")
    print("\nDefault login credentials:")
    print("  Admin: admin / admin123")
    print("  Cashier: cashier / cashier123")
    print("  Manager: manager / manager123")
