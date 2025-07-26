from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime
import json
import traceback

"""
Enhanced POS Widget with Barcode Scanner Support
"""

import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QPushButton, QLabel, QLineEdit, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QFrame, QSplitter,
                             QGroupBox, QSpinBox, QTextEdit, QScrollArea,
                             QCompleter, QListWidget, QListWidgetItem, QComboBox,
                             QHeaderView, QAbstractItemView, QDoubleSpinBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QStringListModel
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor
import json
from datetime import datetime

class POSWidget(QWidget):
    """
    Enhanced Point of Sale Widget with Barcode Scanner Support
    """
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.conn = parent.conn
        self.user_role = getattr(parent, 'user_role', 'admin')
        self.cart_items = []
        self.total = 0.0
        self.total_amount = 0.0
        self.selected_client = "Walk-in Customer"
        self.remise = 0.0
        self.payment_received = 0.0
        self.current_product = None
        
        # Initialize barcode components with fallback
        try:
            from barcode_scanner import BarcodeHandler, BarcodeScanner, BarcodeInputValidator, ProductImageHandler
            self.barcode_handler = BarcodeHandler(self.conn)
            self.barcode_scanner = None
            self.barcode_validator = BarcodeInputValidator()
            self.image_handler = ProductImageHandler()
        except ImportError:
            print("Barcode scanner components not available")
            self.barcode_handler = None
            self.barcode_scanner = None
            self.barcode_validator = None
            self.image_handler = None
        
        # Timer for clock
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        
        # Auto-focus timer for barcode input
        self.focus_timer = QTimer()
        self.focus_timer.timeout.connect(self.ensure_barcode_focus)
        self.focus_timer.start(1000)  # Check focus every second
        
        self.init_ui()
        self.load_products()
        
        # Set initial focus to barcode input
        if hasattr(self, 'barcode_input'):
            self.barcode_input.setFocus()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Point of Sale - Barcode Scanner Ready")
        self.setGeometry(100, 100, 1400, 800)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top bar
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Content area
        content_layout = QHBoxLayout()
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Products and Search
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Cart and Checkout
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([800, 600])
        
        content_layout.addWidget(splitter)
        main_layout.addLayout(content_layout)
        
        self.setLayout(main_layout)
        
        # Apply styling
        self.apply_styling()
    
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
            ("📋 Products", "#fd7e14", lambda: self.parent.show_product_management() if hasattr(self.parent, 'show_product_management') else None),
            ("📄 Tickets", "#dc3545", lambda: self.parent.show_ticket_management() if hasattr(self.parent, 'show_ticket_management') else None),
            ("👤 Main Menu", "#6c757d", lambda: self.parent.show_main_menu() if hasattr(self.parent, 'show_main_menu') else None)
        ]
        
        for text, color, callback in buttons_data:
            btn = QPushButton(text)
            btn.setMinimumSize(100, 40)
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
                    padding: 9px 11px 7px 13px;
                }}
            """)
            if callback:
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
        layout.addWidget(scroll_area, 1)
        layout.addWidget(self.datetime_widget, 0, Qt.AlignRight)
        
        top_widget.setLayout(layout)
        return top_widget

    def darken_color(self, hex_color, percent):
        """Helper to darken colors for hover states"""
        color = QColor(hex_color)
        return color.darker(100 + percent).name()
    
    def create_left_panel(self):
        """Create the left panel with barcode input and products"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # Barcode Scanner Section
        barcode_group = QGroupBox("Barcode Scanner")
        barcode_layout = QVBoxLayout()
        
        # Barcode input field
        barcode_input_layout = QHBoxLayout()
        barcode_label = QLabel("Scan/Enter Barcode:")
        barcode_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan barcode here or type product name...")
        self.barcode_input.setFont(QFont("Arial", 12))
        self.barcode_input.returnPressed.connect(self.process_barcode_input)
        self.barcode_input.textChanged.connect(self.on_barcode_text_changed)
        
        # Camera scan button (if available)
        self.camera_scan_btn = QPushButton("📷 Camera Scan")
        self.camera_scan_btn.clicked.connect(self.start_camera_scan)
        self.camera_scan_btn.setEnabled(True)  # Will be disabled if camera not available
        
        barcode_input_layout.addWidget(barcode_label)
        barcode_input_layout.addWidget(self.barcode_input, 1)
        barcode_input_layout.addWidget(self.camera_scan_btn)
        
        # Search suggestions
        self.search_suggestions = QListWidget()
        self.search_suggestions.setMaximumHeight(100)
        self.search_suggestions.itemClicked.connect(self.select_suggestion)
        self.search_suggestions.hide()
        
        barcode_layout.addLayout(barcode_input_layout)
        barcode_layout.addWidget(self.search_suggestions)
        barcode_group.setLayout(barcode_layout)
        
        # Product display area
        product_group = QGroupBox("Product Information")
        product_layout = QVBoxLayout()
        
        # Product image and details
        product_info_layout = QHBoxLayout()
        
        # Product image
        self.product_image_label = QLabel()
        self.product_image_label.setFixedSize(150, 150)
        self.product_image_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.product_image_label.setAlignment(Qt.AlignCenter)
        self.product_image_label.setText("No Image")
        
        # Product details
        product_details_layout = QVBoxLayout()
        self.product_name_label = QLabel("Product: Not selected")
        self.product_price_label = QLabel("Price: $0.00")
        self.product_stock_label = QLabel("Stock: 0")
        self.product_barcode_label = QLabel("Barcode: -")
        
        # Quantity selector
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Quantity:"))
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setMinimum(1)
        self.quantity_spinbox.setMaximum(999)
        self.quantity_spinbox.setValue(1)
        quantity_layout.addWidget(self.quantity_spinbox)
        quantity_layout.addStretch()
        
        # Add to cart button
        self.add_to_cart_btn = QPushButton("Add to Cart")
        self.add_to_cart_btn.clicked.connect(self.add_selected_product_to_cart)
        self.add_to_cart_btn.setEnabled(False)
        
        product_details_layout.addWidget(self.product_name_label)
        product_details_layout.addWidget(self.product_price_label)
        product_details_layout.addWidget(self.product_stock_label)
        product_details_layout.addWidget(self.product_barcode_label)
        product_details_layout.addLayout(quantity_layout)
        product_details_layout.addWidget(self.add_to_cart_btn)
        product_details_layout.addStretch()
        
        product_info_layout.addWidget(self.product_image_label)
        product_info_layout.addLayout(product_details_layout)
        
        product_layout.addLayout(product_info_layout)
        product_group.setLayout(product_layout)
        
        # Quick access products grid
        quick_products_group = QGroupBox("Quick Access Products")
        self.products_scroll = QScrollArea()
        self.products_widget = QWidget()
        self.products_layout = QGridLayout()
        self.products_widget.setLayout(self.products_layout)
        self.products_scroll.setWidget(self.products_widget)
        self.products_scroll.setWidgetResizable(True)
        
        quick_layout = QVBoxLayout()
        quick_layout.addWidget(self.products_scroll)
        quick_products_group.setLayout(quick_layout)
        
        # Add all sections to left panel
        left_layout.addWidget(barcode_group)
        left_layout.addWidget(product_group)
        left_layout.addWidget(quick_products_group, 1)
        
        left_widget.setLayout(left_layout)
        return left_widget
    
    def create_right_panel(self):
        """Create the right panel with cart and checkout"""
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # Cart section
        cart_group = QGroupBox("Shopping Cart")
        cart_layout = QVBoxLayout()
        
        # Cart table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(['Product', 'Price', 'Qty', 'Total', 'Action'])
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        
        # Cart controls
        cart_controls_layout = QHBoxLayout()
        self.clear_cart_btn = QPushButton("Clear Cart")
        self.clear_cart_btn.clicked.connect(self.clear_cart)
        
        self.remove_item_btn = QPushButton("Remove Selected")
        self.remove_item_btn.clicked.connect(self.remove_selected_item)
        
        cart_controls_layout.addWidget(self.clear_cart_btn)
        cart_controls_layout.addWidget(self.remove_item_btn)
        cart_controls_layout.addStretch()
        
        cart_layout.addWidget(self.cart_table)
        cart_layout.addLayout(cart_controls_layout)
        cart_group.setLayout(cart_layout)
        
        # Total section
        total_group = QGroupBox("Order Total")
        total_layout = QVBoxLayout()
        
        self.subtotal_label = QLabel("Subtotal: $0.00")
        self.tax_label = QLabel("Tax (10%): $0.00")
        self.total_label = QLabel("TOTAL: $0.00")
        self.total_label.setFont(QFont("Arial", 16, QFont.Bold))
        
        total_layout.addWidget(self.subtotal_label)
        total_layout.addWidget(self.tax_label)
        total_layout.addWidget(self.total_label)
        total_group.setLayout(total_layout)
        
        # Checkout section
        checkout_group = QGroupBox("Checkout")
        checkout_layout = QVBoxLayout()
        
        self.checkout_btn = QPushButton("Process Payment")
        self.checkout_btn.clicked.connect(self.process_payment)
        self.checkout_btn.setEnabled(False)
        
        self.print_receipt_btn = QPushButton("Print Last Receipt")
        self.print_receipt_btn.clicked.connect(self.print_receipt)
        
        checkout_layout.addWidget(self.checkout_btn)
        checkout_layout.addWidget(self.print_receipt_btn)
        checkout_group.setLayout(checkout_layout)
        
        # Add all sections to right panel
        right_layout.addWidget(cart_group, 1)
        right_layout.addWidget(total_group)
        right_layout.addWidget(checkout_group)
        
        right_widget.setLayout(right_layout)
        return right_widget
    
    def ensure_barcode_focus(self):
        """Ensure barcode input always has focus when not in a dialog"""
        if hasattr(self, 'barcode_input') and not self.barcode_input.hasFocus() and self.isActiveWindow():
            # Only refocus if no modal dialogs are open
            if not QApplication.activeModalWidget():
                self.barcode_input.setFocus()
    
    def process_barcode_input(self):
        """Process barcode input from scanner or manual entry"""
        input_text = self.barcode_input.text().strip()
        
        if not input_text:
            return
        
        # Search for product by barcode or name
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM products 
                WHERE code_bar = ? OR LOWER(name) LIKE LOWER(?)
                ORDER BY 
                    CASE WHEN code_bar = ? THEN 1 ELSE 2 END,
                    name
            ''', (input_text, f'%{input_text}%', input_text))
            
            products = cursor.fetchall()
            
            if products:
                if len(products) == 1:
                    # Single match found
                    self.add_product_to_cart(products[0])
                    self.show_product_info(products[0])
                else:
                    # Multiple matches - show suggestions
                    self.show_search_suggestions(products)
            else:
                # No matches found
                QMessageBox.warning(self, "Product Not Found", 
                                  f"No product found with barcode/name: {input_text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error searching for product: {str(e)}")
        
        # Clear input and refocus
        self.barcode_input.clear()
        self.barcode_input.setFocus()
    
    def on_barcode_text_changed(self, text):
        """Handle text changes in barcode input for live search"""
        if len(text) >= 3:  # Start searching after 3 characters
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT * FROM products 
                    WHERE LOWER(name) LIKE LOWER(?) OR code_bar LIKE ?
                    ORDER BY name
                    LIMIT 5
                ''', (f'%{text}%', f'%{text}%'))
                
                products = cursor.fetchall()
                if products:
                    self.show_search_suggestions(products)
                else:
                    self.search_suggestions.hide()
            except Exception as e:
                print(f"Error in live search: {e}")
                self.search_suggestions.hide()
        else:
            self.search_suggestions.hide()
    
    def show_search_suggestions(self, products):
        """Show search suggestions dropdown"""
        self.search_suggestions.clear()
        
        for product in products:
            item_text = f"{product[1]} - ${product[4]:.2f} (Stock: {product[5]})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, product)  # Store product data
            self.search_suggestions.addItem(item)
        
        self.search_suggestions.show()
    
    def select_suggestion(self, item):
        """Handle selection from search suggestions"""
        product = item.data(Qt.UserRole)
        if product:
            self.add_product_to_cart(product)
            self.show_product_info(product)
            self.barcode_input.clear()
            self.search_suggestions.hide()
            self.barcode_input.setFocus()
    
    def show_product_info(self, product):
        """Display product information in the product info section"""
        if not product:
            return
        
        # Update product labels
        self.product_name_label.setText(f"Product: {product[1]}")
        self.product_price_label.setText(f"Price: ${product[4]:.2f}")
        self.product_stock_label.setText(f"Stock: {product[5]}")
        self.product_barcode_label.setText(f"Barcode: {product[2] or 'N/A'}")
        
        # Clear image for now
        self.product_image_label.clear()
        self.product_image_label.setText("No Image")
        
        # Enable add to cart button
        self.add_to_cart_btn.setEnabled(True)
        self.current_product = product
    
    def add_selected_product_to_cart(self):
        """Add currently selected product to cart"""
        if hasattr(self, 'current_product') and self.current_product:
            self.add_product_to_cart(self.current_product)
    
    def add_product_to_cart(self, product):
        """Add product to shopping cart"""
        if not product:
            return
        
        quantity = self.quantity_spinbox.value()
        
        # Check if product already in cart
        for i, item in enumerate(self.cart_items):
            if item['id'] == product[0]:
                # Update quantity
                new_quantity = item['quantity'] + quantity
                if new_quantity <= product[5]:  # Check stock
                    self.cart_items[i]['quantity'] = new_quantity
                    self.cart_items[i]['total'] = new_quantity * product[4]
                else:
                    QMessageBox.warning(self, "Insufficient Stock", 
                                      f"Not enough stock. Available: {product[5]}")
                    return
                break
        else:
            # Add new item to cart
            if quantity <= product[5]:  # Check stock
                cart_item = {
                    'id': product[0],
                    'name': product[1],
                    'price': product[4],
                    'quantity': quantity,
                    'total': quantity * product[4],
                    'stock': product[5]
                }
                self.cart_items.append(cart_item)
            else:
                QMessageBox.warning(self, "Insufficient Stock", 
                                  f"Not enough stock. Available: {product[5]}")
                return
        
        self.update_cart_display()
        self.quantity_spinbox.setValue(1)  # Reset quantity
    
    def update_cart_display(self):
        """Update the cart table display"""
        self.cart_table.setRowCount(len(self.cart_items))
        
        subtotal = 0
        for i, item in enumerate(self.cart_items):
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(i, 1, QTableWidgetItem(f"${item['price']:.2f}"))
            self.cart_table.setItem(i, 2, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"${item['total']:.2f}"))
            
            # Add remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, row=i: self.remove_cart_item(row))
            self.cart_table.setCellWidget(i, 4, remove_btn)
            
            subtotal += item['total']
        
        # Update totals
        tax = subtotal * 0.1  # 10% tax
        total = subtotal + tax
        
        self.subtotal_label.setText(f"Subtotal: ${subtotal:.2f}")
        self.tax_label.setText(f"Tax (10%): ${tax:.2f}")
        self.total_label.setText(f"TOTAL: ${total:.2f}")
        
        self.total_amount = total
        self.checkout_btn.setEnabled(len(self.cart_items) > 0)
    
    def remove_cart_item(self, row):
        """Remove item from cart"""
        if 0 <= row < len(self.cart_items):
            del self.cart_items[row]
            self.update_cart_display()
    
    def remove_selected_item(self):
        """Remove selected item from cart"""
        current_row = self.cart_table.currentRow()
        if current_row >= 0:
            self.remove_cart_item(current_row)
    
    def clear_cart(self):
        """Clear all items from cart"""
        if self.cart_items:
            reply = QMessageBox.question(self, "Clear Cart", 
                                       "Are you sure you want to clear the cart?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.cart_items.clear()
                self.update_cart_display()
    
    def start_camera_scan(self):
        """Start camera-based barcode scanning"""
        QMessageBox.information(self, "Camera Scan", "Camera scanning not implemented yet. Please use manual input.")
    
    def load_products(self):
        """Load products from database with error handling"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM products ORDER BY name')
            products = cursor.fetchall()
            
            # Clear existing buttons safely
            self.clear_product_buttons()
            
            row, col = 0, 0
            max_cols = 3
            
            for product in products:
                try:
                    btn = self.create_product_button(product)
                    self.products_layout.addWidget(btn, row, col)
                    
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
            while self.products_layout.count():
                child = self.products_layout.takeAt(0)
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
                    existing_item['total'] = existing_item['quantity'] * existing_item['price']
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
                    'total': product_sell_price,
                    'stock': product_quantity
                }
                self.cart_items.append(new_item)
            
            # Update displays
            self.update_cart_display()
            
        except Exception as e:
            print(f"Error adding product to cart: {e}")
            print(f"Product data: {product}")
            print(f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"Failed to add product to cart: {str(e)}")
    
    def process_payment(self):
        """Process payment for current cart"""
        if not self.cart_items:
            return
        
        # Simple payment dialog
        payment_amount, ok = QInputDialog.getDouble(
            self, 
            "Payment", 
            f"Total amount: ${self.total_amount:.2f}\nEnter payment amount:",
            self.total_amount,
            0,
            999999,
            2
        )
        
        if ok and payment_amount >= self.total_amount:
            # Process the sale
            if self.complete_sale({'amount': payment_amount, 'method': 'cash'}):
                change = payment_amount - self.total_amount
                QMessageBox.information(self, "Sale Complete", 
                                      f"Payment processed successfully!\nChange: ${change:.2f}")
                self.cart_items.clear()
                self.update_cart_display()
                self.barcode_input.setFocus()
        elif ok:
            QMessageBox.warning(self, "Insufficient Payment", 
                              f"Payment amount (${payment_amount:.2f}) is less than total (${self.total_amount:.2f})")
    
    def complete_sale(self, payment_info):
        """Complete the sale and update database"""
        try:
            cursor = self.conn.cursor()
            
            # Generate ticket number
            cursor.execute('SELECT COUNT(*) FROM tickets')
            ticket_count = cursor.fetchone()[0]
            ticket_number = f"TKT{ticket_count + 1:06d}"
            
            # Create sale record
            sale_data = {
                'items': self.cart_items,
                'total': self.total_amount,
                'payment_method': payment_info.get('method', 'cash'),
                'timestamp': datetime.now().isoformat()
            }
            
            cursor.execute('''
                INSERT INTO tickets (ticket_number, total_price, payment_method, items, customer_name, cashier_id, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ticket_number, self.total_amount, payment_info.get('method', 'cash'), 
                  json.dumps(sale_data), self.selected_client, 
                  self.parent.current_user['id'] if self.parent.current_user else 1,
                  datetime.now().isoformat()))
            
            # Update product stock
            for item in self.cart_items:
                cursor.execute('UPDATE products SET quantity = quantity - ? WHERE id = ?',
                             (item['quantity'], item['id']))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Sale Error", f"Error processing sale: {str(e)}")
            return False
    
    def update_clock(self):
        """Update clock display"""
        try:
            if hasattr(self, 'date_label') and hasattr(self, 'time_label'):
                now = datetime.now()
                self.date_label.setText(now.strftime("%d/%m/%Y"))
                self.time_label.setText(now.strftime("%H:%M:%S"))
        except Exception as e:
            print(f"Error updating clock: {e}")
    
    # Button handler functions
    def toggle_printer(self):
        """Toggle printer status"""
        QMessageBox.information(self, "Printer", "Printer status: Ready\nLast printed: Receipt #001")
    
    def show_alerts(self):
        """Show system alerts"""
        try:
            cursor = self.conn.cursor()
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
            cursor = self.conn.cursor()
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
            
            receipt_content = self.generate_receipt_content()
            receipt_dialog = ReceiptDialog(self, receipt_content)
            receipt_dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to print receipt: {str(e)}")
    
    def generate_receipt_content(self):
        """Generate receipt content"""
        content = ""
        content += "=" * 40 + "\n"
        content += "           STORE MANAGER\n"
        content += "        Professional POS\n"
        content += "=" * 40 + "\n"
        content += f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        if self.parent.current_user:
            content += f"Cashier: {self.parent.current_user['username']}\n"
        content += "-" * 40 + "\n"
        
        for item in self.cart_items:
            content += f"{item['name']:<20}\n"
            content += f"  {item['quantity']} x {item['price']:.2f} = {item['total']:.2f} DA\n"
        
        content += "-" * 40 + "\n"
        content += f"{'TOTAL:':<30} {self.total_amount:.2f} DA\n"
        content += "=" * 40 + "\n"
        content += "      Thank you for shopping!\n"
        content += "         Visit us again!\n"
        content += "=" * 40 + "\n"
        
        return content
    
    def apply_styling(self):
        """Apply custom styling to the widget"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QLabel {
                color: #333;
            }
        """)
    
    def closeEvent(self, event):
        """Handle widget close event"""
        # Stop focus timer
        if hasattr(self, 'focus_timer'):
            self.focus_timer.stop()
        
        event.accept()


# Dialog classes
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
            
            cursor = self.parent.conn.cursor()
            cursor.execute('''
                INSERT INTO products (name, code_bar, price_buy, price_sell, quantity, category, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, self.code_input.text().strip(), buy_price, sell_price, quantity, 'General', datetime.now().isoformat()))
            
            self.parent.conn.commit()
            QMessageBox.information(self, "Success", "Product added successfully!")
            self.accept()
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid numeric values")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save product: {str(e)}")


class ReceiptDialog(QDialog):
    def __init__(self, parent, content):
        super().__init__(parent)
        self.content = content
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
        receipt_text.setPlainText(self.content)
        
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
    
    def print_receipt(self):
        """Print the receipt"""
        QMessageBox.information(self, "Print", "Receipt sent to printer!")
        self.accept()
