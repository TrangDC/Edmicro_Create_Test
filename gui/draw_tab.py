from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout,
                             QListWidget, QTextEdit, QPushButton, QScrollArea,
                             QSizePolicy)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import re

class DrawTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.questions = {}
        # self.update_question_list() # Không cần gọi ở đây nữa
    def init_ui(self):
        main_layout = QVBoxLayout()

        # Chọn loại hình
        type_layout = QHBoxLayout()
        type_label = QLabel("Chọn loại hình:")
        type_label.setFont(QFont("Arial",10))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Đồ thị", "Bảng biến thiên", "Hình học"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        main_layout.addLayout(type_layout)

        # Chọn loại chi tiết (thay đổi tùy theo loại hình)
        detail_layout = QHBoxLayout()
        self.detail_label = QLabel("Chọn chi tiết:")
        self.detail_label.setFont(QFont("Arial",10))
        self.detail_combo = QComboBox()
        detail_layout.addWidget(self.detail_label)
        detail_layout.addWidget(self.detail_combo)
        main_layout.addLayout(detail_layout)
        
        # Layout cho danh sách câu hỏi, mô tả ảnh, mã LaTeX và ảnh
        content_layout = QHBoxLayout()
        
        # Danh sách câu hỏi (thêm label)
        question_layout = QVBoxLayout()
        question_label = QLabel("Danh sách câu hỏi:")
        question_label.setFont(QFont("Arial",12))
        question_layout.addWidget(question_label)
        self.question_list = QListWidget()
        self.question_list.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding) # Không mở rộng theo chiều ngang, mở rộng theo chiều dọc
        self.question_list.setMinimumWidth(200) # Set minimum width of the question list
        self.question_list.itemClicked.connect(self.show_selected_description)
        question_layout.addWidget(self.question_list)
        content_layout.addLayout(question_layout)
        
        # Mô tả ảnh
        description_layout = QVBoxLayout()
        description_label = QLabel("Mô tả ảnh:")
        description_label.setFont(QFont("Arial",12))
        description_layout.addWidget(description_label)
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        description_layout.addWidget(self.description_text)
        content_layout.addLayout(description_layout)


        # Layout cho mã Latex và ảnh
        image_layout = QVBoxLayout()

        # Mã LaTeX
        latex_label = QLabel("Mã LaTeX:")
        latex_label.setFont(QFont("Arial",12))
        image_layout.addWidget(latex_label)
        self.latex_text = QTextEdit()
        image_layout.addWidget(self.latex_text)

        # Ảnh
        image_label = QLabel("Ảnh:")
        image_label.setFont(QFont("Arial",12))
        image_layout.addWidget(image_label)
        self.image_scroll_area = QScrollArea()
        self.image_scroll_area.setWidgetResizable(True)
        self.image_scroll_area.setAlignment(Qt.AlignCenter)
        self.image_label = QLabel()
        self.image_scroll_area.setWidget(self.image_label)
        image_layout.addWidget(self.image_scroll_area)

        content_layout.addLayout(image_layout)
        main_layout.addLayout(content_layout)
        # Nút vẽ
        button_layout = QHBoxLayout()
        self.draw_button = QPushButton("Vẽ ảnh")
        self.redraw_button = QPushButton("Vẽ lại")
        self.compile_button = QPushButton("Xuất file docx")
        button_layout.addWidget(self.draw_button)
        button_layout.addWidget(self.redraw_button)
        button_layout.addWidget(self.compile_button)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        self.type_combo.currentIndexChanged.connect(self.update_detail_options)
        self.update_detail_options()
        
    def update_questions(self, questions_data):
        """Updates the question list with data from the JSON file."""
        self.question_list.clear()
        self.questions = {}
        
        for question_type, groups in questions_data.items():
            for group in groups:
                for question in group["list"]:
                    question_content = question["content"]
                    image_description = re.search(r'\[Mô tả ảnh:(.*?)\]', question_content)
                    if image_description:
                      description = image_description.group(1).strip()
                      self.questions[question_content] = description
                    else:
                      self.questions[question_content] = ""
        self.question_list.addItems(self.questions.keys())

    def show_selected_description(self, item):
      selected_question = item.text()
      self.description_text.setText(self.questions.get(selected_question, ""))
    
    def update_detail_options(self):
       selected_type = self.type_combo.currentText()
       if selected_type == "Đồ thị":
         self.detail_label.setText("Chọn loại đồ thị:")
         self.detail_combo.clear()
         self.detail_combo.addItems(["Bậc nhất", "Bậc hai", "Bậc ba", "Bậc bốn trùng phương", "Phân thức bậc nhất/bậc nhất", "Phân thức bậc hai/bậc nhất"])
       elif selected_type == "Bảng biến thiên":
         self.detail_label.setText("Chọn loại hàm số:")
         self.detail_combo.clear()
         self.detail_combo.addItems(["Bậc hai", "Bậc ba", "Bậc bốn trùng phương", "Phân thức bậc nhất/bậc nhất", "Phân thức bậc hai/bậc nhất"])
       elif selected_type == "Hình học":
         self.detail_label.setText("Chọn hình học:")
         self.detail_combo.clear()
         self.detail_combo.addItems(["Tam giác", "Hình vuông","Hình của Đông", "Hình của Trung"])