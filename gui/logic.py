import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
from fractions import Fraction
from pdf2image import convert_from_path
import os
import subprocess
import google.generativeai as genai
import time
import platform


# Hàm để biên dịch LaTeX với MiKTeX
def compile_latex_to_pdf(latex_code, output_path):
    with open("temp.tex", "w", encoding="utf-8") as f:
        f.write(latex_code)

    result = subprocess.run(["pdflatex", "temp.tex"], capture_output=True, text=True)

    if result.stderr:
        print("Error during LaTeX compilation:", result.stderr)
        messagebox.showerror("Lỗi", "Lỗi khi biên dịch LaTeX. Xem chi tiết trong log.")
        return False

    # Kiểm tra nếu tệp temp.pdf tồn tại
    if not os.path.exists("temp.pdf"):
        print("Tệp temp.pdf không tồn tại.")
        messagebox.showerror("Lỗi", "Không thể tạo tệp PDF từ LaTeX.")
        return False

    # Kiểm tra và tạo thư mục nếu không tồn tại
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Di chuyển tệp temp.pdf
    if os.path.exists(output_path):
        os.remove(output_path)
    os.rename("temp.pdf", output_path)

    # Xóa các tệp tạm thời
    for ext in [".tex", ".log", ".aux"]:
        if os.path.exists(f"temp{ext}"):
            os.remove(f"temp{ext}")

    return True

# Hàm để chuyển đổi PDF sang PNG
def pdf_to_png(pdf_path, image_path):
    images = convert_from_path(pdf_path)
    images[0].save(image_path, 'PNG')

