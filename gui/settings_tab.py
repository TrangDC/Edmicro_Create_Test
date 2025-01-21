from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QHBoxLayout, QFileDialog,
                             QFormLayout, QMessageBox)
from PyQt5.QtGui import QFont
import json
import os

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.excel_file_path = ""
        self.prompt_input = None
        self.gemini_input = None
        self.cloudinary_input = None
        self.init_ui()
        self.load_settings()
    def init_ui(self):
        # Layout chính cho tab Cài đặt
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)  # Giảm khoảng cách giữa các hàng
        
        # Form layout để căn chỉnh các widget
        form_layout = QFormLayout()
        form_layout.setSpacing(10) # Giảm khoảng cách giữa các dòng
        
        # Prompt template setup
        prompt_label = QLabel("Prompt_template:")
        prompt_label.setFont(QFont("Arial", 12))
        self.prompt_input = QLineEdit()
        self.prompt_input.setFont(QFont("Arial", 12))
        prompt_button = QPushButton("Chọn file")
        prompt_button.setFont(QFont("Arial", 12))
        prompt_button.clicked.connect(self.open_excel_dialog)
        
        # Thêm widget vào QFormLayout
        prompt_row_layout = QHBoxLayout() # Tạo layout chứa input và button
        prompt_row_layout.addWidget(self.prompt_input)
        prompt_row_layout.addWidget(prompt_button)
        form_layout.addRow(prompt_label, prompt_row_layout)

        # Gemini API Key input
        gemini_label = QLabel("Gemini API Key:")
        gemini_label.setFont(QFont("Arial", 12))
        self.gemini_input = QLineEdit()
        self.gemini_input.setFont(QFont("Arial", 12))
        form_layout.addRow(gemini_label, self.gemini_input)

        # Cloudinary Config input
        cloudinary_label = QLabel("Cloudinary Config:")
        cloudinary_label.setFont(QFont("Arial", 12))
        self.cloudinary_input = QLineEdit()
        self.cloudinary_input.setFont(QFont("Arial", 12))
        form_layout.addRow(cloudinary_label, self.cloudinary_input)
       
        settings_layout.addLayout(form_layout)

        # Save button
        self.save_button = QPushButton("Lưu cài đặt")
        self.save_button.setFont(QFont("Arial", 12))
        self.save_button.clicked.connect(self.save_settings)
        settings_layout.addWidget(self.save_button)
        
        # Set layout cho widget của tab Cài đặt
        self.setLayout(settings_layout)
        
    
    def open_excel_dialog(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Chọn file Excel", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.prompt_input.setText(file_path)
            self.excel_file_path = file_path
            
    def save_settings(self):
        settings = {
            "excel_file_path": self.excel_file_path,
            "gemini_api_key": self.gemini_input.text(),
            "cloudinary_config": self.cloudinary_input.text()
        }

        # Lấy thư mục của file đang chạy
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "settings.json")

        import json
        with open(file_path, 'w') as f:
            json.dump(settings, f, indent=4)
        
        # Load lại cài đặt
        self.load_settings()
        QMessageBox.information(self, "Thành công", f"Đã lưu cài đặt vào file JSON: {file_path}")
        
    def load_settings(self):
        # Lấy thư mục của file đang chạy
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "settings.json")

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    settings = json.load(f)
                self.excel_file_path = settings.get("excel_file_path", "")
                if self.prompt_input:
                    self.prompt_input.setText(self.excel_file_path)
                if self.gemini_input:
                    self.gemini_input.setText(settings.get("gemini_api_key", ""))
                if self.cloudinary_input:
                    self.cloudinary_input.setText(settings.get("cloudinary_config", ""))
            
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể load dữ liệu từ file JSON: {e}")
        # else:
        #     QMessageBox.information(self, "Thông báo", "Không tìm thấy file settings.json") # Xóa dòng này