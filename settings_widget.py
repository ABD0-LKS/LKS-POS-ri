from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
import os

class SettingsWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.settings_file = "app_settings.json"
        self.settings = self.load_settings()
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Back to Main Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        back_btn.clicked.connect(self.parent.show_main_menu)
        
        title_label = QLabel("System Settings")
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            color: #333;
            margin-left: 20px;
        """)
        
        header_layout.addWidget(back_btn)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # POS Interface Settings
        pos_group = QGroupBox("POS Interface Settings")
        pos_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        pos_layout = QVBoxLayout()
        
        # POS Version Selection
        pos_version_layout = QHBoxLayout()
        pos_version_label = QLabel("POS Interface Version:")
        pos_version_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #495057;")
        
        self.pos_version_combo = QComboBox()
        self.pos_version_combo.addItems(["Enhanced POS (Git Version)", "Simple POS (Current Version)"])
        self.pos_version_combo.setCurrentText(self.settings.get('pos_version', 'Enhanced POS (Git Version)'))
        self.pos_version_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #4285f4;
            }
        """)
        
        pos_version_layout.addWidget(pos_version_label)
        pos_version_layout.addWidget(self.pos_version_combo)
        pos_version_layout.addStretch()
        
        # Description
        pos_description = QLabel("""
Enhanced POS: Advanced interface with barcode scanning, product images, and modern UI
Simple POS: Basic interface with essential POS functionality
        """)
        pos_description.setStyleSheet("color: #6c757d; font-size: 12px; margin: 10px 0;")
        
        pos_layout.addLayout(pos_version_layout)
        pos_layout.addWidget(pos_description)
        pos_group.setLayout(pos_layout)
        
        # Barcode Scanner Settings
        barcode_group = QGroupBox("Barcode Scanner Settings")
        barcode_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        barcode_layout = QVBoxLayout()
        
        # Auto-scan enable
        self.auto_scan_checkbox = QCheckBox("Enable Automatic Barcode Scanning")
        self.auto_scan_checkbox.setChecked(self.settings.get('auto_scan_enabled', True))
        self.auto_scan_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: 600;
                color: #495057;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #6c757d;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #28a745;
                border-radius: 3px;
                background: #28a745;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
        """)
        
        # Camera selection
        camera_layout = QHBoxLayout()
        camera_label = QLabel("Camera Device:")
        camera_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #495057;")
        
        self.camera_combo = QComboBox()
        self.camera_combo.addItems(["Default Camera (0)", "USB Camera (1)", "External Camera (2)"])
        self.camera_combo.setCurrentText(self.settings.get('camera_device', 'Default Camera (0)'))
        self.camera_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 200px;
            }
        """)
        
        camera_layout.addWidget(camera_label)
        camera_layout.addWidget(self.camera_combo)
        camera_layout.addStretch()
        
        # Scan timeout
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("Scan Timeout (seconds):")
        timeout_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #495057;")
        
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(5, 60)
        self.timeout_spinbox.setValue(self.settings.get('scan_timeout', 30))
        self.timeout_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 10px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 100px;
            }
        """)
        
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_spinbox)
        timeout_layout.addStretch()
        
        # Sound settings
        self.sound_enabled_checkbox = QCheckBox("Enable Scanner Sound Effects")
        self.sound_enabled_checkbox.setChecked(self.settings.get('sound_enabled', True))
        self.sound_enabled_checkbox.setStyleSheet(self.auto_scan_checkbox.styleSheet())
        
        # Test camera button
        test_camera_btn = QPushButton("🎥 Test Camera")
        test_camera_btn.setStyleSheet("""
            QPushButton {
                background: #17a2b8;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #138496;
            }
        """)
        test_camera_btn.clicked.connect(self.test_camera)
        
        barcode_layout.addWidget(self.auto_scan_checkbox)
        barcode_layout.addLayout(camera_layout)
        barcode_layout.addLayout(timeout_layout)
        barcode_layout.addWidget(self.sound_enabled_checkbox)
        barcode_layout.addWidget(test_camera_btn)
        barcode_group.setLayout(barcode_layout)
        
        # Store Settings
        store_group = QGroupBox("Store Information")
        store_group.setStyleSheet(pos_group.styleSheet())
        store_layout = QFormLayout()
        
        self.store_name_input = QLineEdit()
        self.store_name_input.setText(self.settings.get('store_name', 'Smart Store'))
        
        self.store_address_input = QLineEdit()
        self.store_address_input.setText(self.settings.get('store_address', '123 Business Street'))
        
        self.store_phone_input = QLineEdit()
        self.store_phone_input.setText(self.settings.get('store_phone', '+1 555 123 4567'))
        
        self.currency_input = QLineEdit()
        self.currency_input.setText(self.settings.get('currency', 'DA'))
        
        input_style = """
            QLineEdit {
                padding: 10px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #4285f4;
            }
        """
        
        self.store_name_input.setStyleSheet(input_style)
        self.store_address_input.setStyleSheet(input_style)
        self.store_phone_input.setStyleSheet(input_style)
        self.currency_input.setStyleSheet(input_style)
        
        store_layout.addRow("Store Name:", self.store_name_input)
        store_layout.addRow("Address:", self.store_address_input)
        store_layout.addRow("Phone:", self.store_phone_input)
        store_layout.addRow("Currency:", self.currency_input)
        store_group.setLayout(store_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #c82333;
            }
        """)
        reset_btn.clicked.connect(self.reset_settings)
        
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        save_btn.clicked.connect(self.save_settings)
        
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        
        # Add all sections to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(pos_group)
        main_layout.addWidget(barcode_group)
        main_layout.addWidget(store_group)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def load_settings(self):
        """Load settings from file"""
        default_settings = {
            'pos_version': 'Enhanced POS (Git Version)',
            'auto_scan_enabled': True,
            'camera_device': 'Default Camera (0)',
            'scan_timeout': 30,
            'sound_enabled': True,
            'store_name': 'Smart Store',
            'store_address': '123 Business Street',
            'store_phone': '+1 555 123 4567',
            'currency': 'DA'
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    default_settings.update(settings)
            return default_settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            return default_settings
    
    def save_settings(self):
        """Save current settings"""
        try:
            settings = {
                'pos_version': self.pos_version_combo.currentText(),
                'auto_scan_enabled': self.auto_scan_checkbox.isChecked(),
                'camera_device': self.camera_combo.currentText(),
                'scan_timeout': self.timeout_spinbox.value(),
                'sound_enabled': self.sound_enabled_checkbox.isChecked(),
                'store_name': self.store_name_input.text(),
                'store_address': self.store_address_input.text(),
                'store_phone': self.store_phone_input.text(),
                'currency': self.currency_input.text()
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            self.settings = settings
            
            # Update database settings if needed
            self.update_database_settings()
            
            QMessageBox.information(self, "Settings Saved", 
                                  "Settings have been saved successfully!\n\n"
                                  "Note: POS interface changes will take effect after restart.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
    
    def update_database_settings(self):
        """Update database with store settings"""
        try:
            cursor = self.parent.conn.cursor()
            
            settings_to_update = [
                ('store_name', self.store_name_input.text()),
                ('store_address', self.store_address_input.text()),
                ('store_phone', self.store_phone_input.text()),
                ('currency', self.currency_input.text())
            ]
            
            for key, value in settings_to_update:
                cursor.execute('''
                    INSERT OR REPLACE INTO settings (key, value)
                    VALUES (?, ?)
                ''', (key, value))
            
            self.parent.conn.commit()
            
        except Exception as e:
            print(f"Error updating database settings: {e}")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(self, "Reset Settings", 
                                   "Are you sure you want to reset all settings to defaults?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Reset UI elements
            self.pos_version_combo.setCurrentText('Enhanced POS (Git Version)')
            self.auto_scan_checkbox.setChecked(True)
            self.camera_combo.setCurrentText('Default Camera (0)')
            self.timeout_spinbox.setValue(30)
            self.sound_enabled_checkbox.setChecked(True)
            self.store_name_input.setText('Smart Store')
            self.store_address_input.setText('123 Business Street')
            self.store_phone_input.setText('+1 555 123 4567')
            self.currency_input.setText('DA')
            
            # Remove settings file
            try:
                if os.path.exists(self.settings_file):
                    os.remove(self.settings_file)
                QMessageBox.information(self, "Settings Reset", "Settings have been reset to defaults.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to reset settings: {str(e)}")
    
    def test_camera(self):
        """Test camera functionality"""
        try:
            # Try to import camera libraries
            import cv2
            
            # Get camera index from selection
            camera_text = self.camera_combo.currentText()
            if "0" in camera_text:
                camera_index = 0
            elif "1" in camera_text:
                camera_index = 1
            elif "2" in camera_text:
                camera_index = 2
            else:
                camera_index = 0
            
            # Test camera
            cap = cv2.VideoCapture(camera_index)
            
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                
                if ret:
                    QMessageBox.information(self, "Camera Test", 
                                          f"Camera {camera_index} is working correctly!")
                else:
                    QMessageBox.warning(self, "Camera Test", 
                                      f"Camera {camera_index} opened but failed to capture frame.")
            else:
                QMessageBox.warning(self, "Camera Test", 
                                  f"Failed to open camera {camera_index}.")
                
        except ImportError:
            QMessageBox.warning(self, "Camera Test", 
                              "Camera libraries not installed.\n"
                              "Please install opencv-python to use camera features.")
        except Exception as e:
            QMessageBox.critical(self, "Camera Test", f"Camera test failed: {str(e)}")
    
    def get_setting(self, key, default=None):
        """Get a specific setting value"""
        return self.settings.get(key, default)