# Hàm để tạo mã LaTeX cho đồ thị các hàm số
def create_latex_code_for_function(function_type, parameters):
    def format_number(n):
        """Chuyển đổi số thực thành chuỗi số nguyên nếu cần."""
        return int(n) if n == int(n) else n

    latex_code = "\\documentclass[border=10pt]{standalone}\n"
    latex_code += "\\usepackage{tikz}\n"
    latex_code += "\\begin{document}\n"
    latex_code += "\\begin{tikzpicture}[scale=0.6, line join=round, line cap=round,>=stealth, thick]\n"
    latex_code += "\\tikzset{every node/.style={scale=0.9}}\n"
    latex_code += "\\draw[gray!20] (-6,-6) grid (6,6);\n"
    latex_code += "\\draw[->] (-6,0) -- (6,0) node[below left] {$x$};\n"
    latex_code += "\\draw[->] (0,-6) -- (0,6) node[below left] {$y$};\n"
    latex_code += "\\foreach \\x in {-6,-5,...,6} \\draw[thin] (\\x,1pt) -- (\\x,-1pt) node[below] {\\footnotesize $\\x$};\n"
    latex_code += "\\foreach \\y in {-6,-5,...,6} \\draw[thin] (1pt,\\y) -- (-1pt,\\y) node[left] {\\footnotesize $\\y$};\n"
    latex_code += "\\begin{scope}\n\\clip (-6,-6) rectangle (6,6);\n"

    if function_type == 'Bậc nhất':
        a, b = map(format_number, parameters)
        latex_code += f"\\draw[blue, thick, smooth, domain=-6:6] plot (\\x, {{ {a}*\\x + {b} }});\n"

    elif function_type == 'Bậc hai':
        a, b, c = map(format_number, parameters)
        latex_code += f"\\draw[blue, thick, smooth, domain=-6:6, samples=100] plot (\\x, {{ {a}*\\x*\\x + {b}*\\x + {c} }});\n"

    elif function_type == 'Bậc ba':
        a, b, c, d = map(format_number, parameters)
        latex_code += f"\\draw[blue, thick, smooth, domain=-3:3, samples=100] plot (\\x, {{ {a}*\\x*\\x*\\x + {b}*\\x*\\x + {c}*\\x + {d} }});\n"

    elif function_type == 'Bậc bốn trùng phương':
        a, b, c = map(format_number, parameters)
        latex_code += f"\\draw[blue, thick, smooth, domain=-3:3, samples=100] plot (\\x, {{ {a}*\\x*\\x*\\x*\\x + {b}*\\x*\\x + {c} }});\n"

    elif function_type == 'Phân thức bậc nhất/bậc nhất':
        a, b, c, d = map(format_number, parameters)
        if c != 0:
            vertical_asymptote = -d / c
            horizontal_asymptote = a / c
            epsilon = 0.1  # Khoảng cách nhỏ để bỏ qua vùng gần tiệm cận đứng
            # Vẽ đường tiệm cận đứng (nét đứt, màu đỏ)
            latex_code += f"\\draw[red, dashed, thick] ({vertical_asymptote}, -6) -- ({vertical_asymptote}, 6);\n"
            # Vẽ đường tiệm cận ngang (nét đứt, màu đỏ)
            latex_code += f"\\draw[red, dashed, thick] (-6, {horizontal_asymptote}) -- (6, {horizontal_asymptote});\n"
            # Vẽ đồ thị hàm phân thức (chia miền bỏ qua vùng tiệm cận đứng)
            latex_code += f"\\draw[blue, thick, smooth, domain=-6:{vertical_asymptote - epsilon}, samples=100] plot (\\x, {{ ({a}*\\x + {b}) / ({c}*\\x + {d}) }});\n"
            latex_code += f"\\draw[blue, thick, smooth, domain={vertical_asymptote + epsilon}:6, samples=100] plot (\\x, {{ ({a}*\\x + {b}) / ({c}*\\x + {d}) }});\n"

    elif function_type == 'Phân thức bậc hai/bậc nhất':
        a, b, c, d, e = map(format_number, parameters)
        if d != 0:
            vertical_asymptote = -e / d
            epsilon = 0.1  # Khoảng cách nhỏ để tránh tiệm cận đứng
            # Vẽ đồ thị phân thức bậc hai / bậc nhất (chia miền)
            latex_code += f"\\draw[blue, thick, smooth, domain=-6:{vertical_asymptote - epsilon}, samples=100] plot (\\x, {{ ({a}*\\x*\\x + {b}*\\x + {c}) / ({d}*\\x + {e}) }});\n"
            latex_code += f"\\draw[blue, thick, smooth, domain={vertical_asymptote + epsilon}:6, samples=100] plot (\\x, {{ ({a}*\\x*\\x + {b}*\\x + {c}) / ({d}*\\x + {e}) }});\n"
            # Vẽ đường tiệm cận đứng (nét đứt, màu đỏ)
            latex_code += f"\\draw[red, dashed, thick] ({vertical_asymptote}, -6) -- ({vertical_asymptote}, 6);\n"
        else:
            # Trường hợp không có tiệm cận đứng
            latex_code += f"\\draw[blue, thick, smooth, domain=-6:6, samples=100] plot (\\x, {{ ({a}*\\x*\\x + {b}*\\x + {c}) / ({d}*\\x + {e}) }});\n"

    latex_code += "\\end{scope}\n\\end{tikzpicture}\n\\end{document}"
    return latex_code

# Hàm để tạo mã LaTeX cho bảng biến thiên
def format_as_latex_fraction(value):
    frac = Fraction(value).limit_denominator()
    return f"\\frac{{{frac.numerator}}}{{{frac.denominator}}}" if frac.denominator != 1 else str(frac.numerator)

def calculate_cubic_y(a, b, c, d, x):
    return a * x**3 + b * x**2 + c * x + d

