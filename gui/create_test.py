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
    if text is None:
        return ""
 
    def replace(match):
        escaped_backslash = match.group(0)
        latex_command = match.group(1)
       
        if re.match(r"^(left|right|begin|end|{|}|\\)+", latex_command):
            return "\\" + latex_command
       
        return escaped_backslash
 
    pattern = r"\\\\([a-zA-Z\{\}\\\\]+)"
    text = re.sub(pattern, replace, text)
   
    text = text.replace("\n", "\n\n")
 
    return text
 
 
def json_to_markdown(data, output_file, file_index):
    """Chuyển đổi dữ liệu JSON thành file Markdown, mỗi file ứng với một câu hỏi từ list."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f'# Đề kiểm tra số {file_index + 1}\n\n')
 
        # Choice Questions
        f.write('**PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.** Thí sinh trả lời từ câu 1 đến câu 12. Mỗi câu hỏi thí sinh chỉ chọn một phương án.\n\n')
        for question_set in data.get("choiceQuestions", []):
            if len(question_set.get("list", [])) > file_index:
                question = question_set["list"][file_index]
                f.write(f'**Câu {question_set["questionNumber"]}:** {escape_xml_chars(unescape_latex_chars(question["content"]))}\n\n')
                for option in question["options"]:
                    f.write(f'{escape_xml_chars(unescape_latex_chars(option))}\n\n')
                f.write('\n')
 
        # True/False Questions
        f.write('**PHẦN II. Câu trắc nghiệm đúng sai.** Thí sinh trả lời từ câu 1 đến câu 4. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai\n\n')
        for question_set in data.get("trueFalseQuestions", []):
            if len(question_set.get("list", [])) > file_index:
                question = question_set["list"][file_index]
                f.write(f'**Câu {question_set["questionNumber"]}:** {escape_xml_chars(unescape_latex_chars(question["content"]))}\n\n')
                for option in question["options"]:
                    f.write(f'{escape_xml_chars(unescape_latex_chars(option))}\n\n')
                f.write('\n')
 
        # Short Questions
        f.write('**PHẦN III. Câu trắc nghiệm trả lời ngắn.** Thí sinh trả lời từ câu 1 đến câu 6.\n\n')
        for question_set in data.get("shortQuestions", []):
            if len(question_set.get("list", [])) > file_index:
                question = question_set["list"][file_index]
                f.write(f'**Câu {question_set["questionNumber"]}:** {escape_xml_chars(unescape_latex_chars(question["content"]))}\n\n')
                f.write('\n')
 
        f.write(f'**Hướng dẫn giải đề {file_index + 1}**\n\n')
 
        # Choice Guide
        f.write('**PHẦN I**\n\n')
        for guide_set in data.get("choiceQuestions", []):
            if len(guide_set.get("list", [])) > file_index:
                guide = guide_set["list"][file_index]
                f.write(f'**Câu {guide_set["questionNumber"]}:** {escape_xml_chars(unescape_latex_chars(guide["guide"]))}\n\n')
                f.write('\n')
 
        # True/False Guide
        f.write('**PHẦN II**\n\n')
        for guide_set in data.get("trueFalseQuestions", []):
            if len(guide_set.get("list", [])) > file_index:
                guide = guide_set["list"][file_index]
                f.write(f'**Câu {guide_set["questionNumber"]}:** {escape_xml_chars(unescape_latex_chars(guide["guide"]))}\n\n')
                f.write('\n')
 
        # Short Guide
        f.write('**PHẦN III**\n\n')
        for guide_set in data.get("shortQuestions", []):
            if len(guide_set.get("list", [])) > file_index:
                guide = guide_set["list"][file_index]
                f.write(f'**Câu {guide_set["questionNumber"]}:** {escape_xml_chars(unescape_latex_chars(guide["guide"]))}\n\n')
                f.write('\n')
 
def markdown_to_docx(markdown_file, docx_file):
    """Chuyển đổi file Markdown thành file .docx bằng Pandoc."""
    try:
        subprocess.run(['pandoc', markdown_file, '-o', docx_file], check=True)
        return True
    except subprocess.CalledProcessError as err:
        print(f"Lỗi khi chạy Pandoc: {err}")
        return False

def create_docx_files_with_pandoc(data, output_dir, markdown_dir = None):
    """Tạo các file .docx sử dụng Pandoc, mỗi file một bộ câu hỏi riêng."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if markdown_dir is None:
       markdown_dir = output_dir

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
 
 
# if __name__ == "__main__":
#     with open(r'E:\Edmicro\Tool_tao_de\controller\2_call_gemini\output.json', 'r', encoding='utf-8') as f:
#         data = json.load(f)
#     create_docx_files_with_pandoc(data)
#     print("Hoàn thành việc tạo các file .docx bằng Pandoc!")