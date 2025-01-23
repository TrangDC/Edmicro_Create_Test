import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from fractions import Fraction
from pdf2image import convert_from_path
from logic import compile_latex_to_pdf, pdf_to_png, create_latex_code_for_function,create_latex_code_for_table

# Hàm xử lý sự kiện tạo đồ thị từ tham số
def create_graph():
    function_type = function_choice.get()
    param_text = parameter_entry.get()

    try:
        parameters = tuple(
            float(Fraction(param.strip())) if '/' in param else float(param.strip())
            for param in param_text.split(",")
        )
    except ValueError:
        messagebox.showerror("Lỗi", "Vui lòng nhập đúng định dạng tham số (cách nhau bằng dấu phẩy)!")
        return

    if draw_type.get() == "Đồ thị":
        latex_code = create_latex_code_for_function(function_type, parameters)
    elif draw_type.get() == "Bảng biến thiên":
        latex_code = create_latex_code_for_table(function_type, parameters)
    else:
        messagebox.showerror("Lỗi", "Vui lòng chọn kiểu vẽ!")
        return

    output_pdf = f"{function_type}_output.pdf"
    output_image = f"{function_type}_output.png"

    if compile_latex_to_pdf(latex_code, output_pdf):
        pdf_to_png(output_pdf, output_image)
        messagebox.showinfo("Thành công", f"File PNG đã được tạo thành công!")
    else:
        messagebox.showerror("Lỗi", "Không thể tạo. Vui lòng kiểm tra lại LaTeX.")

# Hàm xử lý file JSON để lấy mã LaTeX và tạo ảnh
def process_json_file():
    file_path = filedialog.askopenfilename(
        title="Chọn file JSON",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    if not file_path:
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "graph" not in data:
            messagebox.showerror("Lỗi", "File JSON không chứa khóa 'graph'.")
            return

        latex_code = data["graph"]
        output_pdf = "json_output.pdf"
        output_image = "json_output.png"

        if compile_latex_to_pdf(latex_code, output_pdf):
            pdf_to_png(output_pdf, output_image)
            messagebox.showinfo("Thành công", "Ảnh từ JSON đã được tạo thành công!")
        else:
            messagebox.showerror("Lỗi", "Không thể tạo ảnh từ JSON. Vui lòng kiểm tra mã LaTeX.")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi xử lý file JSON:\n{e}")

# Hàm cập nhật công thức mẫu
def update_formula_display(event):
    formula_map = {
        "Bậc nhất": "f(x) = ax + b",
        "Bậc hai": "f(x) = ax² + bx + c",
        "Bậc ba": "f(x) = ax³ + bx² + cx + d",
        "Bậc bốn trùng phương": "f(x) = ax⁴ + bx² + c",
        "Phân thức bậc nhất/bậc nhất": "f(x) = (ax + b) / (cx + d)",
        "Phân thức bậc hai/bậc nhất": "f(x) = (ax² + bx + c) / (dx + e)"
    }
    selected_function = function_choice.get()
    formula_label.config(text=formula_map.get(selected_function, ""))

# Tạo giao diện với tkinter
root = tk.Tk()
root.title("Tạo đồ thị hàm số")

# Loại hàm
ttk.Label(root, text="Chọn loại hàm:").grid(row=0, column=0, padx=10, pady=5)
function_choice = ttk.Combobox(root, values=["Bậc nhất", "Bậc hai", "Bậc ba", "Bậc bốn trùng phương", "Phân thức bậc nhất/bậc nhất", "Phân thức bậc hai/bậc nhất"], state="readonly")
function_choice.grid(row=0, column=1, padx=10, pady=5)
function_choice.current(0)
function_choice.bind("<<ComboboxSelected>>", update_formula_display)

# Hiển thị công thức mẫu
ttk.Label(root, text="Công thức mẫu:").grid(row=1, column=0, padx=10, pady=5)
formula_label = ttk.Label(root, text="f(x) = ax + b", foreground="blue")
formula_label.grid(row=1, column=1, padx=10, pady=5)

# Nhập tham số
ttk.Label(root, text="Nhập tham số (cách nhau bằng dấu phẩy):").grid(row=2, column=0, padx=10, pady=5)
parameter_entry = ttk.Entry(root, width=40)
parameter_entry.grid(row=2, column=1, padx=10, pady=5)

# Kiểu vẽ
ttk.Label(root, text="Chọn kiểu vẽ:").grid(row=3, column=0, padx=10, pady=5)
draw_type = ttk.Combobox(root, values=["Đồ thị", "Bảng biến thiên"], state="readonly")
draw_type.grid(row=3, column=1, padx=10, pady=5)
draw_type.current(0)

# Nút tạo đồ thị
ttk.Button(root, text="Tạo", command=create_graph).grid(row=4, column=0, columnspan=2, pady=10)

# Nút chọn file JSON
ttk.Button(root, text="Tải file JSON", command=process_json_file).grid(row=5, column=0, columnspan=2, pady=10)

root.mainloop()
