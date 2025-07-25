import sqlite3
import os
from datetime import datetime

def create_database():
    """Create and initialize the POS database"""
    
    # Remove existing database if it exists
    if os.path.exists('pos_database.db'):
        os.remove('pos_database.db')
    
    # Create new database
    conn = sqlite3.connect('pos_database.db')
    cursor = conn.cursor()
    
    # Create tables
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
            created_date TEXT,
            last_login TEXT
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code_bar TEXT,
            price_buy REAL DEFAULT 0,
            price_sell REAL NOT NULL,
            quantity INTEGER DEFAULT 0,
            category TEXT DEFAULT 'General',
            created_date TEXT,
            updated_date TEXT
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
            created_date TEXT,
            total_purchases REAL DEFAULT 0
        )
    ''')
    
    # Tickets table
    cursor.execute('''
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE,
            date TEXT NOT NULL,
            total_price REAL NOT NULL,
            remis REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'Cash',
            customer_name TEXT,
            items TEXT,
            status TEXT DEFAULT 'Completed',
            cashier_id INTEGER,
            FOREIGN KEY (cashier_id) REFERENCES users (id)
        )
    ''')
    
    # Sales table
    cursor.execute('''
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            total_price REAL,
            date TEXT,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            description TEXT
        )
    ''')
    
    # Daily reports table
    cursor.execute('''
        CREATE TABLE daily_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            total_sales REAL DEFAULT 0,
            total_transactions INTEGER DEFAULT 0,
            total_items_sold INTEGER DEFAULT 0,
            created_date TEXT
        )
    ''')
    
    print("Inserting sample data...")
    
    # Insert default admin user
    cursor.execute('''
        INSERT INTO users (username, password, role, full_name, email, created_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('admin', 'admin123', 'admin', 'System Administrator', 'admin@store.com', datetime.now().isoformat()))
    
    # Insert sample products
    sample_products = [
        ('Coca Cola 330ml', '1234567890123', 25.0, 35.0, 50, 'Beverages'),
        ('Bread', '2345678901234', 15.0, 25.0, 30, 'Bakery'),
        ('Milk 1L', '3456789012345', 45.0, 60.0, 25, 'Dairy'),
        ('Rice 1kg', '4567890123456', 80.0, 120.0, 40, 'Grains'),
        ('Chicken 1kg', '5678901234567', 350.0, 450.0, 15, 'Meat'),
        ('Tomatoes 1kg', '6789012345678', 60.0, 90.0, 20, 'Vegetables'),
        ('Apples 1kg', '7890123456789', 120.0, 180.0, 18, 'Fruits'),
        ('Shampoo', '8901234567890', 180.0, 250.0, 12, 'Personal Care'),
        ('Soap', '9012345678901', 35.0, 50.0, 25, 'Personal Care'),
        ('Pasta 500g', '0123456789012', 45.0, 70.0, 35, 'Grains')
    ]
    
    for product in sample_products:
        cursor.execute('''
            INSERT INTO products (name, code_bar, price_buy, price_sell, quantity, category, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (*product, datetime.now().isoformat()))
    
    # Insert sample customers
    sample_customers = [
        ('Ahmed Benali', '0555123456', 'ahmed@email.com', '123 Main St, Algiers'),
        ('Fatima Khelil', '0666789012', 'fatima@email.com', '456 Oak Ave, Oran'),
        ('Mohamed Saidi', '0777345678', 'mohamed@email.com', '789 Pine Rd, Constantine'),
        ('Amina Bouazza', '0888901234', 'amina@email.com', '321 Elm St, Annaba'),
        ('Youssef Hamdi', '0999567890', 'youssef@email.com', '654 Cedar Blvd, Setif')
    ]
    
    for customer in sample_customers:
        cursor.execute('''
            INSERT INTO customers (name, phone, email, address, created_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (*customer, datetime.now().isoformat()))
    
    # Insert system settings
    settings = [
        ('store_name', 'Smart Store', 'Store name'),
        ('store_address', '123 Business Street, Algiers, Algeria', 'Store address'),
        ('store_phone', '+213 555 123 456', 'Store phone number'),
        ('store_email', 'info@smartstore.dz', 'Store email'),
        ('currency', 'DA', 'Currency symbol'),
        ('tax_rate', '19', 'Tax rate percentage'),
        ('receipt_footer', 'Thank you for shopping with us!', 'Receipt footer message'),
        ('low_stock_threshold', '10', 'Low stock alert threshold')
    ]
    
    for setting in settings:
        cursor.execute('''
            INSERT INTO settings (key, value, description)
            VALUES (?, ?, ?)
        ''', setting)
    
    # Insert sample tickets for demo
    sample_tickets = [
        ('TKT000001', datetime.now().isoformat(), 155.0, 0, 'Cash', 'Ahmed Benali', 
         '[{"name": "Coca Cola 330ml", "quantity": 2, "price": 35.0, "total": 70.0}, {"name": "Bread", "quantity": 1, "price": 25.0, "total": 25.0}, {"name": "Milk 1L", "quantity": 1, "price": 60.0, "total": 60.0}]'),
        ('TKT000002', datetime.now().isoformat(), 270.0, 0, 'Cash', 'Walk-in Customer',
         '[{"name": "Rice 1kg", "quantity": 1, "price": 120.0, "total": 120.0}, {"name": "Chicken 1kg", "quantity": 1, "price": 450.0, "total": 450.0}]')
    ]
    
    for ticket in sample_tickets:
        cursor.execute('''
            INSERT INTO tickets (ticket_number, date, total_price, remis, payment_method, customer_name, items, status, cashier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (*ticket, 'Completed', 1))
    
    conn.commit()
    conn.close()
    
    print("Database created successfully!")
    print("Default login: admin / admin123")

if __name__ == '__main__':
    create_database()
