import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QHBoxLayout, QFileDialog,
                             QComboBox, QTextEdit, QProgressBar, QMessageBox,
                             QSizePolicy, QCompleter)
from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, pyqtSignal, QThread
import os
from openpyxl import load_workbook
import json
import google.generativeai as genai
import logging

# Đảm bảo các đường dẫn này đúng với vị trí thực tế của các file
sys.path.append(r'E:\Edmicro\Tool_tao_de\controller')
try:
    from split_question_to_excel import extract_content
    from call_gemini import get_prompt_templates_excel, process_sheet, SheetType, call_gemini_process
    from find_questions_with_image import extract_questions_with_images
    from create_test import create_docx_files_with_pandoc
except ImportError as e:
    print(f"Lỗi import module: {e}")
    sys.exit()

generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}

model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp",
                            generation_config=generation_config,
                            )

class CompleterComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().installEventFilter(self)  # Install event filter
        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self.completer)
    
    def eventFilter(self, obj, event):
        if obj == self.lineEdit() and event.type() == event.KeyPress:
            text = self.lineEdit().text()
            if event.key() == Qt.Key_Backspace and not text:
                self.setCurrentIndex(-1)
                return True
            
        return super().eventFilter(obj, event)


    def setModel(self, model):
        super().setModel(model)
        self.completer.setModel(model)

    def setModelColumn(self, column):
      self.completer.setCompletionColumn(column)
      super().setModelColumn(column)

class DocumentGenerator(QThread):
    finished_signal = pyqtSignal(str, str)  # Signal khi thread hoàn thành
    log_signal = pyqtSignal(str)  # Signal để gửi log message
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(str)
    image_questions_signal = pyqtSignal(tuple) # Thay vì dict, sử dụng tuple

    def __init__(self, file_path, num_copies, parent):
        super().__init__()
        self.file_path = file_path
        self.num_copies = num_copies
        self.is_running = True
        self.parent_widget = parent

    def run(self):
        try:
            if not self.is_running:
                self.finished_signal.emit("Đã hủy quá trình.", "")
                return
            self.log_signal.emit("Bắt đầu xử lý...")

            # Gọi hàm split_question_to_excel
            excel_file_path = self.parent_widget.run_split_excel()
            if not excel_file_path:
                self.finished_signal.emit("Lỗi: Không tạo được file Excel", "")
                return
            self.log_signal.emit(f"Đã tạo file excel tại {excel_file_path}")

            # Gọi hàm call_gemini
            self.log_signal.emit("Bắt đầu tạo câu tương tự...")
            json_result = self.parent_widget.run_call_gemini(excel_file_path, self.num_copies)
            if not json_result:
                self.finished_signal.emit("Lỗi: Không có kết quả json", "")
                return
            self.log_signal.emit("Hoàn thành tạo dữ liệu câu.")
            
            json_file_path = self.parent_widget.save_json_to_file(self.file_path, json_result)
            if json_file_path:
                try:
                    extracted_questions_file = extract_questions_with_images(json_file_path)
                    with open(extracted_questions_file, 'r', encoding='utf-8') as f:
                        extracted_data = json.load(f)
                    if extracted_data:
                        # Logic if questions with images are found
                        self.log_signal.emit(f"Đã tìm thấy câu hỏi có ảnh trong file {extracted_questions_file}")
                        # TODO: Thêm logic xử lý mới ở đây (ví dụ: hiển thị danh sách câu hỏi, chỉnh sửa, v.v.)
                        self.image_questions_signal.emit((extracted_data, extracted_questions_file, json_file_path)) # emit tuple
                    else:
                        # Logic if no questions with images are found
                        self.log_signal.emit(f"Không tìm thấy câu hỏi nào có ảnh trong file {json_file_path}")
                        create_docx_files_with_pandoc(json.loads(json_result), self.parent_widget.output_dir) # logic cũ
                        self.finished_signal.emit("Hoàn thành tạo file docx", self.parent_widget.output_dir)
                        self.result_signal.emit(json_result)
                except Exception as e:
                    self.log_signal.emit(f"Lỗi khi xử lý file json: {e}")    
        except Exception as e:
            self.log_signal.emit(f"Lỗi: {e}")
            self.finished_signal.emit(f"Lỗi: {e}","")
        finally:
            self.finished_signal.emit("Done.", "")
                

    def stop(self):
        self.is_running = False