def create_latex_code_for_table(function_type, parameters):
    latex_code = "\\documentclass[border=2pt]{standalone}\n"
    latex_code += "\\usepackage{tkz-tab,tikz}\n"
    latex_code += "\\usetikzlibrary{calc,intersections,patterns}\n"
    latex_code += "\\begin{document}\n"
    latex_code += "\\begin{tikzpicture}\n"

    if function_type == 'Bậc hai':
        a, b, c = map(Fraction, parameters)  # Chuyển a, b, c thành phân số
        vertex = -b / (2 * a)
        y_vertex = a * vertex**2 + b * vertex + c

        latex_code += "\\tkzTabInit[nocadre=false, lgt=1, espcl=1.5]\n"
        latex_code += "{$x$ /1,$y$ /2}\n"
        latex_code += f"{{$-\\infty$, {vertex}, $+\\infty$}}\n"

        if a > 0:
            latex_code += f"\\tkzTabVar{{+/ $+\\infty$, -/ ${format_as_latex_fraction(y_vertex)}$, +/ $+\\infty$}}\n"
        else:
            latex_code += f"\\tkzTabVar{{-/ $-\\infty$, +/ ${format_as_latex_fraction(y_vertex)}$, -/ $-\\infty$}}\n"

    elif function_type == 'Bậc ba':
        a, b, c, d = parameters
        a1, b1, c1 = 3 * a, 2 * b, c
        delta = b1**2 - 4 * a1 * c1

        latex_code += "\\tkzTabInit[nocadre=false, lgt=1, espcl=1.5]\n"
        latex_code += "{$x$ /1, $y'$ /1, $y$ /2}\n"

        if delta > 0:
            x1 = (-b1 - delta**0.5) / (2 * a1)
            x2 = (-b1 + delta**0.5) / (2 * a1)
            y1 = calculate_cubic_y(Fraction(a), Fraction(b), Fraction(c), Fraction(d), Fraction(x1))
            y2 = calculate_cubic_y(Fraction(a), Fraction(b), Fraction(c), Fraction(d), Fraction(x2))

            if x1 > x2:
                x1, x2 = x2, x1
                y1, y2 = y2, y1

            x1_formatted = format_as_latex_fraction(x1)
            x2_formatted = format_as_latex_fraction(x2)
            y1_formatted = format_as_latex_fraction(y1)
            y2_formatted = format_as_latex_fraction(y2)

            latex_code += f"{{$-\\infty$, ${x1_formatted}$, ${x2_formatted}$, $+\\infty$}}\n"
            if a > 0:
                latex_code += "\\tkzTabLine{,+,0,-,0,+}\n"
                latex_code += f"\\tkzTabVar{{-/$-\\infty$, +/${y1_formatted}$, -/${y2_formatted}$, +/$+\\infty$}}\n"
            else:
                latex_code += "\\tkzTabLine{,-,0,+,0,-}\n"
                latex_code += f"\\tkzTabVar{{+/$+\\infty$, -/${y1_formatted}$, +/${y2_formatted}$, -/$-\\infty$}}\n"

        elif delta == 0:
            x0 = -b1 / (2 * a1)
            y0 = calculate_cubic_y(Fraction(a), Fraction(b), Fraction(c), Fraction(d), Fraction(x0))
            x0_formatted = format_as_latex_fraction(x0)
            y0_formatted = format_as_latex_fraction(y0)

            latex_code += f"{{$-\\infty$, ${x0_formatted}$, $+\\infty$}}\n"
            if a > 0:
                latex_code += "\\tkzTabLine{,+,0,+}\n"
                latex_code += f"\\tkzTabVar{{-/$-\\infty$, +/${y0_formatted}$, +/$+\\infty$}}\n"
            else:
                latex_code += "\\tkzTabLine{,-,0,-}\n"
                latex_code += f"\\tkzTabVar{{+/$+\\infty$, -/${y0_formatted}$, -/$-\\infty$}}\n"

        else:
            latex_code += "{$-\\infty$, $+\\infty$}\n"
            if a > 0:
                latex_code += "\\tkzTabLine{,+}\n"
                latex_code += "\\tkzTabVar{-/$-\\infty$, +/$+\\infty$}\n"
            else:
                latex_code += "\\tkzTabLine{,-}\n"
                latex_code += "\\tkzTabVar{+/$+\\infty$, -/$-\\infty$}\n"

    elif function_type == 'Bậc bốn trùng phương':
        a, b, c = parameters
        critical_points = []

        # Tìm điểm tới hạn
        if b / (2 * a) < 0:  # Điều kiện tồn tại nghiệm x = ±√(-b/2a)
            root = (-b / (2 * a))**0.5
            critical_points.extend([-root, 0, root])
        else:
            critical_points.append(0)

        # Sắp xếp các điểm tới hạn
        critical_points = sorted(set(critical_points))
        
        # Tính giá trị tại các điểm tới hạn
        y_values = [a * x**4 + b * x**2 + c for x in critical_points]

        # Bắt đầu tạo bảng biến thiên
        latex_code += "\\tkzTabInit[nocadre=false, lgt=1, espcl=1.5]\n"
        latex_code += "{$x$ /1,$y'$ /1,$y$ /2}\n"
        latex_code += "{"
        latex_code += ", ".join(
            f"$-\infty$" if x == -float("inf") else 
            (f"$+\infty$" if x == float("inf") else f"${format_as_latex_fraction(x)}$")
            for x in [-float("inf"), *critical_points, float("inf")]
        )
        latex_code += "}\n"

        # Xét dấu của y' và vẽ bảng biến thiên
        if len(critical_points) == 1:  # Chỉ có một điểm tới hạn (x = 0)
            if a > 0:
                latex_code += "\\tkzTabLine{,-,0,+}\n"
                latex_code += (
                    "\\tkzTabVar{+/ $+\\infty$, "
                    f"-/ ${format_as_latex_fraction(y_values[0])}$, "
                    "+/$+\\infty$}\n"
                )
            else:
                latex_code += "\\tkzTabLine{,+,0,-}\n"
                latex_code += (
                    "\\tkzTabVar{-/ $-\\infty$, "
                    f"+/ ${format_as_latex_fraction(y_values[0])}$, "
                    "-/$-\\infty$}\n"
                )
        else:  # Nhiều điểm tới hạn
            if a > 0:
                latex_code += "\\tkzTabLine{,-,0,+,0,-,0,+}\n"
                latex_code += (
                    "\\tkzTabVar{+/ $+\\infty$, "
                    + ", ".join(f"-/ ${format_as_latex_fraction(y_values[i])}$" if i % 2 == 0 else f"+/ ${format_as_latex_fraction(y_values[i])}$" for i in range(len(y_values)))
                    + ", +/$+\\infty$}\n"
                )
            else:
                latex_code += "\\tkzTabLine{,+,0,-,0,+,0,-}\n"
                latex_code += (
                    "\\tkzTabVar{-/ $-\\infty$, "
                    + ", ".join(f"+/ ${format_as_latex_fraction(y_values[i])}$" if i % 2 == 0 else f"-/ ${format_as_latex_fraction(y_values[i])}$" for i in range(len(y_values)))
                    + ", -/$-\\infty$}\n"
                )

    elif function_type == 'Phân thức bậc nhất/bậc nhất':
        a, b, c, d = parameters
        latex_code += "% Hàm phân thức bậc nhất/bậc nhất: y = (ax + b) / (cx + d)\n"

        # Tính nghiệm và tiệm cận
        zero = -b / a if a != 0 else None
        asymptote_vert = -d / c if c != 0 else None
        asymptote_horiz = a / c if c != 0 else None
        discriminant = a * d - b * c  # Tính y'

        # Tạo bảng biến thiên
        latex_code += "\\tkzTabInit[nocadre=false,lgt=1.5,espcl=3]\n"
        latex_code += "{$x$ /1,$y'$ /1,$y$ /2}\n"

        # Các điểm đặc biệt trên trục x
        x_points = ["$-\\infty$"]
        if asymptote_vert is not None:
            x_points.append(f"$\\frac{{{int(-d)}}}{{{int(c)}}}$")
        x_points.append("$+\\infty$")
        latex_code += "{" + ",".join(x_points) + "}\n"

        # Hàng y'
        if discriminant > 0:
            latex_code += "\\tkzTabLine{,+,d,+,}\n"
        elif discriminant < 0:
            latex_code += "\\tkzTabLine{,-,d,-,}\n"
        else:
            latex_code += "\\tkzTabLine{,z,d,z,}\n"

        # Hàng y
        latex_code += "\\tkzTabVar{"
        if asymptote_horiz is not None:
            asym_horiz_str = f"$\\frac{{{int(a)}}}{{{int(c)}}}$"
            if discriminant > 0:
                # Hàm giảm trước tiệm cận, tăng sau tiệm cận
                latex_code += f"-/ {asym_horiz_str} / , +D-/ $+\\infty$ / $-\\infty$ , +/ {asym_horiz_str} /"
            else:
                # Hàm tăng trước tiệm cận, giảm sau tiệm cận
                latex_code += f"+/ {asym_horiz_str} / , -D+/ $-\\infty$ / $+\\infty$ , -/ {asym_horiz_str} /"
        latex_code += "}\n"

    elif function_type == 'Phân thức bậc hai/bậc nhất':
        a, b, c, d, e = parameters
        latex_code += "% Hàm phân thức bậc hai trên bậc nhất: y = (ax^2 + bx + c) / (dx + e)\n"

        # Tính nghiệm và tiệm cận
        discriminant_numerator = b**2 - 4*a*c  # Định thức của tử số
        x_intercepts = []
        if discriminant_numerator >= 0:
            x_intercepts.append((-b + discriminant_numerator**0.5) / (2 * a))
            x_intercepts.append((-b - discriminant_numerator**0.5) / (2 * a))

        asymptote_vert = -e / d if d != 0 else None  # Tiệm cận thẳng đứng
        
        # Tính tiệm cận ngang (khi x → ±∞)
        asymptote_horiz = a / d if d != 0 else None  # Tiệm cận ngang

        # Tạo bảng biến thiên
        latex_code += "\\tkzTabInit[nocadre=false,lgt=1.5,espcl=3]\n"
        latex_code += "{$x$ /1,$y'$ /1,$y$ /2}\n"

        # Các điểm đặc biệt trên trục x
        x_points = ["$-\\infty$"]
        if asymptote_vert is not None:
            x_points.append(f"$\\frac{{{-e}}}{{{d}}}$")
        if x_intercepts:
            for xi in x_intercepts:
                x_points.append(f"$\\frac{{{int(xi)}}}{{1}}$")
        x_points.append("$+\\infty$")
        latex_code += "{" + ",".join(x_points) + "}\n"

        # Hàng y'
        latex_code += "\\tkzTabLine{,+,d,+,}\n"  # Tạo dòng y'

        # Hàng y
        latex_code += "\\tkzTabVar{"
        if asymptote_horiz is not None:
            asym_horiz_str = f"$\\frac{{{int(a)}}}{{{int(d)}}}$"
            latex_code += f"+/ {asym_horiz_str} / , -/ $+\\infty$ / $-\\infty$ , -/ {asym_horiz_str} /"
        latex_code += "}\n"

    latex_code += "\\end{tikzpicture}\n"
    latex_code += "\\end{document}\n"

    return latex_code

