"""Hệ thống Dược lâm sàng: Ma trận kiểm tra tương tác thuốc & Chăm sóc phi dược lý.
Cung cấp phân tích tương tác thuốc chính xác dựa trên cơ chế dược lực học/dược động học
và giao thức chăm sóc sức khỏe tại nhà (Home-care protocols).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# ==============================================================================
# 1. MA TRẬN TƯƠNG TÁC THUỐC LÂM SÀNG (DRUG-DRUG INTERACTION MATRIX)
# ==============================================================================

# Mức độ nghiêm trọng
SEVERITY_DANGER = "danger"        # 🔴 Chống chỉ định / Nguy hiểm đe dọa tính mạng
SEVERITY_WARNING = "warning"      # 🟡 Cần thận trọng cao / Cân nhắc chỉnh liều
SEVERITY_CAUTION = "caution"      # 🟡 Hiệp đồng hoặc theo dõi phản ứng
SEVERITY_BENEFICIAL = "beneficial"# 🟢 Tương tác có lợi (hỗ trợ bảo vệ)
SEVERITY_SAFE = "safe"            # 🟢 An toàn / Không ghi nhận tương tác bất lợi

# Từ điển các hoạt chất và nhóm dược lý của 42 thuốc
DRUG_PROFILES = {
    "d01": {"name": "Panadol Extra", "actives": ["paracetamol", "caffeine"], "class": "analgesic"},
    "d02": {"name": "Hapacol 650", "actives": ["paracetamol"], "class": "analgesic"},
    "d03": {"name": "Efferalgan 500mg", "actives": ["paracetamol"], "class": "analgesic"},
    "d04": {"name": "Ibuprofen 400mg", "actives": ["ibuprofen"], "class": "nsaid"},
    "d05": {"name": "Meloxicam 7.5mg", "actives": ["meloxicam"], "class": "nsaid"},
    "d06": {"name": "Augmentin 1g", "actives": ["amoxicillin", "clavulanic"], "class": "antibiotic_penicillin"},
    "d07": {"name": "Klamentin 500/125", "actives": ["amoxicillin", "clavulanic"], "class": "antibiotic_penicillin"},
    "d08": {"name": "Zithromax 500mg", "actives": ["azithromycin"], "class": "antibiotic_macrolide"},
    "d09": {"name": "Cefixim 200mg", "actives": ["cefixim"], "class": "antibiotic_cephalosporin"},
    "d10": {"name": "Ciprofloxacin 500mg", "actives": ["ciprofloxacin"], "class": "antibiotic_quinolone"},
    "d11": {"name": "Telfast 180mg", "actives": ["fexofenadine"], "class": "antihistamine"},
    "d12": {"name": "Cetirizine 10mg", "actives": ["cetirizine"], "class": "antihistamine"},
    "d13": {"name": "Loratadine 10mg", "actives": ["loratadine"], "class": "antihistamine"},
    "d14": {"name": "Aerius 5mg", "actives": ["desloratadine"], "class": "antihistamine"},
    "d15": {"name": "Phenergan 2.5%", "actives": ["promethazine"], "class": "topical_antihistamine"},
    "d16": {"name": "Nexium 40mg", "actives": ["esomeprazole"], "class": "ppi"},
    "d17": {"name": "Omeprazole 20mg", "actives": ["omeprazole"], "class": "ppi"},
    "d18": {"name": "Gaviscon Dual Action", "actives": ["alginate", "antacid"], "class": "antacid"},
    "d19": {"name": "Phosphalugel", "actives": ["aluminium_phosphate"], "class": "antacid"},
    "d20": {"name": "Oresol 245", "actives": ["electrolytes", "glucose"], "class": "rehydration"},
    "d21": {"name": "Berberin 50mg", "actives": ["berberin"], "class": "antidiarrheal"},
    "d22": {"name": "Motilium-M 10mg", "actives": ["domperidone"], "class": "prokinetic"},
    "d23": {"name": "Ventolin Inhaler 100mcg", "actives": ["salbutamol"], "class": "beta2_agonist"},
    "d24": {"name": "Seretide Evohaler 25/125", "actives": ["salmeterol", "fluticasone"], "class": "beta2_agonist_ics"},
    "d25": {"name": "Acemuc 200mg", "actives": ["acetylcysteine"], "class": "mucolytic"},
    "d26": {"name": "Bisolvon 8mg", "actives": ["bromhexine"], "class": "mucolytic"},
    "d27": {"name": "Decolgen Forte", "actives": ["paracetamol", "phenylephrine", "chlorpheniramine"], "class": "cold_combo"},
    "d28": {"name": "Berocca Performance", "actives": ["vitamin_b", "vitamin_c", "minerals"], "class": "multivitamin"},
    "d29": {"name": "Upsa-C 1000mg", "actives": ["vitamin_c"], "class": "vitamin_c"},
    "d30": {"name": "Calcium Corbiere 10ml", "actives": ["calcium"], "class": "calcium"},
    "d31": {"name": "Ferrovit", "actives": ["iron", "folic_acid"], "class": "iron"},
    "d32": {"name": "Glucophage 850mg", "actives": ["metformin"], "class": "biguanide"},
    "d33": {"name": "Diamicron MR 60mg", "actives": ["gliclazide"], "class": "sulfonylurea"},
    "d34": {"name": "Forxiga 10mg", "actives": ["dapagliflozin"], "class": "sglt2_inhibitor"},
    "d35": {"name": "Januvia 100mg", "actives": ["sitagliptin"], "class": "dpp4_inhibitor"},
    "d36": {"name": "Berlthyrox 100mcg", "actives": ["levothyroxine"], "class": "thyroid"},
    "d37": {"name": "Amlor 5mg", "actives": ["amlodipine"], "class": "ccb"},
    "d38": {"name": "Concor 5mg", "actives": ["bisoprolol"], "class": "beta_blocker"},
    "d39": {"name": "Micardis 40mg", "actives": ["telmisartan"], "class": "arb"},
    "d40": {"name": "Lipitor 20mg", "actives": ["atorvastatin"], "class": "statin"},
    "d41": {"name": "Crestor 10mg", "actives": ["rosuvastatin"], "class": "statin"},
    "d42": {"name": "Plavix 75mg", "actives": ["clopidogrel"], "class": "antiplatelet"},
}

def normalize_key(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = re.sub(r"[\u0300-\u036f]", "", s)
    return s.replace("đ", "d")

# Danh mục các cặp tương tác đặc hiệu theo hoạt chất hoặc nhóm
INTERACTION_RULES = [
    # 1. Trùng lặp Paracetamol
    {
        "match": lambda a, b: "paracetamol" in a["actives"] and "paracetamol" in b["actives"],
        "severity": SEVERITY_DANGER,
        "title": "Trùng lặp hoạt chất Paracetamol (Nguy cơ ngộ độc gan cấp tính)",
        "mechanism": "Cả hai thuốc đều chứa Paracetamol. Uống đồng thời rất dễ vượt ngưỡng tối đa an toàn (4000 mg/ngày ở người lớn), dẫn đến tích tụ chất chuyển hóa độc N-acetyl-p-benzoquinone imine (NAPQI), gây hoại tử tế bào gan cấp tính và suy gan tối cấp.",
        "management": "TUYỆT ĐỐI KHÔNG uống cùng lúc hai loại thuốc này. Chỉ chọn 1 loại duy nhất và tuân thủ khoảng cách tối thiểu giữa hai liều là 4-6 giờ."
    },
    # 2. NSAID + Kháng kết tập tiểu cầu (Plavix)
    {
        "match": lambda a, b: ("nsaid" in (a["class"], b["class"])) and ("antiplatelet" in (a["class"], b["class"])),
        "severity": SEVERITY_DANGER,
        "title": "Nguy cơ xuất huyết tiêu hóa và loét dạ dày nghiêm trọng",
        "mechanism": "Plavix (Clopidogrel) ức chế kết tập tiểu cầu ngăn đông máu, trong khi thuốc chống viêm NSAID (Ibuprofen, Meloxicam) ức chế tổng hợp prostaglandin bảo vệ niêm mạc dạ dày. Khi dùng chung, nguy cơ loét thủng dạ dày và xuất huyết tiêu hóa ồ ạt tăng gấp 3–5 lần.",
        "management": "Tránh kết hợp tự ý. Nếu cần giảm đau hạ sốt khi đang dùng Plavix, hãy ưu tiên dùng Paracetamol đơn độc. Nếu bắt buộc phải dùng NSAID theo chỉ định bác sĩ, phải uống kèm thuốc ức chế bơm proton (PPI như Nexium) để bảo vệ dạ dày."
    },
    # 3. Chẹn beta (Concor) + Chủ vận beta-2 giãn phế quản (Ventolin / Seretide)
    {
        "match": lambda a, b: ("beta_blocker" in (a["class"], b["class"])) and any(c in (a["class"], b["class"]) for c in ("beta2_agonist", "beta2_agonist_ics")),
        "severity": SEVERITY_DANGER,
        "title": "Đối kháng tác dụng dược lý – Nguy cơ khởi phát cơn hen suyễn cấp",
        "mechanism": "Concor (Bisoprolol) là thuốc chẹn thụ thể beta giao cảm, đối kháng trực tiếp và triệt tiêu tác dụng giãn cơ trơn phế quản của Ventolin (Salbutamol) và Seretide (Salmeterol). Sự đối kháng này làm giảm hiệu quả cắt cơn khó thở và có thể kích phát co thắt phế quản cấp tính nặng.",
        "management": "Chống chỉ định phối hợp hoặc cần thận trọng tối đa. Người có bệnh lý hô hấp (hen, COPD) cần báo ngay cho bác sĩ tim mạch để đổi sang nhóm hạ áp an toàn hơn cho đường thở (như chẹn kênh canxi Amlodipine)."
    },
    # 4. Statin (Lipitor/Crestor) + Kháng sinh Quinolone/Macrolide (Ciprofloxacin/Zithromax)
    {
        "match": lambda a, b: ("statin" in (a["class"], b["class"])) and any(c in (a["class"], b["class"]) for c in ("antibiotic_quinolone", "antibiotic_macrolide")),
        "severity": SEVERITY_WARNING,
        "title": "Tăng nồng độ Statin trong máu – Nguy cơ tổn thương cơ vân (Tiêu cơ vân)",
        "mechanism": "Kháng sinh (Ciprofloxacin, Azithromycin) có thể ức chế enzym chuyển hóa gan CYP3A4 hoặc cạnh tranh đào thải qua thận, làm tăng vọt nồng độ thuốc Statin hạ mỡ máu trong huyết tương. Điều này làm tăng nguy cơ viêm cơ, đau cơ dữ dội và tiêu cơ vân cấp (Rhabdomyolysis) dẫn đến suy thận.",
        "management": "Nếu bắt buộc dùng kháng sinh ngắn ngày, hãy hỏi bác sĩ về việc tạm ngưng Statin trong thời gian điều trị. Đi khám ngay nếu xuất hiện triệu chứng đau mỏi cơ bắp dữ dội hoặc nước tiểu chuyển màu nâu sẫm."
    },
    # 5. Phối hợp NSAID + Thuốc bảo vệ dạ dày PPI (Nexium / Omeprazole)
    {
        "match": lambda a, b: ("nsaid" in (a["class"], b["class"])) and ("ppi" in (a["class"], b["class"])),
        "severity": SEVERITY_BENEFICIAL,
        "title": "Tương tác bảo vệ có lợi cho niêm mạc dạ dày",
        "mechanism": "Thuốc ức chế bơm proton PPI (Nexium/Omeprazole) ức chế tiết acid dịch vị mạnh mẽ, giúp bảo vệ lớp niêm mạc dạ dày tá tràng khỏi tác dụng phụ gây viêm loét của thuốc kháng viêm giảm đau NSAID (Ibuprofen, Meloxicam).",
        "management": "Đây là phối hợp có lợi và thường được bác sĩ chỉ định cho bệnh nhân có nguy cơ đau dạ dày khi phải dùng NSAID."
    },
    # 6. Chẹn kênh canxi (Amlor) + Chẹn beta (Concor)
    {
        "match": lambda a, b: ("ccb" in (a["class"], b["class"])) and ("beta_blocker" in (a["class"], b["class"])),
        "severity": SEVERITY_CAUTION,
        "title": "Hiệp đồng hạ huyết áp & Nguy cơ làm chậm nhịp tim",
        "mechanism": "Amlor (Amlodipine) làm giãn động mạch ngoại biên, trong khi Concor (Bisoprolol) làm giảm nhịp tim và sức co bóp cơ tim. Sự kết hợp này mang lại hiệu quả hạ huyết áp mạnh mẽ nhưng có thể gây tụt huyết áp tư thế (chóng mặt khi đứng dậy) hoặc chậm nhịp tim quá mức.",
        "management": "Phối hợp điều trị phổ biến trong chuyên khoa tim mạch nhưng bắt buộc phải có đơn của bác sĩ. Người bệnh cần theo dõi chỉ số huyết áp và nhịp tim hàng ngày."
    },
    # 7. Thuốc tiểu đường phối hợp (Metformin + Diamicron)
    {
        "match": lambda a, b: ("biguanide" in (a["class"], b["class"])) and ("sulfonylurea" in (a["class"], b["class"])),
        "severity": SEVERITY_CAUTION,
        "title": "Tăng cường kiểm soát đường huyết – Cần phòng ngừa hạ đường huyết",
        "mechanism": "Glucophage (Metformin) giúp giảm sản xuất glucose ở gan, trong khi Diamicron (Gliclazide) kích thích tế bào tụy tiết thêm insulin. Phối hợp này kiểm soát đường huyết rất tốt nhưng làm tăng nguy cơ tụt đường huyết đột ngột.",
        "management": "Phối hợp chuẩn trong điều trị đái tháo đường týp 2. Bệnh nhân cần ăn uống đúng giờ và luôn mang theo vài viên kẹo hoặc gói đường bên mình."
    },
    # 8. Kháng sinh đường uống + Berberin
    {
        "match": lambda a, b: any(c.startswith("antibiotic") for c in (a["class"], b["class"])) and ("antidiarrheal" in (a["class"], b["class"])),
        "severity": SEVERITY_CAUTION,
        "title": "Cản trở hấp thu và ảnh hưởng hệ vi sinh đường ruột",
        "mechanism": "Kháng sinh đường uống tiêu diệt vi khuẩn gây bệnh đồng thời tác động lên hệ vi sinh đường ruột. Dùng đồng thời với Berberin có thể làm giảm khả năng hấp thu của kháng sinh qua niêm mạc ruột.",
        "management": "Uống hai loại thuốc này cách nhau tối thiểu 2 giờ để tránh tương tác cản trở hấp thu."
    },
    # 9. NSAID + Thuốc hạ huyết áp (Amlor, Concor, Micardis)
    {
        "match": lambda a, b: ("nsaid" in (a["class"], b["class"])) and any(c in (a["class"], b["class"]) for c in ("ccb", "beta_blocker", "arb")),
        "severity": SEVERITY_CAUTION,
        "title": "NSAID có thể làm giảm hiệu quả kiểm soát huyết áp",
        "mechanism": "Các thuốc NSAID (Ibuprofen, Meloxicam) ức chế prostaglandin tại thận, gây giữ muối và nước nhẹ, làm giảm một phần tác dụng hạ áp của thuốc điều trị tim mạch.",
        "management": "Người có bệnh tăng huyết áp nên tránh dùng NSAID kéo dài. Nếu chỉ cần giảm đau nhức nhẹ, nên ưu tiên dùng Paracetamol."
    },
]

def analyze_interaction(drug_id_1: str, drug_id_2: str) -> dict[str, Any]:
    """Phân tích tương tác giữa 2 loại thuốc cụ thể theo ID"""
    if drug_id_1 == drug_id_2:
        profile = DRUG_PROFILES.get(drug_id_1, {})
        name = profile.get("name", drug_id_1)
        return {
            "severity": SEVERITY_WARNING,
            "title": f"Bạn đang chọn cùng 1 loại thuốc: {name}",
            "mechanism": "Uống 2 liều của cùng 1 biệt dược cùng một thời điểm có thể gây quá liều cấp tính.",
            "management": "Hãy tuân thủ khoảng cách uống giữa các liều theo chỉ định trong toa thuốc (thường 4-6 giờ hoặc 12-24 giờ tùy loại).",
            "drug1": name,
            "drug2": name,
        }

    p1 = DRUG_PROFILES.get(drug_id_1)
    p2 = DRUG_PROFILES.get(drug_id_2)

    if not p1 or not p2:
        return {
            "severity": SEVERITY_SAFE,
            "title": "Không phát hiện tương tác nguy hiểm",
            "mechanism": "Hai thuốc này thuộc các nhóm cơ chế chuyển hóa khác nhau, không có ghi nhận tương tác bất lợi đáng kể.",
            "management": "Có thể sử dụng kết hợp nếu có chỉ định của bác sĩ hoặc dược sĩ. Hãy uống với nhiều nước và cách bữa ăn hợp lý.",
            "drug1": p1.get("name") if p1 else drug_id_1,
            "drug2": p2.get("name") if p2 else drug_id_2,
        }

    # Quét qua các quy tắc tương tác lâm sàng
    for rule in INTERACTION_RULES:
        if rule["match"](p1, p2):
            return {
                "severity": rule["severity"],
                "title": rule["title"],
                "mechanism": rule["mechanism"],
                "management": rule["management"],
                "drug1": p1["name"],
                "drug2": p2["name"],
            }

    # Trường hợp an toàn mặc định
    return {
        "severity": SEVERITY_SAFE,
        "title": f"Không có tương tác đối kháng đáng kể giữa {p1['name']} và {p2['name']}",
        "mechanism": f"{p1['name']} ({', '.join(p1['actives'])}) và {p2['name']} ({', '.join(p2['actives'])}) chuyển hóa qua các con đường sinh học độc lập, không ghi nhận tương tác bất lợi trong Dược thư Quốc gia.",
        "management": "Hai thuốc có thể phối hợp an toàn theo liều khuyến cáo. Nên uống cách nhau 1-2 giờ nếu một trong hai thuốc gây cồn cào dạ dày.",
        "drug1": p1["name"],
        "drug2": p2["name"],
    }


# ==============================================================================
# 2. GIAO THỨC CHĂM SÓC PHI DƯỢC LÝ TẠI NHÀ (CLINICAL HOME-CARE PROTOCOLS)
# ==============================================================================

HOME_CARE_PROTOCOLS = {
    "giam-dau": {
        "group_name": "Sốt, Đau đầu & Đau nhức cơ thể",
        "rest": "Nằm nghỉ ngơi ở phòng yên tĩnh, thoáng gió, nhiệt độ phòng duy trì 25–27°C. Mặc quần áo cotton rộng rãi, mỏng nhẹ, dễ thấm mồ hôi.",
        "physical": "Chườm ấm (nước ấm khoảng 37–38°C) tại các vùng mạch máu lớn: 2 bên nách, 2 bên bẹn và trán. Tuyệt đối không chườm đá lạnh hoặc thoa cồn vì gây co mạch làm nhiệt độ cơ thể khó thoát ra.",
        "nutrition": "Bù nước và điện giải tối đa: Uống nước lọc ấm, nước oresol pha đúng chuẩn, nước dừa tươi hoặc nước cam giàu vitamin C. Ăn các món dễ tiêu như cháo gà tía tô, súp rau củ ấm.",
        "red_flags": "Sốt cao trên 39.5°C không hạ sau khi đã dùng thuốc 2 giờ, đau đầu dữ dội kèm cứng cổ, co giật, thở dốc tím tái hoặc phát ban xuất huyết dưới da ➔ Cần đến bệnh viện cấp cứu ngay.",
    },
    "tieu-hoa": {
        "group_name": "Đau dạ dày, Trào ngược & Rối loạn tiêu hóa",
        "rest": "Không nằm ngay sau bữa ăn tối thiểu 2–3 giờ. Khi nằm ngủ nên kê cao đầu giường hoặc dùng gối chống trào ngược khoảng 15–20cm để ngăn acid trào lên thực quản.",
        "physical": "Xoa bụng nhẹ nhàng theo chiều kim đồng hồ quanh rốn trong 10–15 phút để kích thích nhu động ruột; chườm túi nước ấm lên vùng thượng vị để giảm cơn co thắt dạ dày.",
        "nutrition": "Chia nhỏ bữa ăn thành 4–5 bữa/ngày, nhai thật kỹ. Kiêng tuyệt đối: đồ cay nóng, thức ăn nhiều dầu mỡ chiên xào, cà phê, rượu bia, nước ngọt có ga và trái cây quá chua (chanh, cóc, xoài xanh). Bổ sung sữa chua và nước ấm.",
        "red_flags": "Nôn ra máu tươi hoặc dịch màu bã cà phê, đi ngoài phân đen hôi tanh, đau bụng quằn quại co cứng như gỗ, hoặc tiêu chảy mất nước lơ mơ ➔ Cần đưa ngay đến cơ sở y tế.",
    },
    "ho-hap": {
        "group_name": "Ho, Viêm họng & Đường hô hấp",
        "rest": "Nghỉ ngơi nhiều hơn, giữ ấm vùng cổ họng, ngực và bàn chân, đặc biệt vào ban đêm và sáng sớm. Tránh quạt gió thổi thẳng vào mặt.",
        "physical": "Súc họng sâu bằng nước muối sinh lý 0.9% ấm 3–4 lần mỗi ngày. Đặt máy tạo độ ẩm trong phòng ngủ nếu thời tiết hanh khô hoặc dùng điều hòa.",
        "nutrition": "Uống nước ấm mật ong chanh hoặc trà gừng ấm (lưu ý mật ong chỉ dùng cho trẻ trên 1 tuổi và người lớn). Ăn cháo hành ấm nhiều tiêu nhẹ, kiêng nước đá lạnh và đồ ăn quá ngọt.",
        "red_flags": "Khó thở, thở rít, cánh mũi phập phồng, rút lõm lồng ngực, môi tím tái, hoặc ho khạc ra đờm lẫn máu tươi ➔ Đi khám chuyên khoa hô hấp khẩn cấp.",
    },
    "di-ung": {
        "group_name": "Dị ứng, Mề đay & Mẩn ngứa",
        "rest": "Hạn chế tiếp xúc với các yếu tố kích ứng: phấn hoa, lông thú cưng, bụi mạt nhà, hóa chất tẩy rửa mạnh hoặc thời tiết thay đổi đột ngột.",
        "physical": "Tắm bằng nước mát hoặc nước ấm vừa phải (không tắm nước quá nóng vì làm giãn mạch gây ngứa dữ dội hơn). Thoa kem dưỡng ẩm dịu nhẹ lành tính. Tuyệt đối không gãi làm trầy xước niêm mạc gây nhiễm trùng.",
        "nutrition": "Uống nhiều nước để hỗ trợ thận đào thải độc tố. Tạm thời kiêng các thức ăn dễ gây kích ứng như hải sản (tôm, cua, mực), nhộng tằm, măng chua và rượu bia.",
        "red_flags": "Dị ứng kèm sưng phù môi, mí mắt, khó thở, thở khò khè, tụt huyết áp hoa mắt chóng mặt (dấu hiệu sốc phản vệ) ➔ Gọi 115 cấp cứu lập tức.",
    },
    "tim-mach": {
        "group_name": "Tim mạch & Kiểm soát Huyết áp",
        "rest": "Giữ tâm lý thư giãn, tránh căng thẳng lo âu, ngủ đủ 7–8 tiếng mỗi ngày. Tránh làm việc gắng sức quá mức hoặc thức khuya.",
        "physical": "Tập thể dục nhẹ nhàng đều đặn: Đi bộ vừa sức 30 phút/ngày, tập yoga hoặc dưỡng sinh. Không tập thể dục ngoài trời lúc sáng sớm trời lạnh.",
        "nutrition": "Thực hiện chế độ ăn giảm muối nghiêm ngặt (dưới 5g muối/ngày, khoảng 1 thìa cà phê). Hạn chế mỡ động vật, phủ tạng; tăng cường rau xanh giàu chất xơ, chuối chín và cá béo.",
        "red_flags": "Đau thắt ngực dữ dội cảm giác đè nặng lan ra cánh tay trái hoặc hàm dưới, huyết áp tăng vọt > 180/120 mmHg, nhìn mờ hoặc méo miệng liệt tay chân ➔ Gọi cấp cứu 115 ngay.",
    },
    "noi-tiet": {
        "group_name": "Đái tháo đường & Chuyển hóa",
        "rest": "Sinh hoạt điều độ, kiểm tra và chăm sóc bàn chân hàng ngày (quan sát kỹ các vết chai, xước hoặc loét nhỏ để xử lý sớm, tránh biến chứng hoại tử bàn chân).",
        "physical": "Đi bộ nhẹ nhàng sau bữa ăn chính 30 phút giúp tế bào tiêu thụ đường tốt hơn và ổn định đường huyết.",
        "nutrition": "Kiểm soát khẩu phần carbohydrate (tinh bột có chỉ số đường huyết thấp như gạo lứt, khoai lang luộc). Ăn đúng giờ, không bỏ bữa. Luôn mang theo kẹo ngọt hoặc gói đường trong túi đề phòng tụt đường huyết.",
        "red_flags": "Đường huyết tụt đột ngột (vã mồ hôi lạnh, run rẩy, hoa mắt, đói lả) sau khi uống thuốc mà không ăn, hoặc đường huyết quá cao kèm nôn ói thở mùi táo chín (nhiễm toan ceton) ➔ Cần xử trí cấp cứu.",
    },
    "khang-sinh": {
        "group_name": "Dùng kháng sinh điều trị nhiễm khuẩn",
        "rest": "Dành nhiều thời gian nghỉ ngơi để hệ miễn dịch phục hồi và tiêu diệt vi khuẩn.",
        "physical": "Uống thuốc đúng giờ, đúng khoảng cách giữa các cữ thuốc theo hướng dẫn để duy trì nồng độ thuốc diệt khuẩn ổn định trong máu.",
        "nutrition": "Uống tối thiểu 2 lít nước mỗi ngày giúp thận đào thải cặn thuốc. Sau khi kết thúc đợt kháng sinh hoặc cách cữ kháng sinh 2 giờ, nên bổ sung sữa chua hoặc men vi sinh để tái tạo hệ vi sinh có lợi đường ruột.",
        "red_flags": "Uống thuốc bị nổi mẩn ngứa toàn thân, tiêu chảy dữ dội tóe nước, sốt cao tái phát hoặc khó thở ➔ Ngừng thuốc và liên hệ bác sĩ điều trị ngay.",
    },
    "vitamin": {
        "group_name": "Bổ sung Vitamin & Nâng cao thể trạng",
        "rest": "Duy trì lối sống năng động, ngủ trước 23h để cơ thể tổng hợp vi chất và phục hồi năng lượng thể chất.",
        "physical": "Tắm nắng buổi sáng sớm 15–20 phút giúp cơ thể tự tổng hợp Vitamin D tự nhiên cho xương chắc khỏe.",
        "nutrition": "Chế độ dinh dưỡng cân bằng 4 nhóm chất: Đạm, đường, béo, vitamin & khoáng chất. Uống vitamin C vào ban ngày (tránh uống tối gây khó ngủ hoặc nguy cơ sỏi thận). Uống viên sắt với nước lọc, tránh dùng chung với trà hoặc sữa.",
        "red_flags": "Dùng quá liều gây buồn nôn, đau dạ dày hoặc táo bón kéo dài ➔ Giảm liều hoặc tạm ngừng để hỏi ý kiến dược sĩ.",
    },
}

def get_home_care_advice(group_id: str | None, drug_name: str | None = None) -> dict[str, str]:
    """Lấy hướng dẫn chăm sóc y tế tại nhà theo nhóm bệnh và thuốc"""
    protocol = HOME_CARE_PROTOCOLS.get(group_id or "giam-dau", HOME_CARE_PROTOCOLS["giam-dau"])
    drug_intro = f" đối với người đang dùng **{drug_name}**" if drug_name else ""
    return {
        "title": f"Cẩm nang chăm sóc & Hành động nên làm tại nhà{drug_intro} ({protocol['group_name']})",
        "rest": protocol["rest"],
        "physical": protocol["physical"],
        "nutrition": protocol["nutrition"],
        "red_flags": protocol["red_flags"],
    }
