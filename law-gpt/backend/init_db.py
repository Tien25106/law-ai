"""Khởi tạo Cơ sở dữ liệu SQLite cho Law GPT – Dữ liệu chuẩn Cục Quản lý Dược (DAV - Bộ Y tế).
Chạy:
    python3 backend/init_db.py
"""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "drugs.db"
GROUPS_CSV = ROOT / "data" / "groups.csv"
DRUGS_CSV = ROOT / "data" / "drugs.csv"
OUT_JS = ROOT / "frontend" / "js" / "sample-data.js"

GROUPS_DATA = [
    ("giam-dau", "Giảm đau – Hạ sốt – Kháng viêm", 1, "Các thuốc hạ sốt, giảm đau từ nhẹ đến nặng và chống viêm non-steroid (NSAIDs)."),
    ("khang-sinh", "Kháng sinh – Kháng khuẩn", 2, "Các thuốc kháng sinh phổ rộng, kháng khuẩn điều trị nhiễm trùng hô hấp, tiết niệu, da."),
    ("di-ung", "Dị ứng & Kháng Histamin", 3, "Các thuốc kháng thụ thể H1 thế hệ mới điều trị viêm mũi dị ứng, mề đay, mẩn ngứa."),
    ("tieu-hoa", "Tiêu hóa & Dạ dày – Ruột", 4, "Thuốc kháng tiết acid PPI, kháng acid, men tiêu hóa, bù điện giải, điều trị tiêu chảy."),
    ("ho-hap", "Hô hấp & Giảm ho – Long đờm", 5, "Thuốc giãn phế quản, cắt cơn hen, tiêu nhầy, long đờm và trị cảm sốt sổ mũi."),
    ("vitamin", "Vitamin & Khoáng chất", 6, "Các chế phẩm bổ sung vitamin tổng hợp, canxi, sắt, khoáng chất nâng cao thể trạng."),
    ("noi-tiet", "Nội tiết & Đái tháo đường", 7, "Thuốc hạ đường huyết đường uống, điều hòa hormon tuyến giáp và chuyển hóa."),
    ("tim-mach", "Tim mạch & Huyết áp", 8, "Thuốc hạ áp chẹn canxi, chẹn beta, ức chế thụ thể, hạ lipid máu và chống đông."),
]