class CreateTab(QWidget):
    result_signal = pyqtSignal(str)
    log_text_signal = pyqtSignal(str)
    def __init__(self, settings_tab, draw_tab, main_window):
        super().__init__()
        self.docx_file_path = ""
        self.num_copies = 0
        self.worker_thread = None
        self.settings_tab = settings_tab
        self.load_settings() # Gọi load_settings ngay sau khi gán settings_tab
        self.init_ui()
        # self.settings_tab.settings_changed.connect(self.load_settings)
        self.result_signal.connect(self.display_json_result)
        self.log_text_signal.connect(self.update_text_log)
        self.json_file_path = ""
        self.output_dir = ""
        self.draw_tab = draw_tab
        self.main_window = main_window
        # self.prompt_input = settings_tab.prompt_input.text()
        # self.gemini_input = settings_tab.gemini_input.text()
        # self.cloudinary_input = settings_tab.cloudinary_input.text()

    def load_settings(self, settings=None):
        if settings is None:
            try:
                with open("settings.json", 'r') as f:
                    settings = json.load(f)
            except:
                settings = {}
            self.prompt_input = settings.get("excel_file_path", "")
            self.gemini_input = settings.get("gemini_api_key", "")
            self.cloudinary_input = settings.get("cloudinary_config", "")

    def run_split_excel(self):
        docx_file_path = self.docx_input.text()
        subject_var = self.subject_combo.currentText()
        grade_var = None # có thể set giá trị mặc định hoặc lấy từ input

        # prompt_input = self.prompt_input
        # gemini_input = self.gemini_input
        # cloudinary_input = self.cloudinary_input

        try:
            excel_file_path = extract_content(self.prompt_input, self.gemini_input, self.cloudinary_input, docx_file_path, subject_var, grade_var)
            return excel_file_path
        except Exception as e:
            self.update_log(f"Lỗi khi chạy split excel: {e}")
            return None

    def run_call_gemini(self, excel_file_path, copy_number):
       try:
            json_result = call_gemini_process(self.gemini_input, excel_file_path, copy_number)
            return json_result
       except Exception as e:
         self.update_log(f"Lỗi khi gọi call gemini: {e}")
         return None
    
    def display_json_result(self, json_result):
        #  self.log_text.append(f"Kết quả JSON:\n{json_result}")
        pass

    def save_json_to_file(self, docx_file, json_data):
        """Saves JSON data to a file in the same directory as the docx file."""
        try:
            docx_dir = os.path.dirname(docx_file)
            docx_filename = os.path.splitext(os.path.basename(docx_file))[0]
            json_filename = f"{docx_filename}_gemini_output.json"
            json_file_path = os.path.join(docx_dir, json_filename)
            self.output_dir = os.path.join(docx_dir, f"{docx_filename}_gemini_output_docs")
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json.loads(json_data), f, ensure_ascii=False, indent=4)
            self.update_log(f"Đã lưu json file tại: {json_file_path}")
            return json_file_path
        except json.JSONDecodeError as e:
            self.update_log(f"Lỗi khi decode json: {e}")
            return None
        except Exception as e:
             self.update_log(f"Lỗi khi lưu file json: {e}")
             return None
            
    def process_finished(self, result_message, output_dir):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if "Hoàn thành" in result_message:  # Chỉ hiển thị thông báo nếu result_message chứa "Hoàn thành"
            QMessageBox.information(self, "Kết quả", result_message + f"\nFile docx được lưu ở: {output_dir}" )
    
    def update_text_log(self, log_message):
         self.log_text.append(log_message)

    def init_ui(self):
         # Font chữ lớn hơn
        font = QFont("Arial", 12) # font chữ Arial, kích thước 12

        # Layout chính
        main_layout = QVBoxLayout()
        
         # Chọn file docx
        docx_layout = QHBoxLayout()
        docx_label = QLabel("Chọn file docx:")
        docx_label.setFont(font)
        self.docx_input = QLineEdit()
        self.docx_input.setFont(font)
        docx_button = QPushButton("Chọn file")
        docx_button.setFont(font)
        docx_button.clicked.connect(self.open_file_dialog)

        # Set size policy cho QLineEdit và QPushButton để chúng mở rộng theo layout
        self.docx_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        docx_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        docx_layout.addWidget(docx_label)
        docx_layout.addWidget(self.docx_input)
        docx_layout.addWidget(docx_button)
        main_layout.addLayout(docx_layout)
        
         # Chọn môn thi
        subject_layout = QHBoxLayout()
        subject_label = QLabel("Chọn môn thi:")
        subject_label.setFont(font)
        # Thay QComboBox bằng CompleterComboBox
        self.subject_combo = CompleterComboBox() 
        self.subject_combo.setFont(font)
        # Set size policy cho QComboBox
        self.subject_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.subject_combo.setMinimumWidth(100)
        subject_layout.addWidget(subject_label)
        subject_layout.addWidget(self.subject_combo)
        main_layout.addLayout(subject_layout)
       
        # Chọn số lượng bản sao
        num_layout = QHBoxLayout()
        num_label = QLabel("Số lượng bản sao:")
        num_label.setFont(font)
        self.num_combo = CompleterComboBox()
        self.num_combo.setFont(font)
        # Set size policy cho QComboBox
        self.num_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.num_combo.setMinimumWidth(100)
        num_layout.addWidget(num_label)
        num_layout.addWidget(self.num_combo)
        main_layout.addLayout(num_layout)
        
        # Loading Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(font)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Log
        log_label = QLabel("Log:")
        log_label.setFont(font)
        self.log_text = QTextEdit()
        self.log_text.setFont(font)
        self.log_text.setReadOnly(True)
        # set size policy cho log text để nó mở rộng khi resize cửa sổ
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(log_label)
        main_layout.addWidget(self.log_text)

        # Button start/stop
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Bắt đầu")
        self.start_button.setFont(font)
        self.start_button.clicked.connect(self.start_process)
        self.stop_button = QPushButton("Hủy")
        self.stop_button.setFont(font)
        self.stop_button.clicked.connect(self.stop_process)
        self.stop_button.setEnabled(False)

        # Set size policy cho các nút start/stop
        self.start_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.stop_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        main_layout.addLayout(button_layout)
        
        self.docx_input.setMinimumHeight(30) # đặt chiều cao tối thiểu cho input là 30
        self.num_combo.setMinimumHeight(30) # đặt chiều cao tối thiểu cho input là 30
        self.subject_combo.setMinimumHeight(30) # đặt chiều cao tối thiểu cho input là 30
        self.log_text.setMinimumHeight(100) # đặt chiều cao tối thiểu cho log là 100
        self.progress_bar.setMinimumHeight(20) # đặt chiều cao tối thiểu cho progress bar là 20
        
        self.setLayout(main_layout)
         # Gọi hàm update_subject_list ngay sau khi tạo giao diện
        self.update_subject_list()
        self.update_num_list()

    def open_file_dialog(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Chọn file docx", "", "Word Documents (*.docx)")
        if file_path:
            self.docx_input.setText(file_path)
            self.docx_file_path = file_path
             # Cập nhật môn học
            self.update_subject_list()
        
    def update_subject_list(self):
        subjects = ["", "Toán", "Vật lý", "Hóa học", "Sinh học", "Ngữ văn", "Lịch sử", "Địa lý"]
        model = self.subject_combo.model()
        if model is None:
            model =  QStandardItemModel(self)
            self.subject_combo.setModel(model)
        
        model.clear()
        for item in subjects:
          qItem = QStandardItem(item)
          model.appendRow(qItem)
       
        self.subject_combo.setModelColumn(0)
        self.subject_combo.setCurrentIndex(0)

    def update_num_list(self):
        num_list = [""] + list(str(i) for i in range(1, 11)) # 1 -> 10
        model = self.num_combo.model()
        if model is None:
            model = QStandardItemModel(self)
            self.num_combo.setModel(model)

        model.clear()
        for item in num_list:
          qItem = QStandardItem(item)
          model.appendRow(qItem)

        self.num_combo.setModelColumn(0)
        self.num_combo.setCurrentIndex(0)

    def start_process(self):
        self.log_text.clear()
        num_text = self.num_combo.currentText()
        try:
           self.num_copies = int(num_text)
        except ValueError:
            QMessageBox.warning(self, "Lỗi", "Số lượng bản sao không hợp lệ")
            return
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)

        if not self.docx_file_path:
            QMessageBox.warning(self, "Lỗi", "Chưa chọn file docx!")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            return

        self.worker_thread = DocumentGenerator(self.docx_file_path, self.num_copies, self) # truyền thêm self vào đây
        self.worker_thread.finished_signal.connect(self.process_finished)
        self.worker_thread.log_signal.connect(self.update_log)
        self.worker_thread.progress_signal.connect(self.update_progress)
        self.worker_thread.result_signal.connect(self.display_json_result)
        self.worker_thread.image_questions_signal.connect(self.handle_image_questions)
        self.worker_thread.start()

    def handle_image_questions(self, image_questions_info):
        """
        Handles the image questions data and file path received from the worker thread.
        """
        questions_data, questions_file_path, json_file_path = image_questions_info
        self.draw_tab.update_questions(questions_data, questions_file_path, json_file_path)
        self.main_window.setCurrentWidget(self.draw_tab)
    def stop_process(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.log_text.append("Đang dừng...")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, log_message):
       self.log_text_signal.emit(log_message)