import matplotlib.pyplot as plt

# --- SỬA LỖI FONT & CẤU HÌNH ---
# Sử dụng font 'DejaVu Sans' vì nó mặc định hỗ trợ tốt và có sẵn trên hầu hết các hệ thống (Linux/GitHub)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Tahoma']
plt.rcParams['axes.unicode_minus'] = False 

def generate_years(start_year, intervals, limit=2060):
    years = []
    current = start_year
    idx = 0
    while current <= limit:
        if current >= 1900:
            years.append(current)
        current += intervals[idx % len(intervals)]
        idx += 1
    return years

# 1. Các năm Hoảng loạn (Panic) - Chu kỳ: 16, 18, 20
panic_years = generate_years(1891, [20, 16, 18], limit=2059)

# 2. Các năm Giá cao (Good Times/Sell) - Chu kỳ: 8, 9, 10
high_years = generate_years(1891, [8, 9, 10], limit=2059)

# 3. Các năm Giá thấp (Hard Times/Buy) - Chu kỳ: 16, 18, 20
low_years = generate_years(1897, [18, 20, 16], limit=2059)

# Vẽ biểu đồ
plt.figure(figsize=(25, 10))
plt.style.use('seaborn-v0_8-muted')

# Vẽ các điểm dữ liệu
plt.scatter(panic_years, [3]*len(panic_years), color='#e74c3c', s=120, label='A: Năm Hoảng Loạn (Panic)', zorder=5)
plt.scatter(high_years, [2]*len(high_years), color='#f1c40f', s=120, label='B: Giá Cao (Nên Bán)', zorder=5)
plt.scatter(low_years, [1]*len(low_years), color='#2ecc71', s=120, label='C: Giá Thấp (Nên Mua)', zorder=5)

# Kết nối các điểm theo thứ tự thời gian để tạo đường zigzag
all_pts = sorted([(y, 3) for y in panic_years] + [(y, 2) for y in high_years] + [(y, 1) for y in low_years])
plt.plot([p[0] for p in all_pts], [p[1] for p in all_pts], color='black', alpha=0.3, linestyle='-', linewidth=1)

# Ghi nhãn tất cả các năm trên biểu đồ
for y, val in all_pts:
    plt.text(y, val + 0.1, str(y), fontsize=9, ha='center', rotation=45, fontweight='bold')

# Định dạng biểu đồ
plt.title("SƠ ĐỒ CHU KỲ BENNER TOÀN DIỆN (1900 - 2059)", fontsize=22, pad=30, fontweight='bold')
plt.yticks([1, 2, 3], ['GIÁ THẤP (MUA)', 'GIÁ CAO (BÁN)', 'HOẢNG LOẠN (PANIC)'], fontsize=12)
plt.xticks(range(1900, 2065, 5))
plt.grid(axis='x', alpha=0.3)
plt.legend(loc='upper right', frameon=True)
plt.xlim(1895, 2062)
plt.ylim(0.5, 3.8)

plt.tight_layout()

# --- QUAN TRỌNG ĐỂ LÀM GITHUB ---
# Lưu biểu đồ thành file ảnh để hiển thị trong README
plt.savefig('benner_cycle_chart.png', dpi=300, bbox_inches='tight')
print("Đã lưu biểu đồ vào file 'benner_cycle_chart.png'")

plt.show()
