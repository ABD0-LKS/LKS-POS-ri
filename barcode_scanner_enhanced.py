"""
Enhanced Barcode Scanner with Automatic Scanning
Supports continuous scanning and automatic product detection
"""

import sys
import cv2
import numpy as np
from pyzbar import pyzbar
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
import os
from datetime import datetime

class AutoBarcodeScanner(QThread):
    """Automatic barcode scanner that continuously scans for barcodes"""
    
    barcode_detected = pyqtSignal(str, str)  # barcode, barcode_type
    frame_ready = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    scanner_status = pyqtSignal(str)
    
    def __init__(self, camera_index=0, scan_timeout=30):
        super().__init__()
        self.camera_index = camera_index
        self.scan_timeout = scan_timeout
        self.running = False
        self.paused = False
        self.last_barcode = ""
        self.last_scan_time = 0
        self.duplicate_prevention_time = 2  # seconds
        
        # Scanner settings
        self.settings = self.load_scanner_settings()
    
    def load_scanner_settings(self):
        """Load scanner settings"""
        try:
            if os.path.exists("app_settings.json"):
                with open("app_settings.json", 'r') as f:
                    return json.load(f)
        except:
            pass
        
        return {
            'auto_scan_enabled': True,
            'sound_enabled': True,
            'scan_timeout': 30,
            'duplicate_prevention': True
        }
    
    def run(self):
        """Main scanning loop"""
        try:
            # Initialize camera
            cap = cv2.VideoCapture(self.camera_index)
            
            if not cap.isOpened():
                self.error_occurred.emit(f"Could not open camera {self.camera_index}")
                return
            
            # Set camera properties for better scanning
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.running = True
            self.scanner_status.emit("Scanner started - Point camera at barcode")
            
            frame_count = 0
            
            while self.running:
                if self.paused:
                    self.msleep(100)
                    continue
                
                ret, frame = cap.read()
                
                if not ret:
                    self.msleep(50)
                    continue
                
                # Emit frame for display
                self.frame_ready.emit(frame.copy())
                
                # Process every 3rd frame for performance
                frame_count += 1
                if frame_count % 3 != 0:
                    self.msleep(33)  # ~30 FPS
                    continue
                
                # Decode barcodes
                barcodes = pyzbar.decode(frame)
                
                for barcode in barcodes:
                    barcode_data = barcode.data.decode('utf-8')
                    barcode_type = barcode.type
                    
                    # Check for duplicate prevention
                    current_time = datetime.now().timestamp()
                    if (self.settings.get('duplicate_prevention', True) and 
                        barcode_data == self.last_barcode and 
                        current_time - self.last_scan_time < self.duplicate_prevention_time):
                        continue
                    
                    # Valid new barcode detected
                    self.last_barcode = barcode_data
                    self.last_scan_time = current_time
                    
                    self.barcode_detected.emit(barcode_data, barcode_type)
                    self.scanner_status.emit(f"Barcode detected: {barcode_data}")
                    
                    # Brief pause after detection
                    self.msleep(500)
                    break
                
                self.msleep(33)  # ~30 FPS
            
            cap.release()
            self.scanner_status.emit("Scanner stopped")
            
        except Exception as e:
            self.error_occurred.emit(f"Scanner error: {str(e)}")
    
    def stop_scanning(self):
        """Stop the scanning process"""
        self.running = False
        self.wait()
    
    def pause_scanning(self):
        """Pause scanning temporarily"""
        self.paused = True
        self.scanner_status.emit("Scanner paused")
    
    def resume_scanning(self):
        """Resume scanning"""
        self.paused = False
        self.scanner_status.emit("Scanner resumed")
    
    def is_running(self):
        """Check if scanner is running"""
        return self.running and self.isRunning()