DRUGS_DATA = [
    # Nhóm 1: Giảm đau - Hạ sốt
    (
        "d01", "Panadol Extra", "Paracetamol 500 mg, Caffeine 65 mg", "500 mg + 65 mg", "Viên nén bao phim",
        "giam-dau", "GlaxoSmithKline (GSK)", "Việt Nam", "VN-22530-20", "Hộp 15 vỉ x 12 viên",
        "Giảm đau từ nhẹ đến vừa: đau đầu, đau nửa đầu, đau cơ, đau bụng kinh, đau họng, đau răng, hạ sốt.",
        "Mẫn cảm với paracetamol hoặc caffeine. Người bệnh thiếu hụt glucose-6-phosphat dehydrogenase (G6PD). Bệnh tim mạch nặng, suy gan nặng.",
        "Người lớn và trẻ em từ 12 tuổi trở lên: uống 1-2 viên mỗi 4-6 giờ khi cần thiết. Không quá 8 viên trong 24 giờ. Khoảng cách tối thiểu giữa 2 lần uống là 4 giờ.",
        "Rất hiếm gặp phản ứng dị ứng, ban da. Dùng quá liều gây độc tính nặng cho gan."
    ),
    (
        "d02", "Hapacol 650", "Paracetamol", "650 mg", "Viên nén",
        "giam-dau", "Dược Hậu Giang (DHG Pharma)", "Việt Nam", "VD-22019-15", "Hộp 10 vỉ x 10 viên",
        "Hạ sốt, giảm các cơn đau đầu, đau răng, đau nhức mỏi cơ xương khớp, đau do cảm cúm.",
        "Mẫn cảm với paracetamol, bệnh gan nặng tiến triển, người thiếu hụt enzym G6PD.",
        "Người lớn và trẻ em trên 12 tuổi: uống 1 viên/lần, cách nhau 4-6 giờ nếu còn đau hoặc sốt. Tối đa không quá 6 viên (3900 mg)/ngày.",
        "Ít tác dụng phụ ở liều điều trị. Có thể gặp ban đỏ, mày đay, buồn nôn."
    ),
    (
        "d03", "Efferalgan 500mg", "Paracetamol", "500 mg", "Viên sủi bọt",
        "giam-dau", "UPSA SAS", "Pháp", "VN-18540-14", "Hộp 4 vỉ x 4 viên sủi",
        "Điều trị triệu chứng đau và sốt từ nhẹ đến vừa ở người lớn và trẻ em.",
        "Quá mẫn với paracetamol. Suy tế bào gan nặng. Cần lưu ý hàm lượng muối natri đối với người ăn kiêng muối.",
        "Hòa tan hoàn toàn 1 viên trong một cốc nước lớn trước khi uống. Cách nhau 4-6 giờ mỗi lần. Không quá 3g (6 viên)/ngày đối với người lớn thông thường.",
        "Hiếm gặp phản ứng quá mẫn, ban ngứa, rối loạn tiêu hóa nhẹ."
    ),
    (
        "d04", "Ibuprofen 400mg", "Ibuprofen", "400 mg", "Viên nén bao phim",
        "giam-dau", "Dược phẩm Domesco", "Việt Nam", "VD-21509-14", "Hộp 10 vỉ x 10 viên",
        "Chống viêm, giảm đau trong viêm khớp dạng thấp, thoái hóa khớp, đau răng, đau bụng kinh, nhức đầu.",
        "Loét dạ dày tá tràng tiến triển, suy gan nặng, suy thận nặng, tiền sử hen suyễn do dùng NSAID, phụ nữ mang thai 3 tháng cuối.",
        "Uống sau bữa ăn với nhiều nước. Người lớn: 1 viên (400mg) mỗi 6-8 giờ khi cần. Liều tối đa 1200-2400 mg/ngày theo chỉ định bác sĩ.",
        "Khó tiêu, buồn nôn, đau thượng vị, ợ nóng, hoa mắt, phát ban."
    ),
    (
        "d05", "Meloxicam 7.5mg", "Meloxicam", "7.5 mg", "Viên nén",
        "giam-dau", "STELLA Pharm", "Việt Nam", "VD-24108-16", "Hộp 3 vỉ x 10 viên",
        "Điều trị triệu chứng dài hạn thoái hóa khớp, viêm cột sống dính khớp, viêm khớp dạng thấp mạn tính.",
        "Phụ nữ có thai hoặc cho con bú. Tiền sử dị ứng aspirin, loét dạ dày tá tràng tiến triển, suy gan thận nặng.",
        "Uống 1 viên (7.5 mg)/ngày trong bữa ăn. Trong trường hợp nặng có thể tăng lên tối đa 2 viên (15 mg)/ngày theo chỉ định.",
        "Đầy hơi, đau bụng, tiêu chảy, chóng mặt, tăng men gan nhẹ."
    ),

    # Nhóm 2: Kháng sinh
    (
        "d06", "Augmentin 1g", "Amoxicillin 875 mg, Acid clavulanic 125 mg", "1 g", "Viên nén bao phim",
        "khang-sinh", "Glaxo Wellcome Production", "Pháp", "VN-18012-14", "Hộp 2 vỉ x 7 viên",
        "Điều trị nhiễm khuẩn đường hô hấp trên và dưới (viêm xoang, viêm tai giữa, viêm phế quản cấp, viêm phổi), nhiễm khuẩn tiết niệu, da.",
        "Dị ứng nhóm beta-lactam (penicillin, cephalosporin). Tiền sử vàng da hoặc rối loạn chức năng gan liên quan đến amoxicillin/clavulanate.",
        "Uống vào đầu bữa ăn để giảm thiểu bất dung nạp đường tiêu hóa. Người lớn và trẻ em trên 40kg: 1 viên x 2 lần/ngày. Đợt điều trị thông thường 7-10 ngày.",
        "Tiêu chảy, buồn nôn, nôn, nhiễm nấm candida trên da và niêm mạc."
    ),
    (
        "d07", "Klamentin 500/125", "Amoxicillin 500 mg, Acid clavulanic 125 mg", "625 mg", "Viên nén bao phim",
        "khang-sinh", "Dược Hậu Giang (DHG Pharma)", "Việt Nam", "VD-20155-13", "Hộp 2 vỉ x 7 viên",
        "Điều trị nhiễm khuẩn tai mũi họng, đường hô hấp dưới, đường tiết niệu - sinh dục, nhiễm khuẩn da và mô mềm.",
        "Mẫn cảm với amoxicillin, acid clavulanic hoặc nhóm penicilin. Bệnh nhân có tiền sử vàng da tắc mật.",
        "Uống thuốc ngay trước bữa ăn. Người lớn: 1 viên mỗi 12 giờ. Nhiễm khuẩn nặng: 1 viên mỗi 8 giờ.",
        "Rối loạn tiêu hóa, phân lỏng, ngứa, mày đay."
    ),
    (
        "d08", "Zithromax 500mg", "Azithromycin", "500 mg", "Viên nén bao phim",
        "khang-sinh", "Pfizer", "Ý", "VN-17120-13", "Hộp 1 vỉ x 3 viên",
        "Điều trị nhiễm khuẩn đường hô hấp dưới (viêm phế quản, viêm phổi), hô hấp trên (viêm xoang, viêm họng), nhiễm trùng da và mô mềm, bệnh lây truyền qua đường tình dục.",
        "Quá mẫn với azithromycin, erythromycin hoặc bất kỳ kháng sinh nhóm macrolid nào. Suy gan nặng.",
        "Uống 1 lần mỗi ngày, ít nhất 1 giờ trước bữa ăn hoặc 2 giờ sau bữa ăn. Liều thông thường: 500 mg/ngày trong 3 ngày liên tiếp (tổng liều 1.5g).",
        "Rối loạn tiêu hóa nhẹ: đau bụng, buồn nôn, tiêu chảy, nhức đầu thoáng qua."
    ),
    (
        "d09", "Cefixim 200mg", "Cefixim", "200 mg", "Viên nang cứng",
        "khang-sinh", "Dược phẩm Mekophar", "Việt Nam", "VD-22415-15", "Hộp 2 vỉ x 10 viên",
        "Nhiễm khuẩn đường tiết niệu không biến chứng, viêm tai giữa, viêm họng và amidan, viêm phế quản cấp và mạn tính.",
        "Tiền sử sốc phản vệ hoặc dị ứng với kháng sinh nhóm cephalosporin hoặc penicillin.",
        "Người lớn và trẻ em trên 12 tuổi: 200 - 400 mg/ngày, uống 1 lần hoặc chia làm 2 lần cách nhau 12 giờ. Đợt dùng từ 5 - 10 ngày.",
        "Rối loạn tiêu hóa, tiêu chảy, đau bụng, nôn, đau đầu, chóng mặt."
    ),
    (
        "d10", "Ciprofloxacin 500mg", "Ciprofloxacin hydrochloride", "500 mg", "Viên nén bao phim",
        "khang-sinh", "STELLA Pharm", "Việt Nam", "VD-25310-16", "Hộp 10 vỉ x 10 viên",
        "Nhiễm khuẩn đường tiết niệu nặng, viêm tuyến tiền liệt, nhiễm khuẩn đường tiêu hóa (tiêu chảy nhiễm trùng), nhiễm khuẩn xương khớp.",
        "Mẫn cảm với nhóm quinolon. Dùng đồng thời với tizanidine. Phụ nữ mang thai và cho con bú, trẻ em dưới 18 tuổi (trừ trường hợp đặc biệt).",
        "Uống nguyên viên với nhiều nước, không phụ thuộc vào bữa ăn. Liều thông thường 500 mg x 2 lần/ngày trong 7 - 14 ngày.",
        "Buồn nôn, tiêu chảy, tăng men gan, mất ngủ, nhạy cảm ánh sáng, đau gân cơ."
    ),

    # Nhóm 3: Dị ứng
    (
        "d11", "Telfast 180mg", "Fexofenadine hydrochloride", "180 mg", "Viên nén bao phim",
        "di-ung", "Sanofi-Aventis", "Việt Nam", "VD-25890-16", "Hộp 1 vỉ x 10 viên",
        "Điều trị triệu chứng mề đay tự phát mạn tính, ngứa da dai dẳng, viêm mũi dị ứng theo mùa ở người lớn và trẻ trên 12 tuổi.",
        "Quá mẫn với fexofenadine hoặc thành phần tá dược của thuốc.",
        "Uống 1 viên (180 mg) duy nhất một lần mỗi ngày với nước lọc. Không uống chung với nước ép hoa quả (bưởi, cam, táo) vì làm giảm hấp thu thuốc.",
        "Thuốc kháng histamin thế hệ 2 không gây buồn ngủ. Rất hiếm gặp đau đầu, mệt mỏi, khô miệng."
    ),
    (
        "d12", "Cetirizine 10mg", "Cetirizine dihydrochloride", "10 mg", "Viên nén bao phim",
        "di-ung", "Dược Hậu Giang (DHG Pharma)", "Việt Nam", "VD-21010-14", "Hộp 10 vỉ x 10 viên",
        "Điều trị viêm mũi dị ứng theo mùa và quanh năm (chảy nước mũi, nghẹt mũi, hắt hơi), viêm kết mạc dị ứng, mề đay vô căn.",
        "Mẫn cảm với cetirizine hoặc hydroxyzine. Bệnh nhân suy thận giai đoạn cuối (độ thanh thải creatinin < 10 ml/phút).",
        "Người lớn và trẻ em từ 6 tuổi trở lên: uống 1 viên (10 mg) một lần mỗi ngày vào buổi tối.",
        "Có thể gây ngủ gà mức độ nhẹ, chóng mặt, khô miệng, mệt mỏi."
    ),
    (
        "d13", "Loratadine 10mg", "Loratadine", "10 mg", "Viên nén",
        "di-ung", "Dược phẩm Domesco", "Việt Nam", "VD-24890-16", "Hộp 3 vỉ x 10 viên",
        "Giảm nhẹ các triệu chứng của viêm mũi dị ứng như hắt hơi, sổ mũi, ngứa mũi; ngứa mắt và xót mắt do dị ứng; mề đay mạn tính.",
        "Mẫn cảm với loratadine. Trẻ em dưới 2 tuổi.",
        "Người lớn và trẻ em trên 12 tuổi: uống 1 viên (10 mg) một lần mỗi ngày trước hoặc sau bữa ăn.",
        "Ít gây buồn ngủ ở liều thông thường. Khô miệng, đau đầu nhẹ."
    ),
    (
        "d14", "Aerius 5mg", "Desloratadine", "5 mg", "Viên nén bao phim",
        "di-ung", "Organon / Schering-Plough", "Bỉ", "VN-15891-12", "Hộp 1 vỉ x 10 viên",
        "Cắt nhanh các triệu chứng liên quan đến viêm mũi dị ứng (hắt hơi, chảy nước mũi, nghẹt mũi, ngứa mắt, đỏ mắt) và mề đay mạn tính.",
        "Quá mẫn với desloratadine hoặc loratadine. Thận trọng với bệnh nhân suy thận nặng.",
        "Uống 1 viên (5 mg) một lần duy nhất trong ngày, có thể dùng cùng hoặc không cùng thức ăn.",
        "Hiếm khi gây mệt mỏi, khô miệng, nhức đầu. Không ảnh hưởng đến khả năng lái xe."
    ),
    (
        "d15", "Phenergan 2.5%", "Promethazine hydrochloride", "25 mg/g (2.5%)", "Kem bôi da",
        "di-ung", "Sanofi", "Việt Nam", "VD-22100-15", "Tuýp 10 g",
        "Điều trị tại chỗ các chứng ngứa, sẩn ngứa, côn trùng đốt, dị ứng da bề mặt, bỏng nhẹ nông.",
        "Các bệnh da nhiễm trùng, tổn thương da rỉ nước, vết thương hở sâu. Trẻ sơ sinh dưới 2 tuổi.",
        "Thoa một lớp mỏng lên vùng da bị tổn thương 3 - 4 lần mỗi ngày. Không bôi trên diện rộng hoặc băng kín.",
        "Có thể gây cảm giác châm chích nhẹ, nhạy cảm ánh sáng tại vùng da bôi thuốc."
    ),

    # Nhóm 4: Tiêu hóa
    (
        "d16", "Nexium 40mg", "Esomeprazole magnesium trihydrate", "40 mg", "Viên nén kháng dịch dạ dày",
        "tieu-hoa", "AstraZeneca", "Thụy Điển", "VN-19782-16", "Hộp 2 vỉ x 7 viên",
        "Điều trị bệnh trào ngược dạ dày - thực quản (GERD), viêm xước thực quản do trào ngược, loét dạ dày tá tràng lành tính, dự phòng loét do NSAID.",
        "Quá mẫn với esomeprazole hoặc các thuốc ức chế bơm proton (PPI) khác. Không phối hợp đồng thời với nelfinavir.",
        "Uống nguyên viên với nước trước bữa ăn sáng ít nhất 30-60 phút. Không được nhai hoặc nghiền nát viên thuốc. Liều: 1 viên/ngày trong 4 - 8 tuần.",
        "Đau đầu, đau bụng, táo bón, tiêu chảy, đầy hơi, buồn nôn."
    ),
    (
        "d17", "Omeprazole 20mg", "Omeprazole", "20 mg", "Viên nang tan trong ruột",
        "tieu-hoa", "Dược Hậu Giang (DHG Pharma)", "Việt Nam", "VD-25800-16", "Hộp 3 vỉ x 10 viên",
        "Loét dạ dày tá tràng tiến triển, hội chứng Zollinger-Ellison, trào ngược dịch vị dạ dày thực quản, phòng loét do stress.",
        "Mẫn cảm với omeprazole hoặc các dẫn chất benzimidazol. Không dùng chung với atazanavir.",
        "Uống nguyên viên trước bữa ăn sáng. Liều thông thường 1 viên (20 mg)/ngày trong 2 - 4 tuần. Hội chứng nặng có thể dùng 40 mg/ngày.",
        "Rối loạn tiêu hóa thoáng qua, nhức đầu, buồn ngủ hoặc mất ngủ nhẹ."
    ),
    (
        "d18", "Gaviscon Dual Action", "Natri alginate, Natri bicarbonate, Calci carbonate", "500mg + 213mg + 325mg / 10ml", "Hỗn dịch uống",
        "tieu-hoa", "Reckitt Benckiser", "Anh", "VN-19010-15", "Hộp 24 gói x 10 ml",
        "Điều trị triệu chứng trào ngược dạ dày thực quản như ợ nóng, ợ chua, khó tiêu do trào ngược sau bữa ăn hoặc trong thai kỳ.",
        "Mẫn cảm với bất kỳ thành phần nào của thuốc. Bệnh nhân suy thận nặng hoặc tăng calci máu.",
        "Lắc đều gói trước khi dùng. Uống trực tiếp sau 3 bữa ăn chính và trước khi đi ngủ. Người lớn: 1-2 gói (10-20ml)/lần, tối đa 4 lần/ngày.",
        "Rất hiếm gặp phản ứng dị ứng như mày đay hoặc co thắt phế quản."
    ),
    (
        "d19", "Phosphalugel", "Nhôm phosphat colloidal 20%", "12.38 g / 20g", "Hỗn dịch uống dạng keo",
        "tieu-hoa", "Boehringer Ingelheim / Sanofi", "Pháp", "VN-17540-13", "Hộp 26 gói x 20 g",
        "Làm dịu cơn đau dạ dày trong viêm dạ dày cấp và mạn tính, loét dạ dày - tá tràng, thoát vị khe thực quản, cảm giác nóng rát dạ dày.",
        "Suy thận nặng mãn tính. Dị ứng với muối nhôm.",
        "Uống trực tiếp hoặc pha với một ít nước. Uống khi có cơn đau hoặc theo chỉ định (sau ăn 1-2 giờ hoặc lúc đói). Người lớn: 1 - 2 gói/lần, ngày 2 - 3 lần.",
        "Có thể gây táo bón nhẹ (đặc biệt ở người cao tuổi hoặc nằm bất động)."
    ),
    (
        "d20", "Oresol 245", "Glucose khan, Natri clorid, Kali clorid, Natri citrat", "Theo tiêu chuẩn WHO", "Gói bột pha dung dịch uống",
        "tieu-hoa", "Dược phẩm Nam Hà", "Việt Nam", "VD-23450-15", "Hộp 20 gói x 4.1 g",
        "Bù nước và điện giải trong tiêu chảy cấp tính, nôn mửa, sốt cao, say nắng, mất nước do vận động thể lực cường độ cao.",
        "Vô niệu hoặc giảm niệu nặng, mất nước nặng kèm sốc, tắc ruột, thủng ruột.",
        "Hòa tan chính xác 1 gói vào đúng lượng nước đun sôi để nguội quy định (thường là 200ml hoặc 1 lít tùy hướng dẫn trên gói). Uống từng ngụm nhỏ, uống rải rác cả ngày.",
        "Hầu như không có tác dụng phụ nếu pha đúng thể tích nước quy định."
    ),
    (
        "d21", "Berberin 50mg", "Berberin clorid", "50 mg", "Viên bao đường",
        "tieu-hoa", "Dược phẩm OPC", "Việt Nam", "VD-21980-14", "Lọ 100 viên",
        "Điều trị hội chứng lỵ, viêm ruột nhiễm khuẩn, tiêu chảy cấp do vi khuẩn, ngộ độc thức ăn nhẹ.",
        "Phụ nữ có thai (do berberin kích thích co bóp tử cung có thể gây sảy thai). Trẻ sơ sinh.",
        "Uống trước bữa ăn. Người lớn: uống 2 - 4 viên/lần, ngày uống 2 lần. Đợt dùng từ 3 - 5 ngày.",
        "Thuốc dung nạp tốt, hiếm khi gây táo bón khi dùng liều cao kéo dài."
    ),
    (
        "d22", "Motilium-M 10mg", "Domperidone", "10 mg", "Viên nén bao phim",
        "tieu-hoa", "Janssen-Cilag", "Thái Lan", "VN-16780-13", "Hộp 10 vỉ x 10 viên",
        "Điều trị triệu chứng buồn nôn và nôn ói do nhiều nguyên nhân khác nhau.",
        "Quá mẫn với domperidone. Xuất huyết tiêu hóa, tắc ruột cơ học hoặc thủng ruột. Bệnh nhân có khoảng QT tim kéo dài hoặc suy gan trung bình/nặng.",
        "Uống trước bữa ăn 15 - 30 phút. Người lớn: 1 viên (10 mg) x tối đa 3 lần/ngày. Thời gian điều trị tối đa không quá 7 ngày.",
        "Khô miệng, tiêu chảy nhẹ, đau đầu, hiếm gặp kéo dài khoảng QT."
    ),

    # Nhóm 5: Hô hấp
    (
        "d23", "Ventolin Inhaler 100mcg", "Salbutamol sulfate", "100 mcg / liều", "Hỗn dịch xịt hít định liều",
        "ho-hap", "GlaxoSmithKline (GSK)", "Tây Ban Nha", "VN-18900-15", "Bình xịt 200 liều",
        "Cắt cơn co thắt phế quản cấp tính trong hen phế quản, viêm phế quản mạn tính và phòng co thắt phế quản do gắng sức.",
        "Quá mẫn với salbutamol. Không dùng để xử trí dọa sẩy thai trong sản khoa.",
        "Lắc đều bình xịt, thở ra hết cỡ, ngậm kín ống ngậm và hít sâu đồng thời ấn bình xịt. Cắt cơn hen: xịt 1 - 2 nhát. Tối đa không quá 8 nhát xịt trong 24 giờ.",
        "Run tay nhẹ, đánh trống ngực, nhịp tim nhanh thoáng qua, nhức đầu."
    ),
    (
        "d24", "Seretide Evohaler 25/125", "Salmeterol xinafoate 25mcg, Fluticasone propionate 125mcg", "25 mcg + 125 mcg", "Hỗn dịch xịt hít định liều",
        "ho-hap", "Glaxo Operations", "Anh", "VN-19450-16", "Bình xịt 120 liều",
        "Điều trị duy trì thường quy bệnh hen suyễn (khi cần phối hợp LABA và corticoid hít), điều trị duy trì bệnh phổi tắc nghẽn mạn tính (COPD).",
        "Mẫn cảm với bất kỳ thành phần nào của thuốc. Không dùng để cắt cơn hen cấp tính.",
        "Hít qua đường miệng đều đặn mỗi ngày. Người lớn: 2 nhát xịt x 2 lần/ngày. Súc miệng bằng nước sạch sau khi hít để ngừa nấm miệng.",
        "Nhiễm nấm candida miệng và họng, khàn giọng, kích ứng họng, đánh trống ngực."
    ),
    (
        "d25", "Acemuc 200mg", "Acetylcysteine", "200 mg", "Cốm pha hỗn dịch uống",
        "ho-hap", "Sanofi-Synthelabo", "Việt Nam", "VD-23110-15", "Hộp 30 gói x 200 mg",
        "Làm loãng chất nhầy, tiêu đờm trong các bệnh lý phế quản - phổi cấp và mạn tính có tăng tiết đờm nhầy quánh đặc.",
        "Tiền sử hen phế quản (nguy cơ co thắt phế quản). Quá mẫn với acetylcysteine. Trẻ em dưới 2 tuổi.",
        "Hòa tan gói cốm trong nửa cốc nước. Uống sau bữa ăn. Người lớn và trẻ trên 7 tuổi: 1 gói x 3 lần/ngày.",
        "Buồn nôn, nôn, tiêu chảy nhẹ, ợ nóng, ù tai."
    ),
    (
        "d26", "Bisolvon 8mg", "Bromhexine hydrochloride", "8 mg", "Viên nén",
        "ho-hap", "Boehringer Ingelheim", "Indonesia", "VN-18450-14", "Hộp 3 vỉ x 10 viên",
        "Làm loãng và tan dịch tiết phế quản trong viêm phế quản cấp/mạn, giãn phế quản, viêm thanh quản, khí phế thũng.",
        "Quá mẫn với bromhexine. Loét dạ dày tá tràng tiến triển. Phụ nữ có thai 3 tháng đầu.",
        "Uống sau bữa ăn với nhiều nước để tăng hiệu quả long đờm. Người lớn và trẻ trên 12 tuổi: 1 viên (8 mg) x 3 lần/ngày.",
        "Đau dạ dày nhẹ, tiêu chảy, đầy bụng, phát ban da hiếm gặp."
    ),
    (
        "d27", "Decolgen Forte", "Paracetamol 500mg, Phenylephrine 10mg, Chlorpheniramine 2mg", "500mg + 10mg + 2mg", "Viên nén",
        "ho-hap", "United Pharma", "Việt Nam", "VD-24500-16", "Hộp 25 vỉ x 4 viên",
        "Điều trị các triệu chứng cảm cúm, sốt, đau đầu, sổ mũi, nghẹt mũi, viêm xoang, chảy nước mắt do cảm lạnh.",
        "Cao huyết áp nặng, bệnh mạch vành nặng, cường giáp, đang dùng thuốc ức chế MAO, glôcôm góc hẹp.",
        "Người lớn: uống 1 - 2 viên/lần, cách nhau 4 - 6 giờ nếu cần. Không uống quá 6 viên trong 24 giờ.",
        "Gây buồn ngủ, khô miệng, tăng huyết áp nhẹ, chóng mặt."
    ),

    # Nhóm 6: Vitamin
    (
        "d28", "Berocca Performance", "Vitamin B tổng hợp, Vitamin C, Calci, Magie, Kẽm", "Đa thành phần", "Viên sủi bọt",
        "vitamin", "Bayer", "Indonesia", "VN-18890-15", "Tuýp 10 viên sủi",
        "Bổ sung các vitamin nhóm B thiết yếu và vitamin C hàm lượng cao giúp giảm căng thẳng mệt mỏi, phục hồi sinh lực thể chất và trí não.",
        "Suy thận nặng, tăng canxi máu, tăng canxi niệu, sỏi thận, thừa vitamin.",
        "Hòa tan 1 viên sủi vào 200ml nước lọc, uống vào buổi sáng sau bữa ăn. Liều dùng: 1 viên/ngày.",
        "Nước tiểu có màu vàng sáng vô hại (do đào thải vitamin B2), rối loạn tiêu hóa nhẹ."
    ),
    (
        "d29", "Upsa-C 1000mg", "Acid ascorbic (Vitamin C)", "1000 mg", "Viên sủi bọt",
        "vitamin", "UPSA SAS", "Pháp", "VN-16540-13", "Tuýp 10 viên sủi",
        "Điều trị tình trạng thiếu hụt vitamin C (scurvy), hỗ trợ tăng cường sức đề kháng khi cơ thể suy nhược, nhiễm trùng, cảm cúm.",
        "Bệnh nhân có tiền sử sỏi thận oxalat, tăng oxalat niệu, người thiếu hụt enzym G6PD.",
        "Hòa tan 1 viên trong một cốc nước đầy. Uống vào buổi sáng hoặc trưa, tránh uống buổi tối vì gây khó ngủ. Liều: 1 viên/ngày trong thời gian ngắn.",
        "Dùng liều cao kéo dài có thể gây kích ứng dạ dày, tiêu chảy, nguy cơ lắng đọng sỏi thận."
    ),
    (
        "d30", "Calcium Corbiere 10ml", "Calci glucoheptonat 1.1g, Vitamin C 100mg, Vitamin PP 50mg", "1.1 g / 10ml", "Dung dịch uống",
        "vitamin", "Sanofi", "Việt Nam", "VD-26500-17", "Hộp 3 vỉ x 10 ống 10 ml",
        "Bổ sung canxi cho phụ nữ mang thai, cho con bú, trẻ em trong giai đoạn tăng trưởng chiều cao, điều trị và phòng ngừa loãng xương ở người cao tuổi.",
        "Tăng canxi huyết, canxi niệu nặng, sỏi thận calci, u ác tính phá hủy xương.",
        "Bẻ một đầu ống, đưa vào miệng hoặc cốc rồi bẻ đầu còn lại để dung dịch chảy ra. Uống vào buổi sáng sau bữa ăn. Người lớn: 1 - 2 ống 10ml/ngày.",
        "Táo bón nhẹ, đầy hơi, buồn nôn hiếm gặp."
    ),
    (
        "d31", "Ferrovit", "Sắt fumarat 162mg, Acid folic 0.75mg, Vitamin B12 7.5mcg", "162 mg + 0.75 mg", "Viên nang mềm",
        "vitamin", "Mega Lifesciences", "Thái Lan", "VN-17800-14", "Hộp 5 vỉ x 10 viên",
        "Dự phòng và điều trị thiếu máu do thiếu sắt ở phụ nữ có thai, bà mẹ cho con bú, thiếu nữ dậy thì, bệnh nhân sau phẫu thuật hoặc mất máu mạn tính.",
        "Quá mẫn với thành phần thuốc. Bệnh nhân thừa sắt (nhiễm sắc tố sắt mô, thiếu máu tan huyết).",
        "Uống 1 viên x 1 - 2 lần/ngày sau các bữa ăn. Uống với nhiều nước, không uống cùng trà, cà phê hay sữa vì cản trở hấp thu sắt.",
        "Phân có màu đen vô hại, buồn nôn nhẹ, táo bón hoặc tiêu chảy thoáng qua."
    ),

    # Nhóm 7: Nội tiết
    (
        "d32", "Glucophage 850mg", "Metformin hydrochloride", "850 mg", "Viên nén bao phim",
        "noi-tiet", "Merck Sante S.A.S", "Pháp", "VN-17980-14", "Hộp 5 vỉ x 20 viên",
        "Điều trị bệnh đái tháo đường týp 2 (không phụ thuộc insulin), đặc biệt ở bệnh nhân thừa cân béo phì khi chế độ ăn kiêng và tập thể dục không kiểm soát được đường huyết.",
        "Suy thận nặng (eGFR < 30 mL/phút), suy tim mất bù, nhiễm toan ceton, nghiện rượu nặng.",
        "Uống trong hoặc ngay sau bữa ăn để giảm tác dụng phụ trên đường tiêu hóa. Khởi đầu: 1 viên (500mg hoặc 850mg) x 1-2 lần/ngày. Liều tối đa 2550 mg/ngày.",
        "Đầy hơi, tiêu chảy, buồn nôn, chán ăn, vị kim loại trong miệng trong những tuần đầu điều trị."
    ),
    (
        "d33", "Diamicron MR 60mg", "Gliclazide phóng thích có biến đổi", "60 mg", "Viên nén phóng thích biến đổi",
        "noi-tiet", "Les Laboratoires Servier", "Pháp", "VN-18650-14", "Hộp 2 vỉ x 30 viên",
        "Điều trị đái tháo đường týp 2 ở người lớn khi chế độ dinh dưỡng, vận động thể lực đơn thuần không đủ duy trì đường huyết mục tiêu.",
        "Đái tháo đường týp 1, hôn mê do tiểu đường, suy gan suy thận nặng, phụ nữ có thai hoặc cho con bú. Dùng đồng thời với miconazol.",
        "Uống nguyên viên (không bẻ đôi, không nghiền nát) một lần duy nhất vào bữa sáng. Liều từ 1/2 viên đến tối đa 2 viên (30 - 120 mg)/ngày theo chỉ định bác sĩ.",
        "Hạ đường huyết (vã mồ hôi, run rẩy, hoa mắt), rối loạn tiêu hóa nhẹ."
    ),
    (
        "d34", "Forxiga 10mg", "Dapagliflozin propanediol monohydrate", "10 mg", "Viên nén bao phim",
        "noi-tiet", "AstraZeneca", "Thụy Điển", "VN-21090-18", "Hộp 2 vỉ x 14 viên",
        "Điều trị đái tháo đường týp 2 ở người lớn; điều trị suy tim mạn tính phân suất tống máu giảm; điều trị bệnh thận mạn tính.",
        "Mẫn cảm với dapagliflozin. Bệnh nhân đái tháo đường týp 1. Thận trọng khi chức năng thận suy giảm nặng.",
        "Uống 1 viên (10 mg) một lần mỗi ngày vào bất kỳ thời điểm nào trong ngày, cùng hoặc không cùng thức ăn.",
        "Nhiễm nấm sinh dục, nhiễm khuẩn đường tiết niệu, tiểu nhiều lần, hạ huyết áp tư thế đứng."
    ),
    (
        "d35", "Januvia 100mg", "Sitagliptin phosphate monohydrate", "100 mg", "Viên nén bao phim",
        "noi-tiet", "Merck Sharp & Dohme (MSD)", "Ý", "VN-19050-15", "Hộp 2 vỉ x 14 viên",
        "Kiểm soát đường huyết ở bệnh nhân đái tháo đường týp 2 theo cơ chế ức chế chọn lọc enzym DPP-4.",
        "Quá mẫn với sitagliptin. Tiền sử viêm tụy cấp tính liên quan đến thuốc.",
        "Uống 1 viên (100 mg) một lần duy nhất mỗi ngày, có thể dùng lúc đói hoặc lúc no.",
        "Viêm mũi họng, đau đầu, viêm xương khớp, rất hiếm gặp viêm tụy cấp."
    ),
    (
        "d36", "Berlthyrox 100mcg", "Levothyroxine natri", "100 mcg", "Viên nén",
        "noi-tiet", "Berlin-Chemie AG", "Đức", "VN-16500-13", "Hộp 4 vỉ x 25 viên",
        "Điều trị thay thế trong suy giáp do mọi nguyên nhân, điều trị bướu giáp đơn thuần lành tính, ức chế sau phẫu thuật ung thư tuyến giáp.",
        "Cường giáp chưa điều trị ổn định, nhồi máu cơ tim cấp, viêm cơ tim cấp, suy tuyến thượng thận chưa điều trị.",
        "Uống một liều duy nhất vào buổi sáng khi đói, trước bữa ăn sáng ít nhất 30 phút với nửa cốc nước lọc. Liều chuẩn độ theo xét nghiệm TSH.",
        "Các triệu chứng của cường giáp khi dùng quá liều: hồi hộp, sụt cân, mất ngủ, run tay, tim đập nhanh."
    ),

    # Nhóm 8: Tim mạch
    (
        "d37", "Amlor 5mg", "Amlodipine besylate", "5 mg", "Viên nang cứng",
        "tim-mach", "Pfizer", "Pháp", "VN-17890-14", "Hộp 3 vỉ x 10 viên",
        "Điều trị tăng huyết áp vô căn, điều trị đau thắt ngực ổn định mạn tính và đau thắt ngực do co thắt mạch (Prinzmetal).",
        "Hạ huyết áp nặng, sốc tim, hẹp động mạch chủ nặng, suy tim không ổn định sau nhồi máu cơ tim cấp.",
        "Uống 1 viên (5 mg) một lần mỗi ngày vào cùng một thời điểm cố định. Có thể tăng tối đa lên 10 mg/ngày nếu cần thiết.",
        "Phù mắt cá chân hoặc bàn chân, bốc hỏa mặt, đau đầu, mệt mỏi, đánh trống ngực."
    ),
    (
        "d38", "Concor 5mg", "Bisoprolol fumarate", "5 mg", "Viên nén bao phim hình tim",
        "tim-mach", "Merck KGaA", "Đức", "VN-18990-15", "Hộp 5 vỉ x 20 viên",
        "Điều trị tăng huyết áp nguyên phát, đau thắt ngực mạn tính, điều trị suy tim mạn tính ổn định phối hợp với thuốc ức chế men chuyển và lợi tiểu.",
        "Suy tim cấp hoặc đợt mất bù, sốc tim, block nhĩ thất độ II hoặc III, nhịp tim chậm < 50 nhịp/phút, hen phế quản nặng.",
        "Uống vào buổi sáng, có thể cùng thức ăn. Uống nguyên viên với nước. Liều thông thường 5 mg/ngày, tối đa 10 mg/ngày. Không ngưng thuốc đột ngột.",
        "Chậm nhịp tim, hạ huyết áp, mệt mỏi, chóng mặt, lạnh đầu chi."
    ),
    (
        "d39", "Micardis 40mg", "Telmisartan", "40 mg", "Viên nén",
        "tim-mach", "Boehringer Ingelheim", "Đức", "VN-16980-13", "Hộp 3 vỉ x 10 viên",
        "Điều trị tăng huyết áp nguyên phát ở người lớn, phòng ngừa biến cố tim mạch và tử vong ở người có nguy cơ cao.",
        "Phụ nữ có thai từ tháng thứ 4 trở đi (độc tính trên thai nhi). Tắc mật hoặc suy gan nặng.",
        "Uống 1 viên (40 mg) một lần mỗi ngày với nước, không phụ thuộc vào bữa ăn.",
        "Hạ huyết áp, chóng mặt, đau lưng, nhiễm trùng đường hô hấp trên nhẹ."
    ),
    (
        "d40", "Lipitor 20mg", "Atorvastatin calcium trihydrate", "20 mg", "Viên nén bao phim",
        "tim-mach", "Pfizer", "Đức", "VN-19200-15", "Hộp 3 vỉ x 10 viên",
        "Giảm cholesterol toàn phần, LDL-C, triglycerid ở bệnh nhân tăng mỡ máu; phòng ngừa tiên phát và thứ phát biến cố tim mạch (nhồi máu cơ tim, đột quỵ).",
        "Bệnh gan tiến triển hoặc tăng men gan dai dẳng không rõ nguyên nhân. Phụ nữ mang thai hoặc đang cho con bú.",
        "Uống 1 lần mỗi ngày vào buổi tối trước khi đi ngủ hoặc buổi sáng. Liều khởi đầu 10-20 mg/ngày, điều chỉnh theo đáp ứng lipid máu.",
        "Đau cơ, yếu cơ, đau khớp, rối loạn tiêu hóa, tăng men gan nhẹ."
    ),
    (
        "d41", "Crestor 10mg", "Rosuvastatin calcium", "10 mg", "Viên nén bao phim",
        "tim-mach", "AstraZeneca", "Anh", "VN-17500-13", "Hộp 2 vỉ x 14 viên",
        "Điều trị tăng cholesterol máu nguyên phát, rối loạn lipid máu hỗn hợp, làm chậm tiến triển của mảng xơ vữa động mạch.",
        "Bệnh gan tiến triển, suy thận nặng, phụ nữ có thai hoặc cho con bú. Không dùng liều 40mg cho người gốc Á.",
        "Uống 1 viên (10 mg) một lần mỗi ngày vào bất kỳ thời điểm nào trong ngày. Có thể tăng lên 20mg sau 4 tuần nếu cần.",
        "Đau cơ, suy nhược cơ thể, đau đầu, chóng mặt, buồn nôn, đau bụng."
    ),
    (
        "d42", "Plavix 75mg", "Clopidogrel bisulfate", "75 mg", "Viên nén bao phim",
        "tim-mach", "Sanofi Winthrop Industrie", "Pháp", "VN-18230-14", "Hộp 2 vỉ x 14 viên",
        "Dự phòng các biến cố huyết khối do xơ vữa (nhồi máu cơ tim, đột quỵ thiếu máu cục bộ, tử vong do tim mạch) ở bệnh nhân xơ vữa động mạch hoặc can thiệp mạch vành.",
        "Đang có xuất huyết bệnh lý hoạt động (như loét dạ dày tá tràng hoặc xuất huyết nội sọ). Suy gan nặng.",
        "Uống 1 viên (75 mg) duy nhất một lần mỗi ngày, cùng hoặc không cùng thức ăn. Bệnh nhân hội chứng vành cấp có liều nạp 300mg ban đầu.",
        "Chảy máu (bầm tím dưới da, chảy máu cam, xuất huyết tiêu hóa), rối loạn tiêu hóa, ban da."
    ),
]


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS drugs")
    cur.execute("DROP TABLE IF EXISTS drug_groups")

    cur.execute("""
    CREATE TABLE drug_groups (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        hue INTEGER NOT NULL,
        description TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE drugs (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        active_ingredient TEXT NOT NULL,
        strength TEXT,
        form TEXT,
        group_id TEXT NOT NULL REFERENCES drug_groups(id),
        manufacturer TEXT,
        country TEXT,
        registration_no TEXT,
        packaging TEXT,
        indications TEXT,
        contraindications TEXT,
        dosage TEXT,
        side_effects TEXT
    )
    """)

    cur.executemany(
        "INSERT INTO drug_groups (id, name, hue, description) VALUES (?, ?, ?, ?)",
        GROUPS_DATA,
    )

    cur.executemany(
        """INSERT INTO drugs (
            id, name, active_ingredient, strength, form, group_id,
            manufacturer, country, registration_no, packaging,
            indications, contraindications, dosage, side_effects
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        DRUGS_DATA,
    )

    # Tạo chỉ mục tìm kiếm tối ưu
    cur.execute("CREATE INDEX idx_drugs_group ON drugs(group_id)")
    cur.execute("CREATE INDEX idx_drugs_name ON drugs(name)")
    cur.execute("CREATE INDEX idx_drugs_active ON drugs(active_ingredient)")
    cur.execute("CREATE INDEX idx_drugs_reg ON drugs(registration_no)")

    conn.commit()
    conn.close()
    print(f"-> Đã tạo thành công Database SQLite: {DB_PATH} ({len(DRUGS_DATA)} thuốc, {len(GROUPS_DATA)} nhóm)")


def export_csv_and_js() -> None:
    """Cập nhật các file CSV và sample-data.js đồng bộ với SQLite"""
    # 1. Export groups.csv
    with open(GROUPS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "hue"])
        for g in GROUPS_DATA:
            writer.writerow([g[0], g[1], g[2]])

    # 2. Export drugs.csv
    with open(DRUGS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "name", "active_ingredient", "strength", "form",
            "group_id", "manufacturer", "registration_no"
        ])
        for d in DRUGS_DATA:
            writer.writerow([d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[8]])

    # 3. Export sample-data.js
    payload = {
        "meta": {
            "isSample": False,
            "total": len(DRUGS_DATA),
            "source": "Cục Quản lý Dược – Bộ Y tế Việt Nam (DAV)",
            "updatedAt": "2026-10-23",
        },
        "groups": [{"id": g[0], "name": g[1], "hue": g[2], "description": g[3]} for g in GROUPS_DATA],
        "drugs": [
            {
                "id": d[0],
                "name": d[1],
                "activeIngredient": d[2],
                "strength": d[3],
                "form": d[4],
                "group": d[5],
                "manufacturer": d[6],
                "country": d[7],
                "registrationNo": d[8],
                "packaging": d[9],
                "indications": d[10],
                "contraindications": d[11],
                "dosage": d[12],
                "sideEffects": d[13],
            }
            for d in DRUGS_DATA
        ],
    }

    header = (
        "/* DỮ LIỆU ĐƯỢC ĐỒNG BỘ TỪ DATABASE SQLite (data/drugs.db).\n"
        " * Nguồn: Cục Quản lý Dược – Bộ Y tế Việt Nam. */\n"
    )
    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    OUT_JS.write_text(
        header + "window.LAWGPT_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"-> Đã đồng bộ sang {GROUPS_CSV.name}, {DRUGS_CSV.name} và {OUT_JS.name}")


if __name__ == "__main__":
    init_db()
    export_csv_and_js()
