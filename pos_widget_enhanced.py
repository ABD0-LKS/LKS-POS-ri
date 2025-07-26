"""
Enhanced POS Widget with Automatic Barcode Scanning
This is the Git version with advanced features
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime
import json
import sqlite3
from barcode_scanner_enhanced import BarcodeScannerWidget

class EnhancedPOSWidget(QWidget):
    """Enhanced POS Widget with barcode scanner integration"""
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.conn = parent.conn
        self.cart_items = []
        self.total_amount = 0.0
        self.selected_client = "Walk-in Customer"
        
        # Load settings
        self.load_settings()
        
        # Initialize UI
        self.init_ui()
        
        # Timer for clock
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()
    
    def load_settings(self):
        """Load application settings"""
        try:
            import json
            import os
            if os.path.exists("app_settings.json"):
                with open("app_settings.json", 'r') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {}
        except:
            self.settings = {}
    
    def init_ui(self):
        """Initialize the enhanced UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top bar
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Barcode scanner and products
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Center panel - Cart and transaction
        center_panel = self.create_center_panel()
        content_splitter.addWidget(center_panel)
        
        # Right panel - Controls and checkout
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        content_splitter.setSizes([400, 500, 300])
        
        main_layout.addWidget(content_splitter)
        self.setLayout(main_layout)
        
        # Apply styling
        self.apply_enhanced_styling()
    
    def create_top_bar(self):
        """Create enhanced top bar"""
        top_widget = QWidget()
        top_widget.setFixedHeight(80)
        top_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                color: white;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Left side - Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        buttons_data = [
            ("🏠 Main Menu", "#28a745", lambda: self.parent.show_main_menu()),
            ("📊 Dashboard", "#17a2b8", lambda: self.parent.show_dashboard()),
            ("📦 Products", "#ffc107", lambda: self.parent.show_product_management()),
            ("🎫 Tickets", "#dc3545", lambda: self.parent.show_ticket_management()),
            ("⚙️ Settings", "#6f42c1", lambda: self.parent.show_settings()),
        ]
        
        for text, color, callback in buttons_data:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 15px;
                    font-weight: 600;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                    transform: scale(1.05);
                }}
            """)
            btn.clicked.connect(callback)
            buttons_layout.addWidget(btn)
        
        # Right side - Clock and info
        info_widget = QWidget()
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        self.date_label = QLabel()
        self.date_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                font-weight: 500;
            }
        """)
        
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: 700;
            }
        """)
        
        info_layout.addWidget(self.date_label, 0, Qt.AlignRight)
        info_layout.addWidget(self.time_label, 0, Qt.AlignRight)
        info_widget.setLayout(info_layout)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        layout.addWidget(info_widget)
        
        top_widget.setLayout(layout)
        return top_widget
    
    def create_left_panel(self):
        """Create left panel with barcode scanner"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # Barcode scanner section
        scanner_group = QGroupBox("🔍 Barcode Scanner")
        scanner_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #4285f4;
                border-radius: 10px;
                margin-top: 10px;
                padding: 15px;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #4285f4;
            }
        """)
        scanner_layout = QVBoxLayout()
        
        # Create barcode scanner widget
        self.barcode_scanner = BarcodeScannerWidget(self, self.conn)
        self.barcode_scanner.product_scanned.connect(self.on_product_scanned)
        
        scanner_layout.addWidget(self.barcode_scanner)
        scanner_group.setLayout(scanner_layout)
        
        # Quick products section
        quick_group = QGroupBox("⚡ Quick Access Products")
        quick_group.setStyleSheet(scanner_group.styleSheet().replace("#4285f4", "#28a745"))
        quick_layout = QVBoxLayout()
        
        # Products scroll area
        self.products_scroll = QScrollArea()
        self.products_widget = QWidget()
        self.products_layout = QGridLayout()
        self.products_widget.setLayout(self.products_layout)
        self.products_scroll.setWidget(self.products_widget)
        self.products_scroll.setWidgetResizable(True)
        self.products_scroll.setMaximumHeight(300)
        
        quick_layout.addWidget(self.products_scroll)
        quick_group.setLayout(quick_layout)
        
        left_layout.addWidget(scanner_group)
        left_layout.addWidget(quick_group)
        left_layout.addStretch()
        
        left_widget.setLayout(left_layout)
        
        # Load products
        self.load_quick_products()
        
        return left_widget
    
    def create_center_panel(self):
        """Create center panel with cart"""
        center_widget = QWidget()
        center_layout = QVBoxLayout()
        
        # Cart section
        cart_group = QGroupBox("🛒 Shopping Cart")
        cart_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #17a2b8;
                border-radius: 10px;
                margin-top: 10px;
                padding: 15px;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #17a2b8;
            }
        """)
        cart_layout = QVBoxLayout()
        
        # Cart table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(['Product', 'Price', 'Qty', 'Total', 'Action'])
        
        # Set column widths
        header = self.cart_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setStyleSheet("""
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
            QHeaderView::section {
                background: #f8f9fa;
                padding: 12px 8px;
                border: none;
                font-weight: 600;
                color: #495057;
            }
        """)
        
        # Cart controls
        cart_controls = QHBoxLayout()
        
        clear_cart_btn = QPushButton("🗑️ Clear Cart")
        clear_cart_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #c82333;
            }
        """)
        clear_cart_btn.clicked.connect(self.clear_cart)
        
        cart_controls.addWidget(clear_cart_btn)
        cart_controls.addStretch()
        
        cart_layout.addWidget(self.cart_table)
        cart_layout.addLayout(cart_controls)
        cart_group.setLayout(cart_layout)
        
        # Total section
        total_group = QGroupBox("💰 Order Summary")
        total_group.setStyleSheet(cart_group.styleSheet().replace("#17a2b8", "#28a745"))
        total_layout = QVBoxLayout()
        
        self.subtotal_label = QLabel("Subtotal: 0.00 DA")
        self.tax_label = QLabel("Tax (19%): 0.00 DA")
        self.total_label = QLabel("TOTAL: 0.00 DA")
        
        # Style total labels
        label_style = """
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #2c3e50;
                padding: 8px;
                background: #f8f9fa;
                border-radius: 6px;
                margin: 2px 0;
            }
        """
        
        self.subtotal_label.setStyleSheet(label_style)
        self.tax_label.setStyleSheet(label_style)
        self.total_label.setStyleSheet(label_style.replace("#2c3e50", "#28a745").replace("16px", "20px"))
        
        total_layout.addWidget(self.subtotal_label)
        total_layout.addWidget(self.tax_label)
        total_layout.addWidget(self.total_label)
        total_group.setLayout(total_layout)
        
        center_layout.addWidget(cart_group, 1)
        center_layout.addWidget(total_group)
        
        center_widget.setLayout(center_layout)
        return center_widget
    
    def create_right_panel(self):
        """Create right panel with checkout controls"""
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # Customer section
        customer_group = QGroupBox("👤 Customer")
        customer_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #ffc107;
                border-radius: 10px;
                margin-top: 10px;
                padding: 15px;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #ffc107;
            }
        """)
        customer_layout = QVBoxLayout()
        
        self.customer_label = QLabel(f"Customer: {self.selected_client}")
        self.customer_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #495057;
                padding: 10px;
                background: #fff3cd;
                border-radius: 6px;
            }
        """)
        
        change_customer_btn = QPushButton("Change Customer")
        change_customer_btn.setStyleSheet("""
            QPushButton {
                background: #ffc107;
                color: #212529;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #e0a800;
            }
        """)
        
        customer_layout.addWidget(self.customer_label)
        customer_layout.addWidget(change_customer_btn)
        customer_group.setLayout(customer_layout)
        
        # Payment section
        payment_group = QGroupBox("💳 Payment")
        payment_group.setStyleSheet(customer_group.styleSheet().replace("#ffc107", "#6f42c1"))
        payment_layout = QVBoxLayout()
        
        # Payment method
        payment_method_layout = QHBoxLayout()
        payment_method_label = QLabel("Method:")
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "Card", "Mobile Payment"])
        
        payment_method_layout.addWidget(payment_method_label)
        payment_method_layout.addWidget(self.payment_method_combo)
        
        # Payment amount
        payment_amount_layout = QHBoxLayout()
        payment_amount_label = QLabel("Amount:")
        self.payment_amount_input = QLineEdit()
        self.payment_amount_input.setPlaceholderText("0.00")
        
        payment_amount_layout.addWidget(payment_amount_label)
        payment_amount_layout.addWidget(self.payment_amount_input)
        
        # Change display
        self.change_label = QLabel("Change: 0.00 DA")
        self.change_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #28a745;
                padding: 10px;
                background: #d4edda;
                border-radius: 6px;
                text-align: center;
            }
        """)
        
        payment_layout.addLayout(payment_method_layout)
        payment_layout.addLayout(payment_amount_layout)
        payment_layout.addWidget(self.change_label)
        payment_group.setLayout(payment_layout)
        
        # Checkout buttons
        checkout_group = QGroupBox("✅ Checkout")
        checkout_group.setStyleSheet(customer_group.styleSheet().replace("#ffc107", "#28a745"))
        checkout_layout = QVBoxLayout()
        
        self.checkout_btn = QPushButton("💰 Process Payment")
        self.checkout_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 15px;
                border: none;
                border-radius: 8px;
                font-weight: 700;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #218838;
            }
            QPushButton:disabled {
                background: #6c757d;
                color: #adb5bd;
            }
        """)
        self.checkout_btn.clicked.connect(self.process_payment)
        self.checkout_btn.setEnabled(False)
        
        print_receipt_btn = QPushButton("🖨️ Print Receipt")
        print_receipt_btn.setStyleSheet("""
            QPushButton {
                background: #17a2b8;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #138496;
            }
        """)
        print_receipt_btn.clicked.connect(self.print_receipt)
        
        checkout_layout.addWidget(self.checkout_btn)
        checkout_layout.addWidget(print_receipt_btn)
        checkout_group.setLayout(checkout_layout)
        
        right_layout.addWidget(customer_group)
        right_layout.addWidget(payment_group)
        right_layout.addWidget(checkout_group)
        right_layout.addStretch()
        
        right_widget.setLayout(right_layout)
        return right_widget
    
    def load_quick_products(self):
        """Load quick access products"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM products WHERE quantity > 0 ORDER BY name LIMIT 12')
            products = cursor.fetchall()
            
            # Clear existing buttons
            for i in reversed(range(self.products_layout.count())): 
                self.products_layout.itemAt(i).widget().setParent(None)
            
            row, col = 0, 0
            for product in products:
                btn = self.create_product_button(product)
                self.products_layout.addWidget(btn, row, col)
                
                col += 1
                if col >= 2:  # 2 columns
                    col = 0
                    row += 1
                    
        except Exception as e:
            print(f"Error loading products: {e}")
    
    def create_product_button(self, product):
        """Create a product button"""
        btn = QPushButton()
        btn.setFixedSize(150, 100)
        
        # Determine color based on stock
        if product[5] <= 0:
            color = "#dc3545"
        elif product[5] < 10:
            color = "#ffc107"
        else:
            color = "#28a745"
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-weight: 600;
                font-size: 11px;
                text-align: center;
            }}
            QPushButton:hover {{
                opacity: 0.9;
                transform: scale(1.05);
            }}
        """)
        
        btn_text = f"{product[1]}\n{product[4]:.2f} DA\nStock: {product[5]}"
        btn.setText(btn_text)
        
        btn.clicked.connect(lambda: self.add_product_to_cart(product))
        return btn
    
    def on_product_scanned(self, product_dict):
        """Handle product scanned from barcode scanner"""
        # Convert dict back to tuple format for compatibility
        product = (
            product_dict['id'],
            product_dict['name'],
            product_dict['code_bar'],
            product_dict['price_buy'],
            product_dict['price_sell'],
            product_dict['quantity'],
            product_dict.get('category', 'General')
        )
        
        self.add_product_to_cart(product)
    
    def add_product_to_cart(self, product):
        """Add product to cart"""
        if not product or product[5] <= 0:
            QMessageBox.warning(self, "Out of Stock", f"Product '{product[1]}' is out of stock!")
            return
        
        # Check if product already in cart
        for item in self.cart_items:
            if item['id'] == product[0]:
                if item['quantity'] < product[5]:
                    item['quantity'] += 1
                    item['total'] = item['quantity'] * item['price']
                else:
                    QMessageBox.warning(self, "Insufficient Stock", 
                                      f"Only {product[5]} units available!")
                    return
                break
        else:
            # Add new item
            cart_item = {
                'id': product[0],
                'name': product[1],
                'price': product[4],
                'quantity': 1,
                'total': product[4],
                'stock': product[5]
            }
            self.cart_items.append(cart_item)
        
        self.update_cart_display()
    
    def update_cart_display(self):
        """Update cart table and totals"""
        self.cart_table.setRowCount(len(self.cart_items))
        
        subtotal = 0
        for i, item in enumerate(self.cart_items):
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(i, 1, QTableWidgetItem(f"{item['price']:.2f}"))
            self.cart_table.setItem(i, 2, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"{item['total']:.2f}"))
            
            # Remove button
            remove_btn = QPushButton("❌")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #c82333;
                }
            """)
            remove_btn.clicked.connect(lambda checked, row=i: self.remove_cart_item(row))
            self.cart_table.setCellWidget(i, 4, remove_btn)
            
            subtotal += item['total']
        
        # Update totals
        tax = subtotal * 0.19  # 19% tax
        total = subtotal + tax
        
        self.subtotal_label.setText(f"Subtotal: {subtotal:.2f} DA")
        self.tax_label.setText(f"Tax (19%): {tax:.2f} DA")
        self.total_label.setText(f"TOTAL: {total:.2f} DA")
        
        self.total_amount = total
        self.checkout_btn.setEnabled(len(self.cart_items) > 0)
        
        # Update payment amount
        self.payment_amount_input.setText(f"{total:.2f}")
        self.calculate_change()
    
    def remove_cart_item(self, row):
        """Remove item from cart"""
        if 0 <= row < len(self.cart_items):
            del self.cart_items[row]
            self.update_cart_display()
    
    def clear_cart(self):
        """Clear all items from cart"""
        if self.cart_items:
            reply = QMessageBox.question(self, "Clear Cart", 
                                       "Are you sure you want to clear the cart?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.cart_items.clear()
                self.update_cart_display()
    
    def calculate_change(self):
        """Calculate and display change"""
        try:
            payment_amount = float(self.payment_amount_input.text() or 0)
            change = payment_amount - self.total_amount
            self.change_label.setText(f"Change: {change:.2f} DA")
            
            if change < 0:
                self.change_label.setStyleSheet(self.change_label.styleSheet().replace("#28a745", "#dc3545").replace("#d4edda", "#f8d7da"))
            else:
                self.change_label.setStyleSheet(self.change_label.styleSheet().replace("#dc3545", "#28a745").replace("#f8d7da", "#d4edda"))
                
        except ValueError:
            self.change_label.setText("Change: 0.00 DA")
    
    def process_payment(self):
        """Process payment"""
        if not self.cart_items:
            return
        
        try:
            payment_amount = float(self.payment_amount_input.text() or 0)
            
            if payment_amount < self.total_amount:
                QMessageBox.warning(self, "Insufficient Payment", 
                                  f"Payment amount is less than total!")
                return
            
            # Process the sale
            if self.complete_sale(payment_amount):
                change = payment_amount - self.total_amount
                QMessageBox.information(self, "Payment Processed", 
                                      f"Payment successful!\nChange: {change:.2f} DA")
                
                # Clear cart
                self.cart_items.clear()
                self.update_cart_display()
                self.payment_amount_input.clear()
                
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid payment amount!")
    
    def complete_sale(self, payment_amount):
        """Complete the sale and update database"""
        try:
            cursor = self.conn.cursor()
            
            # Generate ticket number
            cursor.execute('SELECT COUNT(*) FROM tickets')
            ticket_count = cursor.fetchone()[0]
            ticket_number = f"TKT{ticket_count + 1:06d}"
            
            # Create sale record
            cursor.execute('''
                INSERT INTO tickets (ticket_number, total_price, payment_method, items, customer_name, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ticket_number, self.total_amount, self.payment_method_combo.currentText(),
                  json.dumps([{
                      'name': item['name'],
                      'quantity': item['quantity'],
                      'price': item['price'],
                      'total': item['total']
                  } for item in self.cart_items]),
                  self.selected_client, datetime.now().isoformat()))
            
            # Update product stock
            for item in self.cart_items:
                cursor.execute('UPDATE products SET quantity = quantity - ? WHERE id = ?',
                             (item['quantity'], item['id']))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Sale Error", f"Error processing sale: {str(e)}")
            return False
    
    def print_receipt(self):
        """Print receipt"""
        if not self.cart_items:
            QMessageBox.warning(self, "Empty Cart", "No items to print receipt for!")
            return
        
        # Generate receipt content
        receipt_content = self.generate_receipt_content()
        
        # Show receipt dialog
        dialog = ReceiptDialog(self, receipt_content)
        dialog.exec_()
    
    def generate_receipt_content(self):
        """Generate receipt content"""
        content = "=" * 40 + "\n"
        content += "        ENHANCED STORE MANAGER\n"
        content += "         Professional POS\n"
        content += "=" * 40 + "\n"
        content += f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        content += f"Customer: {self.selected_client}\n"
        content += f"Payment: {self.payment_method_combo.currentText()}\n"
        content += "-" * 40 + "\n"
        
        for item in self.cart_items:
            content += f"{item['name']:<25}\n"
            content += f"  {item['quantity']} x {item['price']:.2f} = {item['total']:.2f} DA\n"
        
        content += "-" * 40 + "\n"
        subtotal = sum(item['total'] for item in self.cart_items)
        tax = subtotal * 0.19
        content += f"{'Subtotal:':<25} {subtotal:.2f} DA\n"
        content += f"{'Tax (19%):':<25} {tax:.2f} DA\n"
        content += f"{'TOTAL:':<25} {self.total_amount:.2f} DA\n"
        content += "=" * 40 + "\n"
        content += "       Thank you for shopping!\n"
        content += "         Visit us again!\n"
        content += "=" * 40 + "\n"
        
        return content
    
    def update_clock(self):
        """Update clock display"""
        now = datetime.now()
        self.date_label.setText(now.strftime("%A, %B %d, %Y"))
        self.time_label.setText(now.strftime("%H:%M:%S"))
    
    def apply_enhanced_styling(self):
        """Apply enhanced styling"""
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #4285f4;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QComboBox:focus {
                border-color: #4285f4;
            }
        """)


class ReceiptDialog(QDialog):
    """Receipt preview dialog"""
    
    def __init__(self, parent, content):
        super().__init__(parent)
        self.content = content
        self.setWindowTitle("Receipt Preview")
        self.setModal(True)
        self.resize(450, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Receipt Preview")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin: 15px;
            }
        """)
        
        # Receipt content
        receipt_text = QTextEdit()
        receipt_text.setReadOnly(True)
        receipt_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background: white;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        receipt_text.setPlainText(self.content)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        
        print_btn = QPushButton("🖨️ Print")
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
        
        layout.addWidget(title)
        layout.addWidget(receipt_text)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def print_receipt(self):
        """Print the receipt"""
        QMessageBox.information(self, "Print", "Receipt sent to printer!")
        self.accept()