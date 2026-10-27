/* Cấu hình frontend Law GPT – Infranixx.
 * Tự động kết nối tới Backend API nếu chạy cùng nguồn, hoặc kết nối tới port 8000.
 */
window.LAWGPT_CONFIG = {
  apiBase: window.location.origin || "http://localhost:8000",
  sourceName: "Cục Quản lý Dược – Bộ Y tế Việt Nam (DAV)",
  sourceUrl: "https://dav.gov.vn"
};
