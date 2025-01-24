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
 
def process_content(content, image_url=None, question=None):
    # print(image_url)
    """
    Xử lý nội dung câu hỏi và thay thế mô tả ảnh bằng cú pháp Markdown cho ảnh.
 
    content: Chuỗi nội dung câu hỏi.
    image_url: Đường dẫn URL ảnh (nếu có) để thay thế vào trong nội dung.
    """
    # Thay thế [Mô tả ảnh: ...] bằng cú pháp Markdown cho ảnh
    def replace_image_description(match):
        if question and question.get('image'):
            return f"![Hình minh họa]({question['image']})"
        else:
            return ""  # Hoặc một giá trị mặc định khác nếu không có URL ảnh

    content = re.sub(r'\[Mô tả ảnh:([^\]]+)\]', replace_image_description, content)
    return content
 
def json_to_markdown_table(table_data):
    """
    Chuyển đổi dữ liệu JSON chứa bảng thành bảng dạng Markdown.
    """
    headers = table_data["header"]
    rows = table_data["rows"]
 
    # Tạo dòng tiêu đề
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join(["-" * len(header) for header in headers]) + " |"
 
    # Tạo các dòng dữ liệu
    data_rows = []
    for row in rows:
        # Đảm bảo mỗi dòng dữ liệu có đủ số cột bằng cách thêm ô trống nếu thiếu
        if len(row) < len(headers):
            row += [""] * (len(headers) - len(row))  # Thêm ô trống vào nếu thiếu
        elif len(row) > len(headers):
            row = row[:len(headers)]  # Cắt bớt cột nếu thừa
 
        # Chuyển dòng dữ liệu thành chuỗi Markdown
        data_rows.append("| " + " | ".join(map(str, row)) + " |")
 
    # Kết hợp thành bảng Markdown
    markdown_table = "\n".join([header_row, separator_row] + data_rows)
    return markdown_table
 
def json_to_markdown(data, output_file, file_index):
    """Chuyển đổi dữ liệu JSON thành file Markdown, mỗi file ứng với một câu hỏi từ list."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f'# Đề kiểm tra số {file_index + 1}\n\n')
 
        # Choice Questions
        f.write('**PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.** Thí sinh trả lời từ câu 1 đến câu 12. Mỗi câu hỏi thí sinh chỉ chọn một phương án.\n\n')
        for question_set in data.get("choiceQuestions", []):
            if len(question_set.get("list", [])) > file_index:
                question = question_set["list"][file_index]
 
                # Xử lý phần content và hình ảnh
                content = escape_xml_chars(unescape_latex_chars(question["content"]))
                content = process_content(content, question['image'], question)  # Thêm xử lý ảnh
                f.write(f'**Câu {question_set["questionNumber"]}:** {content}\n\n')
 
 
                # Xử lý các bảng
                if question["tables"] :
                    for table in question["tables"]:
                        if table["title"]:
                            f.write(f'{table["title"]}\n\n')
                        f.write(f'{json_to_markdown_table(table)}\n\n')
 
                # Xử lý các lựa chọn
                for option in question["options"]:
                    f.write(f'{escape_xml_chars(unescape_latex_chars(option))}\n\n')
                f.write('\n')
 
        # True/False Questions
        f.write('**PHẦN II. Câu trắc nghiệm đúng sai.** Thí sinh trả lời từ câu 1 đến câu 4. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai\n\n')
        for question_set in data.get("trueFalseQuestions", []):
            if len(question_set.get("list", [])) > file_index:
                question = question_set["list"][file_index]
 
                # Xử lý phần content và hình ảnh
                content = escape_xml_chars(unescape_latex_chars(question["content"]))
                content = process_content(content, question['image'], question)  # Thêm xử lý ảnh
                f.write(f'**Câu {question_set["questionNumber"]}:** {content}\n\n')
 
                # Xử lý các bảng
                if question["tables"] :
                    for table in question["tables"]:
                        if table["title"]:
                            f.write(f'{table["title"]}\n\n')
                        f.write(f'{json_to_markdown_table(table)}\n\n')
 
                # Xử lý các lựa chọn
                for option in question["options"]:
                    f.write(f'{escape_xml_chars(unescape_latex_chars(option))}\n\n')
                f.write('\n')
 
        # Short Questions
        f.write('**PHẦN III. Câu trắc nghiệm trả lời ngắn.** Thí sinh trả lời từ câu 1 đến câu 6.\n\n')
        for question_set in data.get("shortQuestions", []):
            if len(question_set.get("list", [])) > file_index:
                question = question_set["list"][file_index]
 
                # Xử lý phần content và hình ảnh
                content = escape_xml_chars(unescape_latex_chars(question["content"]))
                content = process_content(content, question['image'], question)  # Thêm xử lý ảnh
                if question.get("image"):
                    content = content.replace("[mô tả ảnh]", f"![Hình minh họa 1]({question['image']})")
                f.write(f'**Câu {question_set["questionNumber"]}:** {content}\n\n')
 
                # Xử lý các bảng
                if question["tables"] :
                    for table in question["tables"]:
                        if table["title"]:
                            f.write(f'{table["title"]}\n\n')
                        f.write(f'{json_to_markdown_table(table)}\n\n')
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
    """Chuyển đổi file Markdown thành file .docx bằng Pandoc với file mẫu tùy chọn."""
    try:
        # Lệnh cơ bản
        cmd = ['pandoc', markdown_file, '-o', docx_file]
       
        # Nếu có file mẫu, thêm tùy chọn --reference-doc
        # if template_file:
        #     cmd.extend(['--reference-doc', template_file])
       
        # Chạy lệnh Pandoc
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as err:
        print(f"Lỗi khi chạy Pandoc: {err}")
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
                   num_files = max(num_files, len(question_set["list"]))
 
    for file_index in range(num_files):
        markdown_file = os.path.join(markdown_dir, f'Đề_{file_index + 1}.md')
        docx_file = os.path.join(output_dir, f'Đề_{file_index + 1}.docx')
 
        json_to_markdown(data, markdown_file, file_index)
        if markdown_to_docx(markdown_file, docx_file):
            print(f"Đã tạo file .docx: {docx_file}")
        else:
            print(f"Không thể tạo file .docx: {docx_file}")
 
if __name__ == "__main__":
    with open(r'Đề GK2 Toán 10_full lời giải - Copy (2)_gemini_output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
   
    # # File mẫu template
    # template_file = "E:/App/sinhde/template.docx"
   
    create_docx_files_with_pandoc(data)
    print("Hoàn thành việc tạo các file .docx bằng Pandoc!")