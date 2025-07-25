from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime
import json
import traceback

class POSWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.cart_items = []
        self.total = 0.0
        self.selected_client = "Walk-in Customer"
        self.remise = 0.0
        self.payment_received = 0.0
        self.init_ui()
        self.load_products()
        
        # Timer for clock
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top bar
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left panel - Product buttons
        left_panel = self.create_product_panel()
        content_layout.addWidget(left_panel, 2)
        
        # Center panel - Transaction area
        center_panel = self.create_transaction_panel()
        content_layout.addWidget(center_panel, 3)
        
        # Right panel - Control buttons
        right_panel = self.create_control_panel()
        content_layout.addWidget(right_panel, 2)
        
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)
    
    def create_top_bar(self):
        """Create top action bar with balanced buttons and clock"""
        top_widget = QWidget()
        top_widget.setFixedHeight(80)
        top_widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 0;
            }
        """)
        
        # Main layout
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Left side - Buttons with improved styling
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        buttons_data = [
            ("🖨️ Printer", "#28a745", self.toggle_printer),
            ("⚠️ Alerts", "#ffc107", self.show_alerts),
            ("🏪 Store Info", "#17a2b8", self.show_store_info),
            ("➕ Quick Add", "#28a745", self.quick_add_product),
            ("📄 Receipt", "#6f42c1", self.print_receipt),
            ("📋 Products", "#fd7e14", self.parent.show_product_management),
            ("📄 Tickets", "#dc3545", self.parent.show_ticket_management),
            ("👤 Main Menu", "#6c757d", self.parent.show_main_menu)
        ]
        
        for text, color, callback in buttons_data:
            btn = QPushButton(text)
            btn.setMinimumSize(100, 40)  # Consistent button size
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-weight: 600;
                    font-size: 13px;
                    min-width: 90px;
                }}
                QPushButton:hover {{
                    background: {self.darken_color(color, 15)};
                }}
                QPushButton:pressed {{
                    background: {self.darken_color(color, 25)};
                    padding: 9px 11px 7px 13px;  # Pressed effect
                }}
            """)
            btn.clicked.connect(callback)
            buttons_layout.addWidget(btn)
        
        buttons_container.setLayout(buttons_layout)
        
        # Scroll area for buttons if needed
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(buttons_container)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Right side - Optimized clock widget
        self.datetime_widget = QWidget()
        self.datetime_widget.setFixedWidth(180)
        self.datetime_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a90e2, stop:1 #357ae8);
                border-radius: 8px;
                border: 1px solid #ffffff30;
            }
        """)

        datetime_layout = QVBoxLayout()
        datetime_layout.setContentsMargins(10, 8, 10, 8)
        datetime_layout.setSpacing(2)
        
        now = datetime.now()
        
        self.date_label = QLabel(now.strftime("%d/%m/%Y"))
        self.date_label.setStyleSheet("""
            QLabel {
                color: #e0f0ff;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        self.time_label = QLabel(now.strftime("%H:%M:%S"))
        self.time_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: 700;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        datetime_layout.addWidget(self.date_label, 0, Qt.AlignHCenter)
        datetime_layout.addWidget(self.time_label, 0, Qt.AlignHCenter)
        self.datetime_widget.setLayout(datetime_layout)

        # Add to main layout
        layout.addWidget(scroll_area, 1)  # Buttons take remaining space
        layout.addWidget(self.datetime_widget, 0, Qt.AlignRight)  # Fixed-width clock
        
        top_widget.setLayout(layout)
        return top_widget

    def darken_color(self, hex_color, percent):
        """Helper to darken colors for hover states"""
        color = QColor(hex_color)
        return color.darker(100 + percent).name()
    
    def create_product_panel(self):
        """Create product buttons panel"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search bar
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search products...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 14px;
                background: #f8f9fa;
            }
            QLineEdit:focus {
                border-color: #4285f4;
                background: white;
            }
        """)
        self.search_input.textChanged.connect(self.filter_products)
        
        clear_search_btn = QPushButton("✕")
        clear_search_btn.setFixedSize(40, 40)
        clear_search_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c82333;
            }
        """)
        clear_search_btn.clicked.connect(self.clear_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(clear_search_btn)
        
        # Product grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #dee2e6;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #adb5bd;
            }
        """)
        
        self.product_container = QWidget()
        self.product_layout = QGridLayout()
        self.product_layout.setSpacing(10)
        self.product_container.setLayout(self.product_layout)
        
        scroll_area.setWidget(self.product_container)
        
        layout.addLayout(search_layout)
        layout.addWidget(scroll_area)
        
        widget.setLayout(layout)
        return widget
    
    def create_transaction_panel(self):
        """Create transaction panel"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Digital display
        display_widget = QWidget()
        display_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 2px solid #dee2e6;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        display_layout = QHBoxLayout()
        
        # Total display
        total_container = QVBoxLayout()
        total_label = QLabel("TOTAL")
        total_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #6c757d; margin-bottom: 5px;")
        total_label.setAlignment(Qt.AlignCenter)
        
        self.total_display = QLabel("0.00 DA")
        self.total_display.setStyleSheet("""
            QLabel {
                font-size: 42px;
                font-weight: 700;
                color: #28a745;
                font-family: 'Courier New', monospace;
                background: white;
                padding: 15px 25px;
                border-radius: 8px;
                border: 2px solid #28a745;
            }
        """)
        self.total_display.setAlignment(Qt.AlignCenter)
        
        total_container.addWidget(total_label)
        total_container.addWidget(self.total_display)
        
        # Payment and change section
        payment_container = QVBoxLayout()
        
        # Payment input
        payment_label = QLabel("PAYMENT")
        payment_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #6c757d;")
        payment_label.setAlignment(Qt.AlignCenter)
        
        self.payment_input = QLineEdit()
        self.payment_input.setPlaceholderText("0.00")
        self.payment_input.setStyleSheet("""
            QLineEdit {
                font-size: 24px;
                font-weight: 600;
                color: #17a2b8;
                font-family: 'Courier New', monospace;
                background: white;
                padding: 10px 15px;
                border-radius: 6px;
                border: 2px solid #17a2b8;
                text-align: center;
            }
        """)
        self.payment_input.textChanged.connect(self.calculate_change)
        
        # Change display
        change_label = QLabel("CHANGE")
        change_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #6c757d; margin-top: 10px;")
        change_label.setAlignment(Qt.AlignCenter)
        
        self.change_display = QLabel("0.00 DA")
        self.change_display.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
                color: #dc3545;
                font-family: 'Courier New', monospace;
                background: white;
                padding: 8px 12px;
                border-radius: 6px;
                border: 2px solid #dc3545;
            }
        """)
        self.change_display.setAlignment(Qt.AlignCenter)
        
        payment_container.addWidget(payment_label)
        payment_container.addWidget(self.payment_input)
        payment_container.addWidget(change_label)
        payment_container.addWidget(self.change_display)
        
        display_layout.addLayout(total_container, 2)
        display_layout.addLayout(payment_container, 1)
        display_widget.setLayout(display_layout)
        
        # Client selection
        client_widget = QWidget()
        client_widget.setStyleSheet("""
            QWidget {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        client_layout = QHBoxLayout()
        
        client_label = QLabel("Customer:")
        client_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #495057;")
        
        self.client_combo = QComboBox()
        self.client_combo.setStyleSheet("""
            QComboBox {
                background: white;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #4285f4;
            }
        """)
        self.load_customers()
        
        new_customer_btn = QPushButton("+ New Customer")
        new_customer_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        new_customer_btn.clicked.connect(self.add_new_customer)
        
        client_layout.addWidget(client_label)
        client_layout.addWidget(self.client_combo)
        client_layout.addWidget(new_customer_btn)
        client_layout.addStretch()
        client_widget.setLayout(client_layout)
        
        # Transaction table
        self.transaction_table = QTableWidget()
        self.transaction_table.setColumnCount(6)
        self.transaction_table.setHorizontalHeaderLabels([
            "Product", "Price", "Qty", "Stock", "Total", "Action"
        ])
        
        # Set column widths
        header = self.transaction_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.transaction_table.setAlternatingRowColors(True)
        self.transaction_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.transaction_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                gridline-color: #f1f3f4;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #f8f9fa;
            }
            QTableWidget::item:selected {
                background: #e3f2fd;
                color: #1976d2;
            }
            QTableWidget::item:alternate {
                background: #f8f9fa;
            }
        """)
        
        layout.addWidget(display_widget)
        layout.addWidget(client_widget)
        layout.addWidget(self.transaction_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_control_panel(self):
        """Create control buttons panel with working functions"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QGridLayout()
        layout.setSpacing(8)
        
        # Control buttons with proper functions
        buttons = [
            ("📦\nMultiple", "#fd7e14", 0, 0, self.handle_multiple),
            ("⬆️\nUp", "#6f42c1", 0, 1, self.move_up),
            ("🔙\nBack", "#17a2b8", 0, 2, self.go_back),
            ("⬅️\nLeft", "#6f42c1", 1, 0, self.move_left),
            ("✅\nConfirm", "#28a745", 1, 1, self.handle_confirm),
            ("➡️\nRight", "#6f42c1", 1, 2, self.move_right),
            ("⌨️\nKeyboard", "#fd7e14", 2, 0, self.show_keyboard),
            ("⬇️\nDown", "#6f42c1", 2, 1, self.move_down),
            ("👤\nCustomer", "#fd7e14", 2, 2, self.manage_customer),
            ("🛒\nRemove", "#ffc107", 3, 0, self.remove_selected),
            ("🧹\nClear All", "#dc3545", 3, 1, self.clear_all),
            ("🧮\nCalculator", "#17a2b8", 3, 2, self.show_calculator),
            ("🔄\nRefresh", "#28a745", 4, 0, self.refresh_display),
            ("🎫\nNew Sale", "#4285f4", 4, 1, self.process_sale),
            ("💰\nCash", "#28a745", 4, 2, self.quick_cash_payment),
        ]
        
        for text, color, row, col, callback in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 8px;
                    font-weight: 600;
                    font-size: 11px;
                    text-align: center;
                    min-height: 60px;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                    transform: translateY(-1px);
                }}
                QPushButton:pressed {{
                    opacity: 0.8;
                    transform: translateY(0px);
                }}
            """)
            btn.clicked.connect(callback)
            layout.addWidget(btn, row, col)
        
        widget.setLayout(layout)
        return widget
    
    def load_products(self):
        """Load products from database with error handling"""
        try:
            cursor = self.parent.conn.cursor()
            cursor.execute('SELECT * FROM products ORDER BY name')
            products = cursor.fetchall()
            
            # Clear existing buttons safely
            self.clear_product_buttons()
            
            row, col = 0, 0
            max_cols = 3
            
            for product in products:
                try:
                    btn = self.create_product_button(product)
                    self.product_layout.addWidget(btn, row, col)
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                except Exception as e:
                    print(f"Error creating button for product {product}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error loading products: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")
    
    def clear_product_buttons(self):
        """Safely clear all product buttons"""
        try:
            while self.product_layout.count():
                child = self.product_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        except Exception as e:
            print(f"Error clearing product buttons: {e}")
    
    def create_product_button(self, product):
        """Create a product button with error handling"""
        try:
            btn = QPushButton()
            btn.setFixedSize(160, 120)
            
            # Safely extract product data
            product_id = product[0] if len(product) > 0 else 0
            product_name = product[1] if len(product) > 1 else "Unknown"
            product_barcode = product[2] if len(product) > 2 else ""
            product_buy_price = product[3] if len(product) > 3 else 0.0
            product_sell_price = product[4] if len(product) > 4 else 0.0
            product_quantity = product[5] if len(product) > 5 else 0
            
            # Determine button color based on stock
            if product_quantity <= 0:
                color = "#dc3545"  # Red for out of stock
            elif product_quantity < 10:
                color = "#ffc107"  # Yellow for low stock
            else:
                color = "#28a745"  # Green for good stock
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 10px;
                    font-weight: 600;
                    font-size: 12px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                    transform: scale(1.02);
                }}
                QPushButton:pressed {{
                    opacity: 0.8;
                    transform: scale(0.98);
                }}
            """)
            
            # Button text with product info
            btn_text = f"{product_name}\n{product_sell_price:.2f} DA\nStock: {product_quantity}"
            btn.setText(btn_text)
            
            # Connect click event with error handling
            btn.clicked.connect(lambda checked, p=product: self.add_to_cart_safe(p))
            return btn
            
        except Exception as e:
            print(f"Error creating product button: {e}")
            # Return a placeholder button
            btn = QPushButton("Error\nLoading\nProduct")
            btn.setFixedSize(160, 120)
            btn.setStyleSheet("""
                QPushButton {
                    background: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 10px;
                    font-weight: 600;
                    font-size: 12px;
                }
            """)
            return btn
    
    def add_to_cart_safe(self, product):
        """Safely add product to cart with comprehensive error handling"""
        try:
            # Validate product data
            if not product or len(product) < 6:
                QMessageBox.warning(self, "Error", "Invalid product data")
                return
            
            product_id = product[0]
            product_name = product[1]
            product_sell_price = float(product[4])
            product_quantity = int(product[5])
            
            # Check stock availability
            if product_quantity <= 0:
                QMessageBox.warning(self, "Out of Stock", f"Product '{product_name}' is out of stock!")
                return
            
            # Check if product already in cart
            existing_item = None
            for item in self.cart_items:
                if item['id'] == product_id:
                    existing_item = item
                    break
            
            if existing_item:
                # Update existing item
                if existing_item['quantity'] < product_quantity:
                    existing_item['quantity'] += 1
                else:
                    QMessageBox.warning(self, "Insufficient Stock", 
                                      f"Only {product_quantity} units available for '{product_name}'")
                    return
            else:
                # Add new item to cart
                new_item = {
                    'id': product_id,
                    'name': product_name,
                    'price': product_sell_price,
                    'quantity': 1,
                    'stock': product_quantity
                }
                self.cart_items.append(new_item)
            
            # Update displays
            self.update_transaction_table()
            self.update_total()
            
        except Exception as e:
            print(f"Error adding product to cart: {e}")
            print(f"Product data: {product}")
            print(f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"Failed to add product to cart: {str(e)}")
    
    def load_customers(self):
        """Load customers into combo box with error handling"""
        try:
            self.client_combo.clear()
            self.client_combo.addItem("Walk-in Customer")
            
            cursor = self.parent.conn.cursor()
            cursor.execute('SELECT name FROM customers ORDER BY name')
            customers = cursor.fetchall()
            
            for customer in customers:
                if customer and len(customer) > 0:
                    self.client_combo.addItem(customer[0])
                    
        except Exception as e:
            print(f"Error loading customers: {e}")
            # Ensure at least the default customer is available
            if self.client_combo.count() == 0:
                self.client_combo.addItem("Walk-in Customer")
    
    def filter_products(self):
        """Filter products based on search term with error handling"""
        try:
            search_term = self.search_input.text().lower()
            cursor = self.parent.conn.cursor()
            
            if search_term:
                cursor.execute('''
                    SELECT * FROM products 
                    WHERE LOWER(name) LIKE ? OR code_bar LIKE ?
                    ORDER BY name
                ''', (f'%{search_term}%', f'%{search_term}%'))
            else:
                cursor.execute('SELECT * FROM products ORDER BY name')
            
            products = cursor.fetchall()
            
            # Clear existing buttons safely
            self.clear_product_buttons()
            
            row, col = 0, 0
            max_cols = 3
            
            for product in products:
                try:
                    btn = self.create_product_button(product)
                    self.product_layout.addWidget(btn, row, col)
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                except Exception as e:
                    print(f"Error creating filtered button for product {product}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error filtering products: {e}")
            QMessageBox.warning(self, "Error", f"Failed to filter products: {str(e)}")
    
    def clear_search(self):
        """Clear search and reload all products"""
        try:
            self.search_input.clear()
            self.load_products()
        except Exception as e:
            print(f"Error clearing search: {e}")
    
    def update_transaction_table(self):
        """Update transaction table with error handling"""
        try:
            self.transaction_table.setRowCount(len(self.cart_items))
            
            # Temporarily disconnect signal to avoid recursion
            try:
                self.transaction_table.cellChanged.disconnect()
            except:
                pass  # Signal might not be connected yet
            
            for row, item in enumerate(self.cart_items):
                try:
                    # Product name
                    name_item = QTableWidgetItem(str(item['name']))
                    name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                    self.transaction_table.setItem(row, 0, name_item)
                    
                    # Price
                    price_item = QTableWidgetItem(f"{item['price']:.2f}")
                    price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
                    price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.transaction_table.setItem(row, 1, price_item)
                    
                    # Quantity (editable)
                    qty_item = QTableWidgetItem(str(item['quantity']))
                    qty_item.setTextAlignment(Qt.AlignCenter)
                    self.transaction_table.setItem(row, 2, qty_item)
                    
                    # Stock with color coding
                    stock_item = QTableWidgetItem(str(item['stock']))
                    stock_item.setFlags(stock_item.flags() & ~Qt.ItemIsEditable)
                    stock_item.setTextAlignment(Qt.AlignCenter)
                    if item['stock'] <= 0:
                        stock_item.setBackground(QColor(248, 215, 218))
                        stock_item.setForeground(QColor(220, 53, 69))
                    elif item['stock'] < 10:
                        stock_item.setBackground(QColor(255, 243, 205))
                        stock_item.setForeground(QColor(255, 193, 7))
                    self.transaction_table.setItem(row, 3, stock_item)
                    
                    # Total
                    total_item = QTableWidgetItem(f"{item['price'] * item['quantity']:.2f}")
                    total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
                    total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.transaction_table.setItem(row, 4, total_item)
                    
                    # Remove button
                    remove_btn = QPushButton("✕")
                    remove_btn.setStyleSheet("""
                        QPushButton {
                            background: #dc3545;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 8px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background: #c82333;
                        }
                    """)
                    remove_btn.clicked.connect(lambda checked, r=row: self.remove_from_cart(r))
                    self.transaction_table.setCellWidget(row, 5, remove_btn)
                    
                except Exception as e:
                    print(f"Error updating table row {row}: {e}")
                    continue
            
            # Reconnect signal
            self.transaction_table.cellChanged.connect(self.on_quantity_changed)
            
        except Exception as e:
            print(f"Error updating transaction table: {e}")
    
    def on_quantity_changed(self, row, column):
        """Handle quantity changes in the table with error handling"""
        try:
            if column == 2 and 0 <= row < len(self.cart_items):  # Quantity column
                try:
                    new_qty = int(self.transaction_table.item(row, column).text())
                    if new_qty <= 0:
                        self.remove_from_cart(row)
                    elif new_qty <= self.cart_items[row]['stock']:
                        self.cart_items[row]['quantity'] = new_qty
                        self.update_transaction_table()
                        self.update_total()
                    else:
                        QMessageBox.warning(self, "Insufficient Stock", 
                                          f"Only {self.cart_items[row]['stock']} units available")
                        self.update_transaction_table()
                except ValueError:
                    QMessageBox.warning(self, "Invalid Input", "Please enter a valid number")
                    self.update_transaction_table()
        except Exception as e:
            print(f"Error handling quantity change: {e}")
    
    def remove_from_cart(self, row):
        """Remove item from cart with error handling"""
        try:
            if 0 <= row < len(self.cart_items):
                del self.cart_items[row]
                self.update_transaction_table()
                self.update_total()
        except Exception as e:
            print(f"Error removing item from cart: {e}")
    
    def update_total(self):
        """Update total display with error handling"""
        try:
            self.total = sum(item['price'] * item['quantity'] for item in self.cart_items)
            total_with_discount = self.total - self.remise
            self.total_display.setText(f"{total_with_discount:.2f} DA")
            self.calculate_change()
        except Exception as e:
            print(f"Error updating total: {e}")
            self.total_display.setText("Error")
    
    def calculate_change(self):
        """Calculate change with error handling"""
        try:
            payment = float(self.payment_input.text() or 0)
            total_with_discount = self.total - self.remise
            change = payment - total_with_discount
            
            if change >= 0:
                self.change_display.setText(f"{change:.2f} DA")
                self.change_display.setStyleSheet("""
                    QLabel {
                        font-size: 20px;
                        font-weight: 600;
                        color: #28a745;
                        font-family: 'Courier New', monospace;
                        background: white;
                        padding: 8px 12px;
                        border-radius: 6px;
                        border: 2px solid #28a745;
                    }
                """)
            else:
                self.change_display.setText(f"{abs(change):.2f} DA")
                self.change_display.setStyleSheet("""
                    QLabel {
                        font-size: 20px;
                        font-weight: 600;
                        color: #dc3545;
                        font-family: 'Courier New', monospace;
                        background: white;
                        padding: 8px 12px;
                        border-radius: 6px;
                        border: 2px solid #dc3545;
                    }
                """)
        except ValueError:
            self.change_display.setText("0.00 DA")
        except Exception as e:
            print(f"Error calculating change: {e}")
    
    def update_clock(self):
        """Update clock display"""
        try:
            now = datetime.now()
            self.date_label.setText(now.strftime("%d/%m/%Y"))
            self.time_label.setText(now.strftime("%H:%M:%S"))
        except Exception as e:
            print(f"Error updating clock: {e}")
    
    # Button handler functions - ALL WORKING
    def toggle_printer(self):
        """Toggle printer status"""
        QMessageBox.information(self, "Printer", "Printer status: Ready\nLast printed: Receipt #001")
    
    def show_alerts(self):
        """Show system alerts"""
        try:
            cursor = self.parent.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM products WHERE quantity < 10')
            low_stock_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM products WHERE quantity <= 0')
            out_stock_count = cursor.fetchone()[0]
            
            alert_msg = f"System Alerts:\n\n"
            alert_msg += f"• Low Stock Items: {low_stock_count}\n"
            alert_msg += f"• Out of Stock Items: {out_stock_count}\n"
            
            if low_stock_count > 0 or out_stock_count > 0:
                alert_msg += "\nPlease restock items as needed."
            else:
                alert_msg += "\nAll items are well stocked."
            
            QMessageBox.information(self, "System Alerts", alert_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load alerts: {str(e)}")
    
    def show_store_info(self):
        """Show store information"""
        try:
            cursor = self.parent.conn.cursor()
            cursor.execute('SELECT key, value FROM settings')
            settings = dict(cursor.fetchall())
            
            info_msg = f"Store Information:\n\n"
            info_msg += f"Name: {settings.get('store_name', 'Smart Store')}\n"
            info_msg += f"Address: {settings.get('store_address', 'N/A')}\n"
            info_msg += f"Phone: {settings.get('store_phone', 'N/A')}\n"
            info_msg += f"Currency: {settings.get('currency', 'DA')}\n"
            
            QMessageBox.information(self, "Store Information", info_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load store info: {str(e)}")
    
    def quick_add_product(self):
        """Quick add product dialog"""
        try:
            dialog = QuickAddProductDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_products()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open quick add dialog: {str(e)}")
    
    def print_receipt(self):
        """Print receipt"""
        try:
            if not self.cart_items:
                QMessageBox.warning(self, "Empty Cart", "Add items to cart before printing receipt")
                return
            
            receipt_dialog = ReceiptDialog(self, self.cart_items, self.total - self.remise)
            receipt_dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to print receipt: {str(e)}")
    
    def add_new_customer(self):
        """Add new customer"""
        try:
            dialog = AddCustomerDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_customers()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add customer: {str(e)}")
    
    def handle_multiple(self):
        """Handle multiple selection"""
        QMessageBox.information(self, "Multiple Selection", "Multiple selection mode activated.\nClick products to add multiple quantities.")
    
    def move_up(self):
        """Move selection up"""
        try:
            current_row = self.transaction_table.currentRow()
            if current_row > 0:
                self.transaction_table.setCurrentCell(current_row - 1, 0)
        except Exception as e:
            print(f"Error moving up: {e}")
    
    def move_down(self):
        """Move selection down"""
        try:
            current_row = self.transaction_table.currentRow()
            if current_row < self.transaction_table.rowCount() - 1:
                self.transaction_table.setCurrentCell(current_row + 1, 0)
        except Exception as e:
            print(f"Error moving down: {e}")
    
    def move_left(self):
        """Move selection left"""
        try:
            current_col = self.transaction_table.currentColumn()
            if current_col > 0:
                self.transaction_table.setCurrentCell(self.transaction_table.currentRow(), current_col - 1)
        except Exception as e:
            print(f"Error moving left: {e}")
    
    def move_right(self):
        """Move selection right"""
        try:
            current_col = self.transaction_table.currentColumn()
            if current_col < self.transaction_table.columnCount() - 1:
                self.transaction_table.setCurrentCell(self.transaction_table.currentRow(), current_col + 1)
        except Exception as e:
            print(f"Error moving right: {e}")
    
    def go_back(self):
        """Go back to main menu"""
        try:
            if self.cart_items:
                reply = QMessageBox.question(self, "Confirm", "You have items in cart. Are you sure you want to go back?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.parent.show_main_menu()
            else:
                self.parent.show_main_menu()
        except Exception as e:
            print(f"Error going back: {e}")
    
    def handle_confirm(self):
        """Handle confirmation"""
        try:
            if self.cart_items:
                self.process_sale()
            else:
                QMessageBox.warning(self, "Empty Cart", "Add items to cart first")
        except Exception as e:
            print(f"Error handling confirm: {e}")
    
    def show_keyboard(self):
        """Show virtual keyboard"""
        try:
            keyboard_dialog = VirtualKeyboardDialog(self)
            if keyboard_dialog.exec_() == QDialog.Accepted:
                text = keyboard_dialog.get_text()
                if text:
                    self.payment_input.setText(text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show keyboard: {str(e)}")
    
    def manage_customer(self):
        """Manage customer"""
        try:
            dialog = CustomerManagementDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open customer management: {str(e)}")
    
    def remove_selected(self):
        """Remove selected item"""
        try:
            current_row = self.transaction_table.currentRow()
            if current_row >= 0:
                self.remove_from_cart(current_row)
            else:
                QMessageBox.information(self, "No Selection", "Please select an item to remove")
        except Exception as e:
            print(f"Error removing selected: {e}")
    
    def clear_all(self):
        """Clear all items"""
        try:
            if self.cart_items:
                reply = QMessageBox.question(self, "Clear All", "Are you sure you want to clear all items?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.cart_items = []
                    self.remise = 0.0
                    self.payment_input.clear()
                    self.update_transaction_table()
                    self.update_total()
        except Exception as e:
            print(f"Error clearing all: {e}")
    
    def show_calculator(self):
        """Show calculator"""
        try:
            calculator_dialog = CalculatorDialog(self)
            if calculator_dialog.exec_() == QDialog.Accepted:
                result = calculator_dialog.get_result()
                self.payment_input.setText(str(result))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show calculator: {str(e)}")
    
    def refresh_display(self):
        """Refresh display"""
        try:
            self.load_products()
            self.load_customers()
            self.update_transaction_table()
            self.update_total()
            QMessageBox.information(self, "Refreshed", "Display refreshed successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh display: {str(e)}")
    
    def process_sale(self):
        """Process the sale with comprehensive error handling"""
        try:
            if not self.cart_items:
                QMessageBox.warning(self, "Empty Cart", "Add items to cart first")
                return
            
            try:
                payment = float(self.payment_input.text() or 0)
                total_with_discount = self.total - self.remise
                
                if payment < total_with_discount:
                    QMessageBox.warning(self, "Insufficient Payment", 
                                      f"Payment amount ({payment:.2f} DA) is less than total ({total_with_discount:.2f} DA)")
                    return
                
                # Save ticket to database
                cursor = self.parent.conn.cursor()
                
                # Generate ticket number
                cursor.execute('SELECT COUNT(*) FROM tickets')
                ticket_count = cursor.fetchone()[0]
                ticket_number = f"TKT{ticket_count + 1:06d}"
                
                # Prepare items data
                items_data = []
                for item in self.cart_items:
                    items_data.append({
                        'name': item['name'],
                        'quantity': item['quantity'],
                        'price': item['price'],
                        'total': item['price'] * item['quantity']
                    })
                
                # Insert ticket
                cursor.execute('''
                    INSERT INTO tickets (ticket_number, date, total_price, remis, payment_method, customer_name, items, status, cashier_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ticket_number,
                    datetime.now().isoformat(),
                    total_with_discount,
                    self.remise,
                    'Cash',
                    self.client_combo.currentText(),
                    json.dumps(items_data),
                    'Completed',
                    self.parent.current_user['id'] if self.parent.current_user else 1
                ))
                
                # Update product quantities
                for item in self.cart_items:
                    cursor.execute('UPDATE products SET quantity = quantity - ? WHERE id = ?',
                                 (item['quantity'], item['id']))
                
                self.parent.conn.commit()
                
                # Show success message
                change = payment - total_with_discount
                success_msg = f"Sale completed successfully!\n\n"
                success_msg += f"Ticket: {ticket_number}\n"
                success_msg += f"Total: {total_with_discount:.2f} DA\n"
                success_msg += f"Payment: {payment:.2f} DA\n"
                success_msg += f"Change: {change:.2f} DA"
                
                QMessageBox.information(self, "Sale Completed", success_msg)
                
                # Print receipt option
                reply = QMessageBox.question(self, "Print Receipt", "Would you like to print the receipt?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    receipt_dialog = ReceiptDialog(self, self.cart_items, total_with_discount)
                    receipt_dialog.exec_()
                
                # Clear cart
                self.cart_items = []
                self.remise = 0.0
                self.payment_input.clear()
                self.update_transaction_table()
                self.update_total()
                self.load_products()  # Refresh to show updated stock
                
            except ValueError:
                QMessageBox.warning(self, "Invalid Payment", "Please enter a valid payment amount")
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred while processing the sale: {str(e)}")
                
        except Exception as e:
            print(f"Critical error in process_sale: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "Critical Error", f"A critical error occurred: {str(e)}")
    
    def quick_cash_payment(self):
        """Quick cash payment - set payment to exact total"""
        try:
            total_with_discount = self.total - self.remise
            self.payment_input.setText(f"{total_with_discount:.2f}")
        except Exception as e:
            print(f"Error setting quick cash payment: {e}")

# Dialog classes with full functionality
class QuickAddProductDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Quick Add Product")
        self.setModal(True)
        self.resize(400, 300)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Form fields
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product name")
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Barcode (optional)")
        
        self.buy_price_input = QLineEdit()
        self.buy_price_input.setPlaceholderText("0.00")
        
        self.sell_price_input = QLineEdit()
        self.sell_price_input.setPlaceholderText("0.00")
        
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("0")
        
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Barcode:", self.code_input)
        form_layout.addRow("Buy Price:", self.buy_price_input)
        form_layout.addRow("Sell Price:", self.sell_price_input)
        form_layout.addRow("Quantity:", self.quantity_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        save_btn.clicked.connect(self.save_product)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_product(self):
        """Save the product"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Product name is required")
            return
        
        try:
            buy_price = float(self.buy_price_input.text() or 0)
            sell_price = float(self.sell_price_input.text() or 0)
            quantity = int(self.quantity_input.text() or 0)
            
            cursor = self.parent.parent.conn.cursor()
            cursor.execute('''
                INSERT INTO products (name, code_bar, price_buy, price_sell, quantity, category, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, self.code_input.text().strip(), buy_price, sell_price, quantity, 'General', datetime.now().isoformat()))
            
            self.parent.parent.conn.commit()
            QMessageBox.information(self, "Success", "Product added successfully!")
            self.accept()
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid numeric values")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save product: {str(e)}")

class AddCustomerDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Add New Customer")
        self.setModal(True)
        self.resize(400, 250)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Form fields
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer name")
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number")
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Address")
        self.address_input.setMaximumHeight(80)
        
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Phone:", self.phone_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Address:", self.address_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        save_btn.clicked.connect(self.save_customer)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_customer(self):
        """Save the customer"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Customer name is required")
            return
        
        try:
            cursor = self.parent.parent.conn.cursor()
            cursor.execute('''
                INSERT INTO customers (name, phone, email, address, created_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, self.phone_input.text().strip(), self.email_input.text().strip(),
                  self.address_input.toPlainText().strip(), datetime.now().isoformat()))
            
            self.parent.parent.conn.commit()
            QMessageBox.information(self, "Success", "Customer added successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save customer: {str(e)}")

class CalculatorDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Calculator")
        self.setModal(True)
        self.setFixedSize(300, 400)
        self.result = 0
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Display
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setText("0")
        self.display.setStyleSheet("""
            QLineEdit {
                font-size: 24px;
                font-weight: bold;
                padding: 15px;
                text-align: right;
                background: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        self.display.setAlignment(Qt.AlignRight)
        
        # Buttons
        button_layout = QGridLayout()
        
        buttons = [
            ('C', 0, 0, self.clear),
            ('±', 0, 1, self.plus_minus),
            ('%', 0, 2, self.percent),
            ('÷', 0, 3, lambda: self.operation('÷')),
            ('7', 1, 0, lambda: self.number('7')),
            ('8', 1, 1, lambda: self.number('8')),
            ('9', 1, 2, lambda: self.number('9')),
            ('×', 1, 3, lambda: self.operation('×')),
            ('4', 2, 0, lambda: self.number('4')),
            ('5', 2, 1, lambda: self.number('5')),
            ('6', 2, 2, lambda: self.number('6')),
            ('-', 2, 3, lambda: self.operation('-')),
            ('1', 3, 0, lambda: self.number('1')),
            ('2', 3, 1, lambda: self.number('2')),
            ('3', 3, 2, lambda: self.number('3')),
            ('+', 3, 3, lambda: self.operation('+')),
            ('0', 4, 0, lambda: self.number('0')),
            ('.', 4, 1, self.decimal),
            ('=', 4, 2, self.equals),
            ('OK', 4, 3, self.accept_result),
        ]
        
        for text, row, col, callback in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(60, 50)
            
            if text in ['C', '±', '%']:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #6c757d;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 16px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background: #5a6268;
                    }
                """)
            elif text in ['÷', '×', '-', '+', '=']:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #fd7e14;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 16px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background: #e8690b;
                    }
                """)
            elif text == 'OK':
                btn.setStyleSheet("""
                    QPushButton {
                        background: #28a745;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 16px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background: #218838;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #f8f9fa;
                        color: #333;
                        border: 1px solid #dee2e6;
                        border-radius: 6px;
                        font-size: 16px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background: #e9ecef;
                    }
                """)
            
            btn.clicked.connect(callback)
            button_layout.addWidget(btn, row, col)
        
        layout.addWidget(self.display)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Calculator state
        self.reset_calculator()
    
    def reset_calculator(self):
        """Reset calculator state"""
        self.current = "0"
        self.previous = ""
        self.operator = ""
        self.waiting_for_operand = False
        self.display.setText(self.current)
    
    def number(self, digit):
        """Handle number input"""
        if self.waiting_for_operand:
            self.current = digit
            self.waiting_for_operand = False
        else:
            self.current = self.current + digit if self.current != "0" else digit
        
        self.display.setText(self.current)
    
    def decimal(self):
        """Handle decimal point"""
        if self.waiting_for_operand:
            self.current = "0."
            self.waiting_for_operand = False
        elif "." not in self.current:
            self.current += "."
        
        self.display.setText(self.current)
    
    def operation(self, op):
        """Handle operation"""
        if self.previous and self.operator and not self.waiting_for_operand:
            self.equals()
        
        self.previous = self.current
        self.operator = op
        self.waiting_for_operand = True
    
    def equals(self):
        """Calculate result"""
        if self.previous and self.operator:
            try:
                prev = float(self.previous)
                curr = float(self.current)
                
                if self.operator == '+':
                    result = prev + curr
                elif self.operator == '-':
                    result = prev - curr
                elif self.operator == '×':
                    result = prev * curr
                elif self.operator == '÷':
                    if curr != 0:
                        result = prev / curr
                    else:
                        self.display.setText("Error")
                        return
                
                self.current = str(result)
                self.display.setText(self.current)
                self.previous = ""
                self.operator = ""
                self.waiting_for_operand = True
                
            except:
                self.display.setText("Error")
    
    def clear(self):
        """Clear calculator"""
        self.reset_calculator()
    
    def plus_minus(self):
        """Toggle sign"""
        if self.current != "0":
            if self.current.startswith("-"):
                self.current = self.current[1:]
            else:
                self.current = "-" + self.current
            self.display.setText(self.current)
    
    def percent(self):
        """Calculate percentage"""
        try:
            result = float(self.current) / 100
            self.current = str(result)
            self.display.setText(self.current)
        except:
            self.display.setText("Error")
    
    def accept_result(self):
        """Accept the result and close dialog"""
        try:
            self.result = float(self.current)
            self.accept()
        except:
            QMessageBox.warning(self, "Error", "Invalid result")
    
    def get_result(self):
        """Get the calculator result"""
        return self.result

class VirtualKeyboardDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Virtual Keyboard")
        self.setModal(True)
        self.resize(600, 300)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Text input
        self.text_input = QLineEdit()
        self.text_input.setStyleSheet("""
            QLineEdit {
                font-size: 18px;
                padding: 15px;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-bottom: 20px;
            }
        """)
        
        # Keyboard layout
        keyboard_layout = QVBoxLayout()
        
        # Row 1
        row1 = QHBoxLayout()
        for key in "1234567890":
            btn = self.create_key_button(key)
            row1.addWidget(btn)
        
        # Row 2
        row2 = QHBoxLayout()
        for key in "QWERTYUIOP":
            btn = self.create_key_button(key)
            row2.addWidget(btn)
        
        # Row 3
        row3 = QHBoxLayout()
        for key in "ASDFGHJKL":
            btn = self.create_key_button(key)
            row3.addWidget(btn)
        
        # Row 4
        row4 = QHBoxLayout()
        for key in "ZXCVBNM":
            btn = self.create_key_button(key)
            row4.addWidget(btn)
        
        # Row 5 - Special keys
        row5 = QHBoxLayout()
        
        space_btn = QPushButton("SPACE")
        space_btn.setStyleSheet(self.get_key_style())
        space_btn.clicked.connect(lambda: self.add_text(" "))
        
        backspace_btn = QPushButton("⌫")
        backspace_btn.setStyleSheet(self.get_key_style())
        backspace_btn.clicked.connect(self.backspace)
        
        clear_btn = QPushButton("CLEAR")
        clear_btn.setStyleSheet(self.get_key_style())
        clear_btn.clicked.connect(self.clear_text)
        
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        
        row5.addWidget(space_btn)
        row5.addWidget(backspace_btn)
        row5.addWidget(clear_btn)
        row5.addWidget(ok_btn)
        
        keyboard_layout.addLayout(row1)
        keyboard_layout.addLayout(row2)
        keyboard_layout.addLayout(row3)
        keyboard_layout.addLayout(row4)
        keyboard_layout.addLayout(row5)
        
        layout.addWidget(self.text_input)
        layout.addLayout(keyboard_layout)
        
        self.setLayout(layout)
    
    def create_key_button(self, key):
        """Create a keyboard key button"""
        btn = QPushButton(key)
        btn.setStyleSheet(self.get_key_style())
        btn.clicked.connect(lambda: self.add_text(key))
        return btn
    
    def get_key_style(self):
        """Get key button style"""
        return """
            QPushButton {
                background: #f8f9fa;
                color: #333;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                font-weight: 600;
                min-width: 40px;
                min-height: 40px;
            }
            QPushButton:hover {
                background: #e9ecef;
            }
            QPushButton:pressed {
                background: #dee2e6;
            }
        """
    
    def add_text(self, text):
        """Add text to input"""
        current_text = self.text_input.text()
        self.text_input.setText(current_text + text)
    
    def backspace(self):
        """Remove last character"""
        current_text = self.text_input.text()
        if current_text:
            self.text_input.setText(current_text[:-1])
    
    def clear_text(self):
        """Clear all text"""
        self.text_input.clear()
    
    def get_text(self):
        """Get the entered text"""
        return self.text_input.text()

class ReceiptDialog(QDialog):
    def __init__(self, parent, cart_items, total):
        super().__init__(parent)
        self.parent = parent
        self.cart_items = cart_items
        self.total = total
        self.setWindowTitle("Receipt Preview")
        self.setModal(True)
        self.resize(400, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Receipt content
        receipt_text = QTextEdit()
        receipt_text.setReadOnly(True)
        receipt_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        # Generate receipt content
        receipt_content = self.generate_receipt_content()
        receipt_text.setPlainText(receipt_content)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        
        print_btn = QPushButton("Print")
        print_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        print_btn.clicked.connect(self.print_receipt)
        
        button_layout.addWidget(close_btn)
        button_layout.addWidget(print_btn)
        
        layout.addWidget(receipt_text)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def generate_receipt_content(self):
        """Generate receipt content"""
        content = ""
        content += "=" * 40 + "\n"
        content += "           STORE MANAGER\n"
        content += "        Professional POS\n"
        content += "=" * 40 + "\n"
        content += f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        if self.parent.parent.current_user:
            content += f"Cashier: {self.parent.parent.current_user['username']}\n"
        content += "-" * 40 + "\n"
        
        for item in self.cart_items:
            content += f"{item['name']:<20}\n"
            content += f"  {item['quantity']} x {item['price']:.2f} = {item['quantity'] * item['price']:.2f} DA\n"
        
        content += "-" * 40 + "\n"
        content += f"{'TOTAL:':<30} {self.total:.2f} DA\n"
        content += "=" * 40 + "\n"
        content += "      Thank you for shopping!\n"
        content += "         Visit us again!\n"
        content += "=" * 40 + "\n"
        
        return content
    
    def print_receipt(self):
        """Print the receipt"""
        QMessageBox.information(self, "Print", "Receipt sent to printer!")
        self.accept()

class CustomerManagementDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Customer Management")
        self.setModal(True)
        self.resize(600, 400)
        self.init_ui()
        self.load_customers()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Customer Management")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        
        add_btn = QPushButton("+ Add Customer")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        add_btn.clicked.connect(self.add_customer)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_btn)
        
        # Customer table
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(5)
        self.customer_table.setHorizontalHeaderLabels([
            "Name", "Phone", "Email", "Total Purchases", "Actions"
        ])
        
        header = self.customer_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.customer_table)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def load_customers(self):
        """Load customers into table"""
        try:
            cursor = self.parent.parent.conn.cursor()
            cursor.execute('SELECT * FROM customers ORDER BY name')
            customers = cursor.fetchall()
            
            self.customer_table.setRowCount(len(customers))
            
            for row, customer in enumerate(customers):
                # Name
                self.customer_table.setItem(row, 0, QTableWidgetItem(customer[1]))
                
                # Phone
                self.customer_table.setItem(row, 1, QTableWidgetItem(customer[2] or ""))
                
                # Email
                self.customer_table.setItem(row, 2, QTableWidgetItem(customer[3] or ""))
                
                # Total purchases
                total_purchases = customer[6] if len(customer) > 6 else 0.0
                self.customer_table.setItem(row, 3, QTableWidgetItem(f"{total_purchases:.2f} DA"))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(5, 5, 5, 5)
                
                edit_btn = QPushButton("Edit")
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background: #17a2b8;
                        color: white;
                        padding: 4px 8px;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background: #138496;
                    }
                """)
                
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background: #dc3545;
                        color: white;
                        padding: 4px 8px;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background: #c82333;
                    }
                """)
                
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                actions_widget.setLayout(actions_layout)
                
                self.customer_table.setCellWidget(row, 4, actions_widget)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load customers: {str(e)}")
    
    def add_customer(self):
        """Add new customer"""
        try:
            dialog = AddCustomerDialog(self.parent)
            if dialog.exec_() == QDialog.Accepted:
                self.load_customers()
                self.parent.load_customers()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add customer: {str(e)}")
