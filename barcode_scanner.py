"""
Barcode Scanner Module for POS System
Provides barcode scanning capabilities using camera and input validation
"""

import sys
import sqlite3
import json
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import re
import os
from PyQt5.QtMultimedia import QSound

# Try to import camera scanning libraries
try:
    import cv2
    import numpy as np
    from pyzbar import pyzbar
    CAMERA_AVAILABLE = True
    print("Camera scanning available")
except ImportError:
    CAMERA_AVAILABLE = False
    print("Camera scanning not available. Install opencv-python and pyzbar for camera support.")

class BarcodeHandler(QObject):
    """Handles barcode operations and database interactions"""
    
    def __init__(self, database_connection):
        super().__init__()
        self.conn = database_connection
        self.sound_enabled = True
        
        # Initialize sound files (optional)
        self.success_sound_path = "sounds/beep_success.wav"
        self.error_sound_path = "sounds/beep_error.wav"
    
    def search_product_by_barcode(self, barcode):
        """Search for product by exact barcode match"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM products WHERE code_bar = ?', (barcode,))
            result = cursor.fetchone()
            
            if result:
                # Log successful scan
                self.log_barcode_scan(barcode, result[0], True)
            
            return result
        except Exception as e:
            print(f"Error searching product by barcode: {e}")
            return None
    
    def search_product_by_name_or_code(self, search_term):
        """Search for products by name or partial barcode"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM products 
                WHERE LOWER(name) LIKE LOWER(?) 
                   OR code_bar LIKE ?
                   OR LOWER(category) LIKE LOWER(?)
                ORDER BY 
                    CASE 
                        WHEN code_bar = ? THEN 1
                        WHEN LOWER(name) = LOWER(?) THEN 2
                        WHEN LOWER(name) LIKE LOWER(?) THEN 3
                        ELSE 4
                    END,
                    name
                LIMIT 10
            ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%',
                  search_term, search_term, f'{search_term}%'))
            
            return cursor.fetchall()
        except Exception as e:
            print(f"Error searching products: {e}")
            return []
    
    def update_product_stock(self, product_id, quantity_sold):
        """Update product stock after sale"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE products 
                SET quantity = quantity - ? 
                WHERE id = ? AND quantity >= ?
            ''', (quantity_sold, product_id, quantity_sold))
            
            if cursor.rowcount > 0:
                self.conn.commit()
                return True
            else:
                print(f"Insufficient stock for product ID {product_id}")
                return False
        except Exception as e:
            print(f"Error updating product stock: {e}")
            return False
    
    def log_barcode_scan(self, barcode, product_id, success):
        """Log barcode scan attempt"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO barcode_scans (barcode, product_id, success, scan_time)
                VALUES (?, ?, ?, datetime('now'))
            ''', (barcode, product_id if success else None, success))
            self.conn.commit()
        except Exception as e:
            print(f"Error logging barcode scan: {e}")
    
    def get_scan_statistics(self):
        """Get barcode scanning statistics"""
        try:
            cursor = self.conn.cursor()
            
            # Total scans
            cursor.execute('SELECT COUNT(*) FROM barcode_scans')
            total_scans = cursor.fetchone()[0]
            
            # Successful scans
            cursor.execute('SELECT COUNT(*) FROM barcode_scans WHERE success = 1')
            successful_scans = cursor.fetchone()[0]
            
            # Most scanned products
            cursor.execute('''
                SELECT p.name, COUNT(*) as scan_count
                FROM barcode_scans bs
                JOIN products p ON bs.product_id = p.id
                WHERE bs.success = 1
                GROUP BY bs.product_id
                ORDER BY scan_count DESC
                LIMIT 5
            ''')
            top_products = cursor.fetchall()
            
            return {
                'total_scans': total_scans,
                'successful_scans': successful_scans,
                'success_rate': (successful_scans / total_scans * 100) if total_scans > 0 else 0,
                'top_products': top_products
            }
        except Exception as e:
            print(f"Error getting scan statistics: {e}")
            return None
    
    def play_success_sound(self):
        """Play success sound"""
        if self.sound_enabled:
            try:
                if os.path.exists(self.success_sound_path):
                    QSound.play(self.success_sound_path)
                else:
                    # System beep as fallback
                    print("\a")  # ASCII bell character
            except Exception as e:
                print(f"Error playing success sound: {e}")
    
    def play_error_sound(self):
        """Play error sound"""
        if self.sound_enabled:
            try:
                if os.path.exists(self.error_sound_path):
                    QSound.play(self.error_sound_path)
                else:
                    # System beep as fallback (different pattern)
                    print("\a\a")  # Double beep for error
            except Exception as e:
                print(f"Error playing error sound: {e}")
    
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.sound_enabled = not self.sound_enabled
        return self.sound_enabled


class BarcodeScanner(QThread):
    """Camera-based barcode scanner thread"""
    
    barcode_detected = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.camera_available = False
        
        # Try to import camera libraries
        try:
            import cv2
            from pyzbar import pyzbar
            self.cv2 = cv2
            self.pyzbar = pyzbar
            self.camera_available = True
        except ImportError as e:
            self.camera_available = False
            print(f"Camera libraries not available: {e}")
    
    def run(self):
        """Main scanning loop"""
        if not self.camera_available:
            self.error_occurred.emit("Camera libraries not installed. Please install opencv-python and pyzbar.")
            return
        
        try:
            # Initialize camera
            cap = self.cv2.VideoCapture(0)
            
            if not cap.isOpened():
                self.error_occurred.emit("Could not open camera")
                return
            
            self.running = True
            
            while self.running:
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Decode barcodes in the frame
                barcodes = self.pyzbar.decode(frame)
                
                for barcode in barcodes:
                    # Extract barcode data
                    barcode_data = barcode.data.decode('utf-8')
                    barcode_type = barcode.type
                    
                    # Emit signal with detected barcode
                    self.barcode_detected.emit(barcode_data)
                    
                    # Stop after first successful detection
                    self.running = False
                    break
                
                # Small delay to prevent excessive CPU usage
                self.msleep(100)
            
            cap.release()
            
        except Exception as e:
            self.error_occurred.emit(f"Camera scanning error: {str(e)}")
    
    def stop_scanning(self):
        """Stop the scanning process"""
        self.running = False
    
    def is_camera_available(self):
        """Check if camera is available"""
        return self.camera_available


class ProductImageHandler:
    """Handles product images for barcode scanning"""
    
    def __init__(self, images_directory="product_images"):
        self.images_dir = images_directory
        
        # Create images directory if it doesn't exist
        if not os.path.exists(self.images_dir):
            try:
                os.makedirs(self.images_dir)
            except Exception as e:
                print(f"Could not create images directory: {e}")
    
    def has_product_image(self, product_id, barcode=None):
        """Check if product has an associated image"""
        image_path = self.get_product_image_path(product_id, barcode)
        return os.path.exists(image_path)
    
    def get_product_image_path(self, product_id, barcode=None):
        """Get the file path for a product image"""
        # Try different naming conventions
        possible_names = [
            f"product_{product_id}.jpg",
            f"product_{product_id}.png",
            f"product_{product_id}.jpeg"
        ]
        
        if barcode:
            possible_names.extend([
                f"barcode_{barcode}.jpg",
                f"barcode_{barcode}.png",
                f"barcode_{barcode}.jpeg"
            ])
        
        for name in possible_names:
            path = os.path.join(self.images_dir, name)
            if os.path.exists(path):
                return path
        
        # Return default path (may not exist)
        return os.path.join(self.images_dir, f"product_{product_id}.jpg")
    
    def save_product_image(self, product_id, image_data, barcode=None):
        """Save product image"""
        try:
            image_path = os.path.join(self.images_dir, f"product_{product_id}.jpg")
            
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            return image_path
        except Exception as e:
            print(f"Error saving product image: {e}")
            return None
    
    def delete_product_image(self, product_id, barcode=None):
        """Delete product image"""
        try:
            image_path = self.get_product_image_path(product_id, barcode)
            if os.path.exists(image_path):
                os.remove(image_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting product image: {e}")
            return False


class BarcodeInputValidator:
    """Validates and cleans barcode input"""
    
    @staticmethod
    def clean_barcode(barcode):
        """Clean barcode input by removing unwanted characters"""
        if not barcode:
            return ""
        
        # Remove whitespace and convert to uppercase
        cleaned = barcode.strip().upper()
        
        # Remove common prefixes that scanners might add
        prefixes_to_remove = ['CODE:', 'BARCODE:', 'UPC:', 'EAN:']
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        return cleaned
    
    @staticmethod
    def is_valid_barcode(barcode):
        """Check if barcode format is valid"""
        if not barcode:
            return False
        
        # Allow alphanumeric characters, hyphens, and underscores
        # Length should be between 3 and 50 characters
        pattern = r'^[A-Z0-9\-_]{3,50}$'
        return bool(re.match(pattern, barcode))
    
    @staticmethod
    def get_barcode_type(barcode):
        """Determine barcode type based on format"""
        if not barcode:
            return "UNKNOWN"
        
        length = len(barcode)
        
        if length == 8 and barcode.isdigit():
            return "EAN-8"
        elif length == 13 and barcode.isdigit():
            return "EAN-13"
        elif length == 12 and barcode.isdigit():
            return "UPC-A"
        elif length in [6, 7, 8] and barcode.isdigit():
            return "UPC-E"
        elif re.match(r'^[0-9]{1,14}$', barcode):
            return "NUMERIC"
        elif re.match(r'^[A-Z0-9\-_]+$', barcode):
            return "ALPHANUMERIC"
        else:
            return "CUSTOM"


class BarcodeDialog(QDialog):
    """Dialog for barcode scanning and input"""
    
    def __init__(self, parent=None, title="Scan Barcode"):
        super().__init__(parent)
        self.barcode = ""
        self.scanner = None
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Barcode Scanner")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 20px;
        """)
        layout.addWidget(title_label)
        
        # Manual input
        input_group = QGroupBox("Manual Input")
        input_layout = QVBoxLayout()
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Enter or scan barcode...")
        self.barcode_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
            }
            QLineEdit:focus {
                border-color: #2980b9;
            }
        """)
        self.barcode_input.returnPressed.connect(self.accept_barcode)
        
        input_layout.addWidget(self.barcode_input)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Camera scanning
        if CAMERA_AVAILABLE:
            camera_group = QGroupBox("Camera Scanning")
            camera_layout = QVBoxLayout()
            
            self.camera_btn = QPushButton("📷 Start Camera Scan")
            self.camera_btn.setStyleSheet("""
                QPushButton {
                    background: #27ae60;
                    color: white;
                    padding: 12px;
                    font-size: 14px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background: #229954;
                }
            """)
            self.camera_btn.clicked.connect(self.toggle_camera_scan)
            
            self.camera_status = QLabel("Camera ready")
            self.camera_status.setAlignment(Qt.AlignCenter)
            self.camera_status.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            
            camera_layout.addWidget(self.camera_btn)
            camera_layout.addWidget(self.camera_status)
            camera_group.setLayout(camera_layout)
            layout.addWidget(camera_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept_barcode)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        ok_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.barcode_input.setFocus()
    
    def toggle_camera_scan(self):
        """Toggle camera scanning"""
        if not CAMERA_AVAILABLE:
            QMessageBox.warning(self, "Camera Not Available", 
                              "Camera scanning requires opencv-python and pyzbar packages.")
            return
        
        if not self.scanner or not self.scanner.isRunning():
            self.start_camera_scan()
        else:
            self.stop_camera_scan()
    
    def start_camera_scan(self):
        """Start camera scanning"""
        try:
            self.scanner = BarcodeScanner()
            self.scanner.barcode_detected.connect(self.on_barcode_detected)
            self.scanner.error_occurred.connect(self.on_camera_error)
            
            self.scanner.start()
            self.camera_btn.setText("⏹️ Stop Camera Scan")
            self.camera_status.setText("Scanning... Point camera at barcode")
            self.camera_status.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold;")
            
        except Exception as e:
            QMessageBox.critical(self, "Camera Error", f"Failed to start camera: {str(e)}")
    
    def stop_camera_scan(self):
        """Stop camera scanning"""
        if self.scanner:
            self.scanner.stop_scanning()
            self.scanner = None
        
        self.camera_btn.setText("📷 Start Camera Scan")
        self.camera_status.setText("Camera ready")
        self.camera_status.setStyleSheet("color: #7f8c8d; font-size: 12px;")
    
    def on_barcode_detected(self, barcode):
        """Handle barcode detection from camera"""
        self.barcode_input.setText(barcode)
        self.stop_camera_scan()
        self.accept_barcode()
    
    def on_camera_error(self, error_message):
        """Handle camera errors"""
        self.stop_camera_scan()
        QMessageBox.warning(self, "Camera Error", error_message)
    
    def accept_barcode(self):
        """Accept the barcode input"""
        barcode = self.barcode_input.text().strip()
        
        if not barcode:
            QMessageBox.warning(self, "No Barcode", "Please enter or scan a barcode.")
            return
        
        # Validate barcode
        cleaned_barcode = BarcodeInputValidator.clean_barcode(barcode)
        if not BarcodeInputValidator.is_valid_barcode(cleaned_barcode):
            QMessageBox.warning(self, "Invalid Barcode", "The barcode format is invalid.")
            return
        
        self.barcode = cleaned_barcode
        self.accept()
    
    def get_barcode(self):
        """Get the scanned/entered barcode"""
        return self.barcode
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        self.stop_camera_scan()
        event.accept()


class BarcodeGeneratorDialog(QDialog):
    """Dialog for generating barcodes for products"""
    
    def __init__(self, parent=None, product_name=""):
        super().__init__(parent)
        self.product_name = product_name
        self.generated_barcode = ""
        self.setWindowTitle("Generate Barcode")
        self.setModal(True)
        self.setFixedSize(400, 350)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Barcode Generator")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 20px;
        """)
        layout.addWidget(title_label)
        
        # Product info
        if self.product_name:
            product_label = QLabel(f"Product: {self.product_name}")
            product_label.setAlignment(Qt.AlignCenter)
            product_label.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-bottom: 15px;")
            layout.addWidget(product_label)
        
        # Generation options
        options_group = QGroupBox("Barcode Options")
        options_layout = QFormLayout()
        
        # Barcode type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["EAN-13", "EAN-8", "UPC-A", "Custom"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        
        # Prefix
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("Optional prefix")
        self.prefix_input.setMaxLength(6)
        
        options_layout.addRow("Type:", self.type_combo)
        options_layout.addRow("Prefix:", self.prefix_input)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Generated barcode display
        display_group = QGroupBox("Generated Barcode")
        display_layout = QVBoxLayout()
        
        self.barcode_display = QLineEdit()
        self.barcode_display.setReadOnly(True)
        self.barcode_display.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 16px;
                font-family: 'Courier New', monospace;
                background: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
            }
        """)
        
        generate_btn = QPushButton("Generate New Barcode")
        generate_btn.clicked.connect(self.generate_barcode)
        generate_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        
        display_layout.addWidget(self.barcode_display)
        display_layout.addWidget(generate_btn)
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        use_btn = QPushButton("Use This Barcode")
        use_btn.clicked.connect(self.accept_barcode)
        use_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(use_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Generate initial barcode
        self.generate_barcode()
    
    def on_type_changed(self):
        """Handle barcode type change"""
        self.generate_barcode()
    
    def generate_barcode(self):
        """Generate a new barcode"""
        import random
        import time
        
        barcode_type = self.type_combo.currentText()
        prefix = self.prefix_input.text().strip()
        
        # Generate based on type
        if barcode_type == "EAN-13":
            # Generate 13-digit EAN
            if prefix:
                remaining_digits = 13 - len(prefix)
                if remaining_digits > 0:
                    random_part = ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
                    barcode = prefix + random_part
                else:
                    barcode = prefix[:13]
            else:
                barcode = ''.join([str(random.randint(0, 9)) for _ in range(13)])
        
        elif barcode_type == "EAN-8":
            # Generate 8-digit EAN
            if prefix:
                remaining_digits = 8 - len(prefix)
                if remaining_digits > 0:
                    random_part = ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
                    barcode = prefix + random_part
                else:
                    barcode = prefix[:8]
            else:
                barcode = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        
        elif barcode_type == "UPC-A":
            # Generate 12-digit UPC
            if prefix:
                remaining_digits = 12 - len(prefix)
                if remaining_digits > 0:
                    random_part = ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
                    barcode = prefix + random_part
                else:
                    barcode = prefix[:12]
            else:
                barcode = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        
        else:  # Custom
            # Generate custom barcode with timestamp
            timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
            if prefix:
                barcode = f"{prefix}{timestamp}"
            else:
                barcode = f"PRD{timestamp}"
        
        self.barcode_display.setText(barcode)
        self.generated_barcode = barcode
    
    def accept_barcode(self):
        """Accept the generated barcode"""
        if not self.generated_barcode:
            QMessageBox.warning(self, "No Barcode", "Please generate a barcode first.")
            return
        
        self.accept()
    
    def get_barcode(self):
        """Get the generated barcode"""
        return self.generated_barcode


# Utility functions
def validate_barcode_checksum(barcode):
    """Validate barcode checksum for EAN/UPC codes"""
    if not barcode or not barcode.isdigit():
        return False
    
    if len(barcode) == 13:  # EAN-13
        # Calculate checksum
        odd_sum = sum(int(barcode[i]) for i in range(0, 12, 2))
        even_sum = sum(int(barcode[i]) for i in range(1, 12, 2))
        checksum = (10 - ((odd_sum + even_sum * 3) % 10)) % 10
        return checksum == int(barcode[12])
    
    elif len(barcode) == 12:  # UPC-A
        # Calculate checksum
        odd_sum = sum(int(barcode[i]) for i in range(0, 11, 2))
        even_sum = sum(int(barcode[i]) for i in range(1, 11, 2))
        checksum = (10 - ((odd_sum * 3 + even_sum) % 10)) % 10
        return checksum == int(barcode[11])
    
    return True  # For other formats, assume valid


def generate_barcode_suggestions(partial_barcode, database_connection):
    """Generate barcode suggestions based on partial input"""
    try:
        cursor = database_connection.cursor()
        cursor.execute('''
            SELECT DISTINCT code_bar FROM products 
            WHERE code_bar LIKE ? AND code_bar IS NOT NULL
            ORDER BY code_bar
            LIMIT 10
        ''', (f'{partial_barcode}%',))
        
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error generating barcode suggestions: {e}")
        return []


def format_barcode_for_display(barcode):
    """Format barcode for display purposes"""
    if not barcode:
        return "N/A"
    
    # Add spacing for common barcode formats
    if len(barcode) == 13 and barcode.isdigit():  # EAN-13
        return f"{barcode[0]} {barcode[1:7]} {barcode[7:13]}"
    elif len(barcode) == 12 and barcode.isdigit():  # UPC-A
        return f"{barcode[0]} {barcode[1:6]} {barcode[6:11]} {barcode[11]}"
    else:
        return barcode


# Test functions
def test_barcode_scanner():
    """Test the barcode scanner functionality"""
    app = QApplication(sys.argv)
    
    # Test barcode dialog
    dialog = BarcodeDialog(None, "Test Barcode Scanner")
    if dialog.exec_() == QDialog.Accepted:
        print(f"Scanned barcode: {dialog.get_barcode()}")
    
    sys.exit(app.exec_())


def test_barcode_generator():
    """Test the barcode generator"""
    app = QApplication(sys.argv)
    
    # Test generator dialog
    dialog = BarcodeGeneratorDialog(None, "Test Product")
    if dialog.exec_() == QDialog.Accepted:
        print(f"Generated barcode: {dialog.get_barcode()}")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "generator":
        test_barcode_generator()
    else:
        test_barcode_scanner()
