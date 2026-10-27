# Law GPT – Tra cứu thuốc (Infranixx)

Dự án tra cứu thuốc với dữ liệu tham khảo từ Cục Quản lý Dược – Bộ Y tế Việt Nam, do **Infranixx** thực hiện.
Trợ lý AI hiển thị nút bấm (nhóm thuốc, tên thuốc) thông minh, tích hợp tra cứu triệu chứng, tờ thông tin thuốc chi tiết và thống kê.

---

## Cấu trúc dự án

```text
law-gpt/
├─ frontend/                 # Giao diện web người dùng (SPA)
│  ├─ index.html             # Trang giao diện chính
│  ├─ css/style.css          # Giao diện responsive, hỗ trợ Dark/Light mode tự động
│  ├─ js/app.js              # Xử lý trợ lý AI, tờ thông tin thuốc, danh mục, lọc dữ liệu
│  ├─ js/config.js           # Cấu hình kết nối API backend (apiBase)
│  ├─ js/sample-data.js      # Dữ liệu cache đồng bộ trực tiếp từ Database SQLite
│  └─ img/
│     ├─ logo.png            # Logo Infranixx
│     └─ charts/*.png        # Biểu đồ thống kê (matplotlib), bản sáng và tối
├─ backend/
│  ├─ server.py              # Máy chủ Unified Backend API (REST API + Phục vụ Static Files)
│  ├─ init_db.py             # Script khởi tạo và nạp dữ liệu chuẩn Bộ Y tế vào SQLite
│  └─ build_frontend_data.py # Script sinh biểu đồ và file tĩnh từ dữ liệu
├─ data/
│  ├─ drugs.db               # Cơ sở dữ liệu SQLite chính thức (bảng drugs, drug_groups)
│  ├─ groups.csv             # Danh mục nhóm thuốc
│  ├─ drugs.csv              # Danh mục thuốc chuẩn Bộ Y tế
│  └─ drugs_sample.csv       # File mẫu ban đầu
├─ requirements.txt          # Thư viện Python phụ trợ (pandas, numpy, matplotlib)
└─ README.md                 # Tài liệu dự án
```

---

## Khởi chạy dự án

### 1. Khởi tạo Cơ sở dữ liệu (SQLite)
Hệ thống đã có sẵn dữ liệu chuẩn hóa của hơn 42 loại biệt dược phổ biến tại Việt Nam với số đăng ký thực từ Cục Quản lý Dược. Nếu muốn reset hoặc nạp lại CSDL:

```bash
python3 backend/init_db.py
```

### 2. Khởi chạy máy chủ Backend API & Web (Port 8000)
Chạy trực tiếp server tích hợp (hỗ trợ REST API và Frontend):

```bash
python3 backend/server.py
```

Mở trình duyệt truy cập: **[http://localhost:8000](http://localhost:8000)**

---

## Các API cung cấp

| Phương thức | Endpoint | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/api/drugs` | Lấy toàn bộ danh sách thuốc và nhóm thuốc từ SQLite |
| `GET` | `/api/drugs/<id>` | Lấy chi tiết 1 loại thuốc (chỉ định, liều dùng, tác dụng phụ, quy cách) |
| `GET` | `/api/stats` | Thống kê số lượng thuốc theo nhóm và theo dạng bào chế |
| `GET` | `/api/search?q=...` | Tìm kiếm thuốc theo tên, hoạt chất, số đăng ký |
| `POST` | `/api/chat` | Trợ lý AI phân tích triệu chứng/nhu cầu, giải đáp thông tin và gợi ý nút bấm |

---

## Bản quyền
© 2026 Infranixx. Dự án Law GPT – Tra cứu thuốc. Dữ liệu tham khảo từ Cục Quản lý Dược – Bộ Y tế.
