import json
import os
import subprocess
import xml.sax.saxutils
import re

def escape_xml_chars(text):
    if text is None:
        return ""
    return xml.sax.saxutils.escape(str(text))

def unescape_latex_chars(text):
    """Chuyển đổi các \\ trong LaTeX thành \, chỉ giữ lại 1 \ nếu nó đứng trước các lệnh LaTeX."""
    if text is None:
        return ""

    def replace(match):
        escaped_backslash = match.group(0)
        if escaped_backslash.startswith("\\\\"):
            latex_command = escaped_backslash[2:]
            if re.match(r"^(left|right|begin|end|{|}|\s|\\)+", latex_command):
                return "\\" + latex_command
            return escaped_backslash
        return escaped_backslash

    
    # Sử dụng regular expression để tìm các chuỗi \\ trước các lệnh LaTeX
    pattern = r"\\\\([a-zA-Z\{\}\\\\]+)"
    
    text = re.sub(pattern, replace, text)
    
    # Fix xử lý chuỗi Latex
    # text = text.replace("\\\\", "\\")

    # text = re.sub(r"(\S)\s+\$", r"\1$", text)
    
    return text


def json_to_markdown(data, output_file, file_index):
    """Chuyển đổi dữ liệu JSON thành file Markdown, mỗi file ứng với một câu hỏi từ list."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f'# Đề kiểm tra số {file_index + 1}\n\n')

        # Choice Questions
        f.write('## Dạng 1: Câu hỏi trắc nghiệm\n\n')
        for question_set in data.get("choiceQuestions", []):
            if len(question_set.get("list", [])) > file_index:
                question = question_set["list"][file_index]
                f.write(f'**Câu {question_set["questionNumber"]}:** {escape_xml_chars(unescape_latex_chars(question["content"]))}\n\n')
                for option in question["options"]:
                    f.write(f'- {escape_xml_chars(unescape_latex_chars(option))}\n')
                f.write('\n')

        # True/False Questions
        f.write('## Dạng 2: Câu hỏi đúng/sai\n\n')
        for question_set in data.get("trueFalseQuestions", []):
            if len(question_set.get("list", [])) > file_index:
                question = question_set["list"][file_index]
                f.write(f'**Câu {question_set["questionNumber"]}:** {escape_xml_chars(unescape_latex_chars(question["content"]))}\n\n')
                for option in question["options"]:
                    f.write(f'- {escape_xml_chars(unescape_latex_chars(option))}\n')
                f.write('\n')

        # Short Questions
        f.write('## Dạng 3: Câu hỏi trả lời ngắn\n\n')
        for question_set in data.get("shortQuestions", []):
            if len(question_set.get("list", [])) > file_index:
                question = question_set["list"][file_index]
                f.write(f'**Câu {question_set["questionNumber"]}:** {escape_xml_chars(unescape_latex_chars(question["content"]))}\n\n')
                f.write('\n')

def markdown_to_docx(markdown_file, docx_file):
    """Chuyển đổi file Markdown thành file .docx bằng Pandoc."""
    try:
        subprocess.run(['pandoc', markdown_file, '-o', docx_file], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi chạy Pandoc: {e}")
        return False

def create_docx_files_with_pandoc(data, output_dir="output_docx", markdown_dir="output_md"):
    """Tạo các file .docx sử dụng Pandoc, mỗi file một bộ câu hỏi riêng."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(markdown_dir):
        os.makedirs(markdown_dir)

    num_files = 0
    for key in ["choiceQuestions", "trueFalseQuestions", "shortQuestions"]:
        if key in data and isinstance(data[key], list):
            for question_set in data[key]:
                if "list" in question_set and isinstance(question_set["list"], list):
                   num_files = max(num_files,len(question_set["list"]))

    for file_index in range(num_files):
        markdown_file = os.path.join(markdown_dir, f'test_{file_index + 1}.md')
        docx_file = os.path.join(output_dir, f'test_{file_index + 1}.docx')

        json_to_markdown(data, markdown_file, file_index)
        if markdown_to_docx(markdown_file, docx_file):
            print(f"Đã tạo file .docx: {docx_file}")
        else:
            print(f"Không thể tạo file .docx: {docx_file}")


if __name__ == "__main__":
    with open(r'E:\Edmicro\Tool_tạo_đề\controller\2_call_gemini\output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    create_docx_files_with_pandoc(data)
    print("Hoàn thành việc tạo các file .docx bằng Pandoc!")