class BarcodeScannerWidget(QWidget):
    """Widget for displaying camera feed and scanner controls"""
    
    product_scanned = pyqtSignal(dict)  # Emit product data when found
    
    def __init__(self, parent, database_connection):
        super().__init__(parent)
        self.parent = parent
        self.conn = database_connection
        self.scanner = None
        self.settings = self.load_settings()
        self.init_ui()
        
        # Auto-start scanner if enabled
        if self.settings.get('auto_scan_enabled', True):
            self.start_scanner()
    
    def load_settings(self):
        """Load scanner settings"""
        try:
            if os.path.exists("app_settings.json"):
                with open("app_settings.json", 'r') as f:
                    return json.load(f)
        except:
            pass
        
        return {
            'auto_scan_enabled': True,
            'camera_device': 'Default Camera (0)',
            'scan_timeout': 30,
            'sound_enabled': True
        }
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Camera display
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(400, 300)
        self.camera_label.setStyleSheet("""
            QLabel {
                border: 2px solid #4285f4;
                border-radius: 8px;
                background: #f8f9fa;
                color: #6c757d;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setText("Camera Feed\nWaiting for scanner...")
        
        # Status label
        self.status_label = QLabel("Scanner Status: Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                background: #e9ecef;
                padding: 10px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                color: #495057;
            }
        """)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("📷 Start Scanner")
        self.start_btn.clicked.connect(self.start_scanner)
        
        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.clicked.connect(self.pause_scanner)
        self.pause_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_scanner)
        self.stop_btn.setEnabled(False)
        
        # Style buttons
        button_style = """
            QPushButton {
                background: #4285f4;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #3367d6;
            }
            QPushButton:disabled {
                background: #6c757d;
                color: #adb5bd;
            }
        """
        
        self.start_btn.setStyleSheet(button_style)
        self.pause_btn.setStyleSheet(button_style.replace("#4285f4", "#ffc107").replace("#3367d6", "#e0a800"))
        self.stop_btn.setStyleSheet(button_style.replace("#4285f4", "#dc3545").replace("#3367d6", "#c82333"))
        
        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.pause_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch()
        
        # Last scanned info
        self.last_scan_label = QLabel("Last Scanned: None")
        self.last_scan_label.setStyleSheet("""
            QLabel {
                background: #f8f9fa;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
                color: #6c757d;
            }
        """)
        
        layout.addWidget(self.camera_label)
        layout.addWidget(self.status_label)
        layout.addLayout(controls_layout)
        layout.addWidget(self.last_scan_label)
        
        self.setLayout(layout)
    
    def start_scanner(self):
        """Start the barcode scanner"""
        try:
            if self.scanner and self.scanner.is_running():
                return
            
            # Get camera index from settings
            camera_text = self.settings.get('camera_device', 'Default Camera (0)')
            if "0" in camera_text:
                camera_index = 0
            elif "1" in camera_text:
                camera_index = 1
            elif "2" in camera_text:
                camera_index = 2
            else:
                camera_index = 0
            
            # Create and start scanner
            self.scanner = AutoBarcodeScanner(
                camera_index=camera_index,
                scan_timeout=self.settings.get('scan_timeout', 30)
            )
            
            # Connect signals
            self.scanner.barcode_detected.connect(self.on_barcode_detected)
            self.scanner.frame_ready.connect(self.update_camera_display)
            self.scanner.error_occurred.connect(self.on_scanner_error)
            self.scanner.scanner_status.connect(self.update_status)
            
            self.scanner.start()
            
            # Update UI
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Scanner Error", f"Failed to start scanner: {str(e)}")
    
    def pause_scanner(self):
        """Pause the scanner"""
        if self.scanner:
            self.scanner.pause_scanning()
            self.pause_btn.setText("▶️ Resume")
            self.pause_btn.clicked.disconnect()
            self.pause_btn.clicked.connect(self.resume_scanner)
    
    def resume_scanner(self):
        """Resume the scanner"""
        if self.scanner:
            self.scanner.resume_scanning()
            self.pause_btn.setText("⏸️ Pause")
            self.pause_btn.clicked.disconnect()
            self.pause_btn.clicked.connect(self.pause_scanner)
    
    def stop_scanner(self):
        """Stop the scanner"""
        if self.scanner:
            self.scanner.stop_scanning()
            self.scanner = None
        
        # Update UI
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setText("⏸️ Pause")
        
        # Clear camera display
        self.camera_label.clear()
        self.camera_label.setText("Camera Feed\nScanner stopped")
    
    def update_camera_display(self, frame):
        """Update camera display with current frame"""
        try:
            # Convert frame to Qt format
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Scale to fit label
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                self.camera_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.camera_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Error updating camera display: {e}")
    
    def update_status(self, status):
        """Update status label"""
        self.status_label.setText(f"Scanner Status: {status}")
    
    def on_scanner_error(self, error):
        """Handle scanner errors"""
        self.status_label.setText(f"Scanner Error: {error}")
        QMessageBox.warning(self, "Scanner Error", error)
        self.stop_scanner()
    
    def on_barcode_detected(self, barcode, barcode_type):
        """Handle barcode detection"""
        self.last_scan_label.setText(f"Last Scanned: {barcode} ({barcode_type})")
        
        # Play sound if enabled
        if self.settings.get('sound_enabled', True):
            self.play_scan_sound()
        
        # Search for product in database
        self.search_product(barcode)
    
    def search_product(self, barcode):
        """Search for product by barcode"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM products WHERE code_bar = ?', (barcode,))
            product = cursor.fetchone()
            
            if product:
                # Convert to dict for easier handling
                product_dict = {
                    'id': product[0],
                    'name': product[1],
                    'code_bar': product[2],
                    'price_buy': product[3],
                    'price_sell': product[4],
                    'quantity': product[5],
                    'category': product[6] if len(product) > 6 else 'General'
                }
                
                # Emit product found signal
                self.product_scanned.emit(product_dict)
                
                # Update status
                self.status_label.setText(f"Product Found: {product[1]}")
                
            else:
                # Product not found
                self.status_label.setText(f"Product not found: {barcode}")
                QMessageBox.information(self, "Product Not Found", 
                                      f"No product found with barcode: {barcode}")
                
        except Exception as e:
            print(f"Error searching product: {e}")
            self.status_label.setText(f"Database error: {str(e)}")
    
    def play_scan_sound(self):
        """Play scan sound effect"""
        try:
            # Simple beep sound
            print("\a")  # System beep
        except:
            pass
    
    def closeEvent(self, event):
        """Handle widget close"""
        self.stop_scanner()
        event.accept()


class BarcodeTestDialog(QDialog):
    """Dialog for testing barcode scanner functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Barcode Scanner Test")
        self.setModal(True)
        self.resize(500, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Barcode Scanner Test")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                margin: 20px;
            }
        """)
        
        # Test area
        self.scanner_widget = BarcodeScannerWidget(self, None)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
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
        
        layout.addWidget(title)
        layout.addWidget(self.scanner_widget)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def closeEvent(self, event):
        """Handle dialog close"""
        if hasattr(self, 'scanner_widget'):
            self.scanner_widget.stop_scanner()
        event.accept()


# Test function
def test_barcode_scanner():
    """Test the barcode scanner"""
    app = QApplication(sys.argv)
    
    dialog = BarcodeTestDialog()
    dialog.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_barcode_scanner()