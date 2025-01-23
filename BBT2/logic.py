import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
from fractions import Fraction
from pdf2image import convert_from_path

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
def create_latex_code_for_table(function_type, parameters):
    latex_code = "\\documentclass[border=2pt]{standalone}\n"
    latex_code += "\\usepackage{tkz-tab,tikz}\n"
    latex_code += "\\usetikzlibrary{calc,intersections,patterns}\n"
    latex_code += "\\begin{document}\n"
    latex_code += "\\begin{tikzpicture}\n"

    if function_type == 'Bậc hai':
        a, b, c = parameters
        vertex = -b / (2 * a)
        y_vertex = a * vertex**2 + b * vertex + c
        latex_code += "\\tkzTabInit[nocadre=false, lgt=1, espcl=1.5]\n"
        latex_code += "{$x$ /1,$y$ /2}\n"
        latex_code += f"{{$-\\infty$, {vertex}, $+\\infty$}}\n"
        if a > 0:
            # Nếu a > 0, đồ thị giảm từ +∞ đến đỉnh (y_vertex), sau đó tăng lên +∞
            latex_code += f"\\tkzTabVar{{+/$+\\infty$, -/{y_vertex}, +/$+\\infty$}}\n"
        else:
            # Nếu a < 0, đồ thị tăng từ -∞ đến đỉnh (y_vertex), sau đó giảm xuống -∞
            latex_code += f"\\tkzTabVar{{-/$-\\infty$, +/{y_vertex}, -/$-\\infty$}}\n"

    elif function_type == 'Bậc ba':
        a, b, c, d = parameters
        # Đạo hàm: y' = 3a*x^2 + 2b*x + c
        a1, b1, c1 = 3 * a, 2 * b, c  # Các hệ số của y'
        delta = b1**2 - 4 * a1 * c1  # Delta của phương trình y' = 0
        
        latex_code += "\\tkzTabInit[nocadre=false, lgt=1, espcl=1.5]\n"
        latex_code += "{$x$ /1,$y'$ /1,$y$ /2}\n"
        
        if delta > 0:  # 2 nghiệm phân biệt
            x1 = (-b1 - delta**0.5) / (2 * a1)
            x2 = (-b1 + delta**0.5) / (2 * a1)
            y1 = a * x1**3 + b * x1**2 + c * x1 + d
            y2 = a * x2**3 + b * x2**2 + c * x2 + d
            
            # Sắp xếp x1, x2 theo thứ tự tăng dần
            if x1 > x2:
                x1, x2 = x2, x1
                y1, y2 = y2, y1
            
            # Chuyển x1, x2 gần 0 về 0 nếu cần
            x1 = 0 if abs(x1) < 1e-10 else x1
            x2 = 0 if abs(x2) < 1e-10 else x2
            
            latex_code += f"{{$-\\infty$, {x1:.2f}, {x2:.2f}, $+\\infty$}}\n"
            if a > 0:
                latex_code += "\\tkzTabLine{,+,0,-,0,+}\n"
                latex_code += f"\\tkzTabVar{{-/$-\\infty$, +/{y1:.2f}, -/{y2:.2f}, +/$+\\infty$}}\n"
            else:
                latex_code += "\\tkzTabLine{,-,0,+,0,-}\n"
                latex_code += f"\\tkzTabVar{{+/$+\\infty$, -/{y1:.2f}, +/{y2:.2f}, -/$-\\infty$}}\n"
        
        elif delta == 0:  # Nghiệm kép
            x0 = -b1 / (2 * a1)
            y0 = a * x0**3 + b * x0**2 + c * x0 + d
            # Chuyển x0 gần 0 về 0 nếu cần
            x0 = 0 if abs(x0) < 1e-10 else x0
            
            latex_code += f"{{$-\\infty$, {x0:.2f}, $+\\infty$}}\n"
            if a > 0:
                latex_code += "\\tkzTabLine{,+,0,+}\n"
                latex_code += f"\\tkzTabVar{{-/$-\\infty$, +/{y0:.2f}, +/$+\\infty$}}\n"
            else:
                latex_code += "\\tkzTabLine{,-,0,-}\n"
                latex_code += f"\\tkzTabVar{{+/$+\\infty$, -/{y0:.2f}, -/$-\\infty$}}\n"
        
        else:  # Không có nghiệm
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
        if b != 0:
            discriminant = -b / (2 * a)
            if discriminant > 0:
                root1 = (discriminant)**0.5
                root2 = -(discriminant)**0.5
                critical_points.extend([root2, 0, root1])
            else:
                critical_points.append(0)
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
        latex_code += ", ".join(f"$-\infty$" if x == -float("inf") else (f"$+\infty$" if x == float("inf") else f"${x:.2f}$") for x in [-float("inf"), *critical_points, float("inf")])
        latex_code += "}\n"

        # Xét dấu và vẽ bảng biến thiên
        if a > 0:
            latex_code += "\\tkzTabLine{,-,0,+,0,-,0,+}\n"
            latex_code += (
                "\\tkzTabVar{+/ $+\\infty$, "
                f"-/ ${y_values[0]:.2f}$, "
                f"+/ ${y_values[1]:.2f}$, "
                f"-/ ${y_values[2]:.2f}$, "
                "+/$+\\infty$}\n"
            )
        else:
            latex_code += "\\tkzTabLine{,+,0,-,0,+,0,-}\n"
            latex_code += (
                "\\tkzTabVar{-/ $-\\infty$, "
                f"+/ ${y_values[0]:.2f}$, "
                f"-/ ${y_values[1]:.2f}$, "
                f"+/ ${y_values[2]:.2f}$, "
                "-/$-\\infty$}\n"
            )

    elif function_type == 'Phân thức bậc nhất/bậc nhất':
        a, b, c, d = parameters
        # Tính nghiệm và tiệm cận
        zero = -b / a if a != 0 else None
        asymptote = -d / c if c != 0 else None

        latex_code += "\\tkzTabInit[nocadre=false,lgt=1.5,espcl=3]\n"
        latex_code += "{$x$ /1,$y'$ /1,$y$ /2}\n"
        latex_code += f"{{$-\\infty$, {zero:.2f}, $+\\infty$}}\n"
        latex_code += "\\tkzTabLine{,-,d,+,}\n"
        latex_code += f"\\tkzTabVar{{+/ $+\\infty$, -/ $y = {zero:.2f}$, +/ $y = {asymptote:.2f}$}}\n"


    elif function_type == 'Phân thức bậc nhất/bậc nhất':
        a, b, c, d = parameters
        # Tính nghiệm và tiệm cận
        zero = -b / a if a != 0 else "Không xác định"
        asymptote = -d / c if c != 0 else "Không xác định"

        latex_code += "\\tkzTabInit[nocadre=false,lgt=1.5,espcl=3]\n"
        latex_code += "{$x$ /1,$y'$ /1,$y$ /2}\n"
        latex_code += f"{{$-\\infty$,$- {zero}$,$+\\infty$}}\n"
        latex_code += "\\tkzTabLine{,-,d,-,}\n"
        latex_code += f"\\tkzTabVar{{+/ {zero} / , -D+/ $-\\infty$ / $+\\infty$ , -/ {asymptote} /}}\n"

    elif function_type == 'Phân thức bậc hai/bậc nhất':
        a, b, c, d = parameters
        discriminant = b**2 - 4*a*c
        if discriminant > 0:
            root1 = (-b + discriminant**0.5) / (2 * a)
            root2 = (-b - discriminant**0.5) / (2 * a)
            latex_code += "\\tkzTabInit[nocadre=false, lgt=1, espcl=1.5]\n"
            latex_code += "{$x$ /1,$y$ /2}\n"
            latex_code += f"{{$-\\infty$, {root1}, {root2}, $+\\infty$}}\n"
            if a > 0:
                latex_code += f"\\tkzTabVar{{-/$-\\infty$ , +/{root1} , -/{root2} , +/$+\\infty$}}\n"
            else:
                latex_code += f"\\tkzTabVar{{+/$+\\infty$ , -/{root1} , +/{root2} , -/$-\\infty$}}\n"
        else:
            latex_code += "\\tkzTabInit[nocadre=false, lgt=1, espcl=1.5]\n"
            latex_code += "{$x$ /1,$y$ /2}\n"
            latex_code += "{$-\\infty$, $+\\infty$}\n"
            if a > 0:
                latex_code += "\\tkzTabVar{-/$-\\infty$ , +/$+\\infty$}\n"
            else:
                latex_code += "\\tkzTabVar{+/$+\\infty$ , -/$-\\infty$}\n"

    latex_code += "\\end{tikzpicture}\n\\end{document}"
    return latex_code
