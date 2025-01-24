from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
                             QComboBox, QTextEdit, QProgressBar, QMessageBox,
                             QSizePolicy, QCompleter, QTabWidget, QFormLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from docx import Document
from PyQt5.QtWidgets import QComboBox, QLineEdit
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QColor
import json
import os
from draw_tab import DrawTab
from create_tab import CreateTab
from settings_tab import SettingsTab

class MainTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tool tạo đề")
        # Thay đổi kích thước ở đây
        self.setGeometry(100, 100, 1600, 900) # Tăng chiều rộng lên 800, chiều cao lên 600
        self.setMinimumSize(640, 480)

        # Tạo tab Cài đặt
        self.create_settings_tab()

        # Tạo tab Vẽ hình
        self.create_draw_tab()
        
        # Tạo tab Tạo đề
        self.create_create_tab()

         # Set style cho tab bar
        self.style_tab()

        # Kết nối tín hiệu currentChanged với hàm load_settings
        self.currentChanged.connect(self.on_tab_changed)
        
    def style_tab(self):
          self.setStyleSheet("""
            QTabBar::tab {
                background-color: lightgray;
                color: black;
                border: none;
                padding: 10px;
                width: 100%;
                font-size: 14px;
                font-weight: bold;
            }

            QTabBar::tab:selected {
                 background-color: blue;
                color: white;
            }
        """)
    
    def create_draw_tab(self):
        # Tạo tab Vẽ hình
        draw_tab = DrawTab()
        self.draw_tab = draw_tab # Khởi tạo DrawTab
        self.addTab(draw_tab, "Vẽ hình")
    
    def create_settings_tab(self):
        # Tạo tab Cài đặt
        settings_tab = SettingsTab()
        self.settings_tab = settings_tab
        self.addTab(settings_tab, "Cài đặt")

    def create_create_tab(self):
        # Tạo tab Tạo đề
        create_tab = CreateTab(self.settings_tab, self.draw_tab, self)
        self.create_tab = create_tab  # Khởi tạo CreateTab
        self.addTab(create_tab, "Tạo đề")

    def on_tab_changed(self, index):
        # Kiểm tra xem tab hiện tại có phải là CreateTab hay không
        if self.widget(index) == self.create_tab:
            self.create_tab.load_settings()