# Hàm xử lý thay đổi tên các đỉnh
def rename_latex_vertices(latex_code, new_names_input):
    try:
        # Tách tên mới từ đầu vào
        new_names = new_names_input.split(",")
        new_names = {chr(65 + i): name.strip() for i, name in enumerate(new_names) if name.strip()}

        # Kiểm tra trùng lặp trong danh sách tên mới
        unique_names = set(new_names.values())
        if len(unique_names) != len(new_names.values()):
            raise ValueError("Tên các đỉnh mới bị trùng lặp. Vui lòng nhập lại.")

        # Tạo prompt gửi đến API
        prompt = (
            "Hãy thay đổi tên đỉnh đoạn mã LaTeX hình học này "
            f"bằng các tên đỉnh mới sau đây: {', '.join(new_names.values())}\n"
            f"Mã LaTeX:\n{latex_code}\n"
            "## Lưu ý: Trả lời chính xác, không thêm thắt thừa thãi, chỉ cần gửi về mã LaTeX đã đổi tên đỉnh thôi! Không cần thêm cụm ```latex ```."
        )

        # Cấu hình API key
        API_KEY = 'AIzaSyDX_boeR-9xR1Doqq2IC4I5nFBJ6Frr5e4'  # Replace with your actual API key
        genai.configure(api_key=API_KEY)

        generation_config = {
            "temperature": 0.4,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        # **List available models**
        available_models = genai.list_models()
        print("Available models with their functionality:")
        for model in available_models:
            if "gemini" in model.name:
                print(model)

        # Choose a valid model name, ensure it supports 'generateContent' and replace it below if needed
        model_name = "gemini-2.0-flash-exp"

        # Create model object
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
        )
        response = model.generate_content(prompt)
        print("Response from API:", response.text)

        # Xử lý đoạn mã LaTeX trả về
        updated_latex_code = response.text.strip()
        if not updated_latex_code:
            raise ValueError("API không trả về kết quả hợp lệ.")

        # Loại bỏ các cụm ```latex và ```
        if updated_latex_code.startswith("```latex"):
            updated_latex_code = updated_latex_code[len("```latex"):].strip()
        if updated_latex_code.endswith("```"):
            updated_latex_code = updated_latex_code[:-len("```")].strip()
        
        return updated_latex_code
    

    except Exception as e:
        raise ValueError(f"Lỗi khi thay đổi tên đỉnh: {e}")
