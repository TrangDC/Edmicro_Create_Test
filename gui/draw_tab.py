from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout,
                             QListWidget, QTextEdit, QPushButton, QScrollArea,
                             QSizePolicy, QDialog, QLineEdit, QFormLayout, QFileDialog, QMessageBox)
from logic import compile_latex_to_pdf, pdf_to_png, create_latex_code_for_function,create_latex_code_for_table,rename_latex_vertices
from create_test import create_docx_files_with_pandoc
from find_questions_with_image import update_questions_with_images
import json
from tkinter import ttk, messagebox
from fractions import Fraction
from pdf2image import convert_from_path
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
import re
import os
import cloudinary
import logging
import requests

# Configuration
cloudinary.config(
    cloud_name="dgbjb4emp",
    api_key="995523778761239",
    api_secret="kO8fKCyTkgKXvkcBZMcqvrncuTk",
    secure=True
)

def upload_image_to_cloudinary(image_bytes):
        try:
            response = cloudinary.uploader.upload(
                image_bytes,
            )
            if 'secure_url' in response:
                return response['secure_url']
            else:
                return None
        except Exception as e:
            logging.error(f"Error uploading to Cloudinary: {str(e)}", exc_info=True)
            return None

def create_imgur_url(image_path):
        try:
            with open(image_path, "rb") as image_file:
                image_bytes = image_file.read()
            cloudinary_url = upload_image_to_cloudinary(image_bytes)
            return cloudinary_url
        except Exception as e:
            logging.error(f"Error creating Cloudinary URL {str(e)}", exc_info=True)
            return None

class DrawParamsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nhập tham số vẽ hình")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Nhập tham số cho đồ thị
        self.param_label = QLabel("Nhập tham số (cách nhau bằng dấu phẩy):")
        self.param_input = QLineEdit()

        # Nút xác nhận
        self.draw_button = QPushButton("Vẽ")
        self.draw_button.clicked.connect(self.accept)

        # Thêm các widget vào layout
        layout.addWidget(self.param_label)
        layout.addWidget(self.param_input)
        layout.addWidget(self.draw_button)

        self.setLayout(layout)

    def get_input_data(self):
        # Lấy dữ liệu từ trường nhập
        return self.param_input.text()

class DrawTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.questions = {}
        self.selected_question_index = None
        self.current_json_file = None
        self.all_tests_json_file = None
        self.image_cache = {} # Thêm dòng này

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Các widget hiện tại trong GUI vẫn giữ nguyên
        # Chọn loại hình
        type_layout = QHBoxLayout()
        type_label = QLabel("Chọn loại hình:")
        type_label.setFont(QFont("Arial",12)) # Tăng cỡ chữ
        self.type_combo = QComboBox()
        self.type_combo.setFont(QFont("Arial",12))# Tăng cỡ chữ
        self.type_combo.addItems(["Đồ thị", "Bảng biến thiên", "Hình học"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        main_layout.addLayout(type_layout)

        # Chọn loại chi tiết (thay đổi tùy theo loại hình)
        detail_layout = QHBoxLayout()
        self.detail_label = QLabel("Chọn chi tiết:")
        self.detail_label.setFont(QFont("Arial",12)) # Tăng cỡ chữ
        self.detail_combo = QComboBox()
        self.detail_combo.setFont(QFont("Arial",12)) # Tăng cỡ chữ
        detail_layout.addWidget(self.detail_label)
        detail_layout.addWidget(self.detail_combo)
        main_layout.addLayout(detail_layout)

        # Layout cho danh sách câu hỏi, mô tả ảnh, mã LaTeX và ảnh
        content_layout = QHBoxLayout()

        # Danh sách câu hỏi
        question_layout = QVBoxLayout()
        question_label = QLabel("Danh sách câu hỏi:")
        question_label.setFont(QFont("Arial",14))  # Tăng cỡ chữ
        question_layout.addWidget(question_label)
        self.question_list = QListWidget()
        self.question_list.setFont(QFont("Arial",12))  # Tăng cỡ chữ
        self.question_list.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.question_list.setMinimumWidth(450) # Tăng chiều rộng
        self.question_list.itemClicked.connect(self.show_selected_description)
        question_layout.addWidget(self.question_list)
        content_layout.addLayout(question_layout)

        # Mô tả ảnh
        description_layout = QVBoxLayout()
        description_label = QLabel("Mô tả ảnh:")
        description_label.setFont(QFont("Arial",14))  # Tăng cỡ chữ
        description_layout.addWidget(description_label)
        self.description_text = QTextEdit()
        self.description_text.setFont(QFont("Arial",12)) # Tăng cỡ chữ
        self.description_text.setReadOnly(True)
        self.description_text.setLineWrapMode(QTextEdit.WidgetWidth)
        description_layout.addWidget(self.description_text)
        content_layout.addLayout(description_layout)

        # Layout cho mã LaTeX và ảnh (đổi vị trí)
        image_latex_layout = QVBoxLayout()
        
        # Ảnh
        image_label = QLabel("Ảnh:")
        image_label.setFont(QFont("Arial",12))
        image_latex_layout.addWidget(image_label)
        self.image_scroll_area = QScrollArea()
        self.image_scroll_area.setWidgetResizable(True)
        self.image_scroll_area.setAlignment(Qt.AlignCenter)
        self.image_label = QLabel()
        self.image_scroll_area.setWidget(self.image_label)
        image_latex_layout.addWidget(self.image_scroll_area)

        # Mã LaTeX
        latex_label = QLabel("Mã LaTeX:")
        latex_label.setFont(QFont("Arial",12))
        image_latex_layout.addWidget(latex_label)
        self.latex_text = QTextEdit()
        self.latex_text.setFont(QFont("Arial",10)) # Giảm cỡ chữ
        image_latex_layout.addWidget(self.latex_text)

        content_layout.addLayout(image_latex_layout)
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

        # Nút vẽ sẽ mở cửa sổ nhập tham số
        self.draw_button.clicked.connect(self.open_draw_params_dialog)

        # Kết nối nút compile với hàm xuất docx
        self.compile_button.clicked.connect(self.compile_to_docx)

    def load_image(self, image_url):
        """Load image from URL or file, using cache."""
        if image_url in self.image_cache:
            return self.image_cache[image_url]
        try:
            if image_url.startswith("http"):
                response = requests.get(image_url, stream=True, timeout=5)
                response.raise_for_status()
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
            else:
                pixmap = QPixmap(image_url)
            if not pixmap.isNull():
                self.image_cache[image_url] = pixmap
                return pixmap
            else:
                QMessageBox.warning(self, "Error", f"Could not load image at: {image_url}")
                return None
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading image {image_url}: {str(e)}")
            return None

    def open_draw_params_dialog(self):
    # Lấy loại chi tiết từ detail_combo
      selected_type = self.detail_combo.currentText()
      dialog = DrawParamsDialog(self)  # Tạo hộp thoại nhập tham số

      if dialog.exec_() == QDialog.Accepted:  # Kiểm tra nếu nhấn 'Vẽ'
          params = dialog.get_input_data()
          self.process_draw_params(params, selected_type)

    def process_draw_params(self, params, selected_type):
        try:
            # Kiểm tra loại chính (Đồ thị, Bảng biến thiên, Hình học)
            parent_type = self.type_combo.currentText()

            # Xử lý tham số dựa trên loại
            if parent_type == "Hình học":
                # Nếu là Hình học, cho phép nhập các ký tự như "a", "b", "c", "d"
                parameters = [param.strip() for param in params.split(",")]
                # Chuyển danh sách thành chuỗi để phù hợp với hàm rename_latex_vertices
                parameters_str = ", ".join(parameters)
            else:
                # Nếu là Đồ thị hoặc Bảng biến thiên, chuyển đổi tham số thành số (float hoặc Fraction)
                parameters = tuple(
                    float(Fraction(param.strip())) if '/' in param else float(param.strip())
                    for param in params.split(",")
                )
                parameters_str = None  # Không dùng trong trường hợp Đồ thị hoặc Bảng biến thiên

            latex_code = ""

            # Tạo mã LaTeX dựa trên loại chính
            if parent_type == "Đồ thị":
                latex_code = create_latex_code_for_function(selected_type, parameters)
                file_prefix = f"graph_{selected_type.replace(' ', '_')}"
            elif parent_type == "Bảng biến thiên":
                latex_code = create_latex_code_for_table(selected_type, parameters)
                file_prefix = f"table_{selected_type.replace(' ', '_')}"
            elif parent_type == "Hình học":
                # Gọi rename_latex_vertices với chuỗi thay vì danh sách
                latex_code = rename_latex_vertices(selected_type, parameters_str)
                file_prefix = f"geometry_{selected_type.replace(' ', '_')}"
            else:
                messagebox.showerror("Lỗi", "Loại hình không được hỗ trợ.")
                return

            # Tạo tên file PDF và PNG động
            output_pdf = f"{file_prefix}_output.pdf"
            output_image = f"{file_prefix}_output.png"

            json_dir = os.path.dirname(self.current_json_file)
            full_output_pdf = os.path.join(json_dir, output_pdf)
            full_output_image = os.path.join(json_dir, output_image)

            # Đảm bảo thư mục đích tồn tại
            output_dir = os.path.dirname(full_output_pdf)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Xuất file PDF và PNG từ mã LaTeX
            if compile_latex_to_pdf(latex_code, full_output_pdf):
                pdf_to_png(full_output_pdf, full_output_image)
                messagebox.showinfo("Thành công", f"File PNG đã được tạo thành công: {full_output_image}!")

                # Get the directory of the JSON file
                if self.selected_question_index is not None and self.current_json_file:
                    image_url = create_imgur_url(full_output_image)
                    # Update the JSON with the image path
                    self.update_json_image_path(image_url, self.selected_question_index)
                    self.display_image(full_output_image)
            else:
                messagebox.showerror("Lỗi", "Không thể tạo đồ thị hoặc bảng. Kiểm tra lại LaTeX.")
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập tham số đúng định dạng.")



    def display_image(self, image_path):
        """Display an image in the image label."""
        pixmap = self.load_image(image_path)
        if pixmap:
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.clear()

    def update_json_image_path(self, image_path, index):
        """Updates the image path in the loaded JSON data."""
        if self.current_json_file and index is not None:
             with open(self.current_json_file, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)

             # Find the question's category (shortQuestions etc).
             for question_type, groups in questions_data.items():
                for group in groups:
                    if index < len(group["list"]):
                        group["list"][index]["image"] = image_path
                        break

             #Write back to the json file:
             with open(self.current_json_file, 'w', encoding='utf-8') as f:
                  json.dump(questions_data, f, indent=2, ensure_ascii=False)
             #Refresh the Question List
             with open(self.current_json_file, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
             self.update_questions(questions_data, self.current_json_file, self.all_tests_json_file)

    def update_questions(self, questions_data, extracted_questions_file, json_file_path):
        self.question_list.clear()
        self.questions = {}
        self.current_json_file = extracted_questions_file
        self.all_tests_json_file = json_file_path

        for question_type, groups in questions_data.items():
            for group in groups:
                for i, question in enumerate(group["list"]):
                    question_content = question["content"]
                    image_description = re.search(r'\[Mô tả ảnh:(.*?)\]', question_content)
                    if image_description:
                        description = image_description.group(1).strip()
                        self.questions[question_content] = description
                    else:
                        self.questions[question_content] = ""
                    # Load ảnh ngay khi load câu hỏi
                    if question.get("image"):
                            self.load_image(question["image"])
                # Chỉ hiển thị ảnh nếu index của câu hỏi trùng với self.selected_question_index
                    if i == self.selected_question_index and question.get("image"):
                        self.display_image(question["image"])
                    elif i == self.selected_question_index and not question.get("image"):
                        self.image_label.clear()
        self.question_list.clear()
        self.questions = {}
        for question_type, groups in questions_data.items():
            for group in groups:
                for i, question in enumerate(group["list"]):
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
        self.selected_question_index = self.question_list.row(self.question_list.currentItem())
        self.description_text.setText(self.questions.get(selected_question, ""))

        # Gọi lại update_questions để tải và hiển thị ảnh
        if self.current_json_file and self.all_tests_json_file:
            with open(self.current_json_file, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
            self.update_questions(questions_data, self.current_json_file, self.all_tests_json_file)
            
    def update_detail_options(self):
        selected_type = self.type_combo.currentText()
        if selected_type == "Đồ thị":
            self.detail_label.setText("Chọn loại đồ thị:")
            self.detail_combo.clear()
            self.detail_combo.addItems(["Bậc nhất", "Bậc hai", "Bậc ba", "Bậc bốn trùng phương", "Phân thức bậc nhất/bậc nhất", "Phân thức bậc hai/bậc nhất"])
        elif selected_type == "Bảng biến thiên":
            self.detail_label.setText("Chọn loại hàm số:")
            self.detail_combo.clear()
            self.detail_combo.addItems(["Bậc hai", "Bậc ba", "Bậc bốn trùng phương",
                                "Phân thức bậc nhất/bậc nhất", "Phân thức bậc hai/bậc nhất"])
        elif selected_type == "Hình học":
            self.detail_label.setText("Chọn hình học:")
            self.detail_combo.clear()
            self.detail_combo.addItems(["Hình chóp tam giác cạnh vuông góc", "Hình chóp tam giác mặt vuông góc", "Hình chóp tam giác đều", "Hình tứ diện", "Hình chóp tứ giác", "Hình chóp đáy h.b.h cạnh vuông góc", "Hình chóp đáy h.b.h mặt vuông góc", "Hình chóp tứ giác đều", "Hình lăng trụ xiên tam giác", "Hình lăng trụ đứng tam giác", "Hình hộp", "Hình lập phương"])

    def compile_to_docx(self):
        """Compiles the current set of questions to a .docx file."""
        if self.current_json_file and self.all_tests_json_file:
            # Get the directory of the JSON file
            json_dir = os.path.dirname(self.current_json_file)
            docx_output_dir = os.path.join(json_dir, "output_docx")

            # Use the logic from the original code to create docx files
            self.update_questions_with_images()
            self.create_docx_files_with_pandoc(docx_output_dir)
            messagebox.showinfo("Thành công", f"Đã xuất file docx thành công tại thư mục {docx_output_dir}")
        else:
            messagebox.showerror("Lỗi", "Không có file JSON nào được chọn.")
    def update_questions_with_images(self):
      if self.current_json_file and self.all_tests_json_file:
          update_questions_with_images(self.all_tests_json_file,self.current_json_file)
    def create_docx_files_with_pandoc(self, output_dir):
        """Tạo các file .docx sử dụng Pandoc, mỗi file một bộ câu hỏi riêng."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if self.all_tests_json_file:
              with open(self.all_tests_json_file, 'r', encoding='utf-8') as f:
                  data = json.load(f)
              create_docx_files_with_pandoc(data, output_dir)