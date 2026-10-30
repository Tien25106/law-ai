"""Module AI Cốt lõi cho Law GPT (Medical AI Engine)
Tích hợp 6 thành phần chuyên sâu:
  1. Medical Guardrails & Emergency Triggers (Bộ lọc an toàn & Phát hiện nguy cấp y tế)
  2. Medical NER (Named Entity Recognition - Bóc tách thực thể y tế & Ý định lâm sàng)
  3. Clinical Drug Interaction Engine (Bộ phân tích tương tác thuốc thông minh)
  4. Clinical Home-Care Protocol (Tư vấn chăm sóc phi dược lý & Chế độ sinh hoạt cá nhân hóa)
  5. RAG & Semantic Retrieval (Truy xuất tăng cường tri thức y khoa từ CSDL Dược)
  6. Generative Response Synthesis (Tổng hợp phản hồi AI - Hỗ trợ cả Local Engine & Cloud LLM)
"""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import unicodedata
import urllib.request
import urllib.error
from pathlib import Path

# Import tri thức dược lâm sàng
try:
    from backend.clinical_kb import (
        analyze_interaction, get_home_care_advice, DRUG_PROFILES,
        SEVERITY_DANGER, SEVERITY_WARNING, SEVERITY_CAUTION, SEVERITY_BENEFICIAL, SEVERITY_SAFE
    )
except ImportError:
    from clinical_kb import (
        analyze_interaction, get_home_care_advice, DRUG_PROFILES,
        SEVERITY_DANGER, SEVERITY_WARNING, SEVERITY_CAUTION, SEVERITY_BENEFICIAL, SEVERITY_SAFE
    )

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "drugs.db"
CONFIG_PATH = ROOT / "backend" / "ai_config.json"

STOP_WORDS = {
    "toi", "minh", "em", "ban", "bac", "si", "cho", "hoi", "bi", "va", "la",
    "cac", "nhung", "co", "duoc", "cua", "trong", "khi", "o", "voi", "neu",
    "mot", "nhieu", "gi", "sao", "uong", "thuoc", "can", "dung", "hay", "hoi",
    "rat", "qua", "bi", "nay", "do", "the", "nao"
}


def normalize_text(text: str) -> str:
    """Chuẩn hóa tiếng Việt: chuyển chữ thường, bỏ dấu thanh và sửa lỗi gõ phím thường gặp"""
    if not text:
        return ""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r"[\u0300-\u036f]", "", text)
    text = text.replace("đ", "d")

    # Sửa lỗi chính tả L/N hoặc gõ nhầm thường gặp
    text = re.sub(r"\bbuon\s+lon\b", "buon non", text)
    text = re.sub(r"\bmac\s+lon\b", "mac non", text)
    text = re.sub(r"\bnon\s+lon\b", "non mua", text)
    text = re.sub(r"\blon\s+mua\b", "non mua", text)
    return text.strip()


def find_drugs_in_text(text: str) -> list[str]:
    """Tìm kiếm các tên thuốc được nhắc đến trong văn bản tự nhiên"""
    norm = normalize_text(text)
    found = []
    # Sắp xếp theo độ dài giảm dần
    sorted_profiles = sorted(DRUG_PROFILES.items(), key=lambda x: len(x[1]["name"]), reverse=True)
    for d_id, p in sorted_profiles:
        name_norm = normalize_text(p["name"])
        tokens = name_norm.split()
        if re.search(r"\b" + re.escape(tokens[0]) + r"\b", norm):
            if d_id not in found:
                found.append(d_id)
    return found


# ==============================================================================
# PHẦN 1: MEDICAL GUARDRAILS & EMERGENCY TRIGGERS (BỘ LỌC AN TOÀN & NGUY CẤP)
# ==============================================================================

EMERGENCY_PATTERNS = [
    # Dấu hiệu nhồi máu cơ tim / mạch vành cấp
    (r"\b(dau that nguc|dau nguc du doi|nguc bi de nang|dau lan ra tay|dau tim cap)\b",
     "Đau thắt ngực dữ dội nghi ngờ hội chứng mạch vành cấp hoặc nhồi máu cơ tim."),
    # Dấu hiệu suy hô hấp nặng
    (r"\b(khong tho duoc|kho tho du doi|tim tai|ngat tho|tho rit thanh quan)\b",
     "Suy hô hấp cấp tính, khó thở nghiêm trọng đe dọa tính mạng."),
    # Dấu hiệu đột quỵ não (FAST)
    (r"\b(liet nua nguoi|meo mieng|noi ngong dot ngot|mat thi luc dot ngot|yeu tay chan dot ngot)\b",
     "Các dấu hiệu cảnh báo đột quỵ não cấp tính (FAST)."),
    # Dấu hiệu bụng ngoại khoa cấp cứu (viêm ruột thừa cấp, thủng tạng rỗng)
    (r"\b(bung go cung|bung cung nhu go|dau ruot thua|dau bung du doi quan that)\b",
     "Đau bụng dữ dội kèm co cứng thành bụng như gỗ nghi ngờ viêm ruột thừa cấp hoặc bụng ngoại khoa."),
    # Sốc phản vệ / Ngộ độc
    (r"\b(soc phan ve|uong qua lieu|ngo doc thuoc|uong nham thuoc|non ra mau|di ngoai ra mau)\b",
     "Dấu hiệu sốc phản vệ, ngộ độc thuốc cấp hoặc xuất huyết nội tạng nặng."),
    # Co giật, mất ý thức
    (r"\b(co giat|ngat xiu|hon me|bat tinh|mat y thuc)\b",
     "Trạng thái co giật, hôn mê hoặc mất tri giác cấp tính."),
]


class MedicalGuardrails:
    """Bộ lọc an toàn y tế và nhận diện tình trạng cấp cứu"""

    @staticmethod
    def check_emergency(query: str) -> tuple[bool, str]:
        norm = normalize_text(query)
        for pattern, reason in EMERGENCY_PATTERNS:
            if re.search(pattern, norm):
                return True, reason
        return False, ""

    @staticmethod
    def build_emergency_response(reason: str) -> dict:
        return {
            "reply": (
                "🚨 **CẢNH BÁO NGUY CẤP Y TẾ!**\n\n"
                f"Hệ thống phát hiện dấu hiệu nguy hiểm tính mạng: **{reason}**\n\n"
                "⚠️ **HÀNH ĐỘNG KHẨN CẤP:**\n"
                "1. Hãy gọi ngay cấp cứu **115** hoặc di chuyển khẩn trương đến khoa Cấp cứu của bệnh viện gần nhất!\n"
                "2. **TUYỆT ĐỐI KHÔNG** tự ý mua hoặc uống thuốc qua mạng trong tình huống này.\n"
                "3. Giữ bệnh nhân ở tư thế thoải mái, thoáng khí và luôn có người theo dõi liên tục."
            ),
            "choices": [
                {"label": "📞 Gọi cấp cứu 115", "query": "cấp cứu"},
                {"label": "Bệnh viện gần nhất", "query": "bệnh viện"},
                {"label": "Chọn nhóm thuốc khác", "query": "nhóm thuốc"},
            ],
            "ai_metadata": {
                "is_emergency": True,
                "reason": reason,
                "provider": "guardrails",
            }
        }


# ==============================================================================
# PHẦN 2: MEDICAL NER (NAMED ENTITY RECOGNITION - NHẬN DIỆN THỰC THỂ Y TẾ)
# ==============================================================================

SYMPTOM_DICTIONARY = {
    # 1. Giảm đau - Hạ sốt
    "sot cao": ("Sốt cao", "giam-dau"),
    "sot": ("Sốt, tăng thân nhiệt", "giam-dau"),
    "nong sot": ("Sốt, nóng sốt", "giam-dau"),
    "dau dau": ("Đau đầu, nhức đầu", "giam-dau"),
    "nhuc dau": ("Đau đầu, nhức đầu", "giam-dau"),
    "dau nua dau": ("Đau nửa đầu", "giam-dau"),
    "dau rang": ("Đau răng", "giam-dau"),
    "dau co": ("Đau nhức cơ xương khớp", "giam-dau"),
    "nhuc moi": ("Đau nhức mỏi cơ thể", "giam-dau"),
    "dau nhuc": ("Đau nhức cơ thể", "giam-dau"),
    "dau bung kinh": ("Đau bụng kinh", "giam-dau"),
    "viem khop": ("Viêm khớp, thoái hóa khớp", "giam-dau"),

    # 2. Hô hấp
    "ho co dom": ("Ho có đờm đặc", "ho-hap"),
    "ho": ("Ho, ngứa họng", "ho-hap"),
    "dom": ("Tăng tiết đờm nhầy", "ho-hap"),
    "viem hong": ("Viêm họng, đau rát họng", "ho-hap"),
    "dau hong": ("Đau rát họng", "ho-hap"),
    "nghet mui": ("Nghẹt mũi, ngạt mũi", "ho-hap"),
    "so mui": ("Sổ mũi, chảy nước mũi", "ho-hap"),
    "chay nuoc mui": ("Sổ mũi, chảy nước mũi", "ho-hap"),
    "hat hoi": ("Hắt hơi", "di-ung"),
    "cam cum": ("Cảm cúm, cảm lạnh", "ho-hap"),
    "kho tho": ("Khó thở nhẹ, co thắt phế quản", "ho-hap"),
    "hen suyen": ("Hen suyễn, co thắt phế quản", "ho-hap"),

    # 3. Dị ứng
    "di ung": ("Dị ứng, phản ứng quá mẫn", "di-ung"),
    "ngua": ("Mẩn ngứa da", "di-ung"),
    "me day": ("Mề đay, phát ban", "di-ung"),
    "man ngua": ("Mẩn ngứa", "di-ung"),
    "viem mui di ung": ("Viêm mũi dị ứng", "di-ung"),

    # 4. Tiêu hóa - Dạ dày - Ruột
    "dau bung": ("Đau bụng, co thắt tiêu hóa", "tieu-hoa"),
    "dau bung duoi": ("Đau bụng dưới", "tieu-hoa"),
    "bung cung": ("Bụng căng chướng khó tiêu", "tieu-hoa"),
    "cang bung": ("Bụng căng chướng", "tieu-hoa"),
    "dau da day": ("Đau dạ dày, viêm dạ dày", "tieu-hoa"),
    "dau bao tu": ("Đau dạ dày, viêm dạ dày", "tieu-hoa"),
    "dau thuong vi": ("Đau vùng thượng vị dạ dày", "tieu-hoa"),
    "trao nguoc": ("Trào ngược dạ dày thực quản (GERD)", "tieu-hoa"),
    "o nong": ("Ợ nóng, nóng rát thực quản", "tieu-hoa"),
    "o chua": ("Ợ chua", "tieu-hoa"),
    "loet da day": ("Loét dạ dày tá tràng", "tieu-hoa"),
    "buon non": ("Buồn nôn, nôn nao", "tieu-hoa"),
    "non mua": ("Nôn mửa", "tieu-hoa"),
    "mac non": ("Buồn nôn", "tieu-hoa"),
    "non": ("Nôn ói", "tieu-hoa"),
    "tieu chay": ("Tiêu chảy, đi ngoài phân lỏng", "tieu-hoa"),
    "di ngoai": ("Tiêu chảy, đi ngoài lỏng", "tieu-hoa"),
    "day bung": ("Đầy bụng, khó tiêu", "tieu-hoa"),
    "chuong bung": ("Chướng bụng, đầy hơi", "tieu-hoa"),
    "kho tieu": ("Khó tiêu, đầy hơi", "tieu-hoa"),
    "roi loan tieu hoa": ("Rối loạn tiêu hóa", "tieu-hoa"),

    # 5. Kháng sinh / Nhiễm trùng
    "nhiem khuan": ("Nhiễm khuẩn đường hô hấp / tiết niệu", "khang-sinh"),
    "viem xoang": ("Viêm xoang nhiễm khuẩn", "khang-sinh"),
    "viem tai": ("Viêm tai giữa", "khang-sinh"),

    # 6. Tim mạch / Nội tiết
    "cao huyet ap": ("Tăng huyết áp", "tim-mach"),
    "huyet ap cao": ("Tăng huyết áp", "tim-mach"),
    "mo mau": ("Rối loạn mỡ máu, tăng cholesterol", "tim-mach"),
    "tieu duong": ("Đái tháo đường týp 2", "noi-tiet"),
    "duong huyet": ("Đường huyết cao", "noi-tiet"),
    "suy giap": ("Suy giáp, bệnh tuyến giáp", "noi-tiet"),

    # 7. Vitamin
    "met moi": ("Mệt mỏi, suy nhược thể chất", "vitamin"),
    "suy nhuoc": ("Suy nhược cơ thể", "vitamin"),
    "thieu mau": ("Thiếu máu do thiếu sắt", "vitamin"),
    "loang xuong": ("Phòng ngừa loãng xương, thiếu canxi", "vitamin"),
}

DEMOGRAPHIC_DICTIONARY = {
    "tre em": "Trẻ em",
    "em be": "Trẻ nhỏ",
    "so sinh": "Trẻ sơ sinh",
    "ba bau": "Phụ nữ mang thai",
    "mang thai": "Phụ nữ mang thai",
    "co thai": "Phụ nữ mang thai",
    "cho con bu": "Phụ nữ đang cho con bú",
    "nguoi gia": "Người cao tuổi",
    "nguoi lon tuoi": "Người cao tuổi",
}

CONDITION_DICTIONARY = {
    "loet da day": "Tiền sử viêm loét dạ dày",
    "suy gan": "Bệnh lý suy gan",
    "men gan": "Tăng men gan",
    "suy than": "Bệnh lý suy thận",
    "hen": "Tiền sử hen phế quản",
    "tim mach": "Bệnh tim mạch",
    "tieu duong": "Bệnh đái tháo đường",
}

HOME_CARE_PATTERN = r"\b(ngoai ra.*nen lam gi|ngoai ra.*lam gi|ngoai ra.*the nao|nen lam gi|can lam gi|kieng gi|can kieng|an gi|uong gi|nghi ngoi|cham soc|sinh hoat|luu y gi|cach chua tai nha|meo|bien phap|hanh dong|loi khuyen)\b"
INTERACTION_PATTERN = r"\b(uong chung|uong cung|dung chung|dung cung|cung luc|ket hop|uong voi|tuong tac|uong ca hai|phoi hop|co tuong tac|uong duoc khong|dung duoc khong|dong thoi|uong kem)\b"


class MedicalNER:
    """Bộ bóc tách thực thể y tế tiếng Việt (Symptoms, Demographics, Conditions, Drug Mentions, Intent)"""

    @classmethod
    def extract_entities(cls, text: str) -> dict:
        norm = normalize_text(text)
        symptoms = []
        target_groups = []

        # 1. Bóc tách triệu chứng
        sorted_symptom_terms = sorted(SYMPTOM_DICTIONARY.keys(), key=lambda x: len(x), reverse=True)
        for term in sorted_symptom_terms:
            if re.search(r"\b" + re.escape(term) + r"\b", norm):
                std_name, grp = SYMPTOM_DICTIONARY[term]
                if std_name not in symptoms:
                    symptoms.append(std_name)
                if grp not in target_groups:
                    target_groups.append(grp)

        # 2. Bóc tách đối tượng người bệnh
        demographics = []
        for term, std_demo in DEMOGRAPHIC_DICTIONARY.items():
            if re.search(r"\b" + re.escape(term) + r"\b", norm):
                if std_demo not in demographics:
                    demographics.append(std_demo)

        # 3. Bóc tách bệnh nền / tiền sử
        conditions = []
        for term, std_cond in CONDITION_DICTIONARY.items():
            if re.search(r"\b" + re.escape(term) + r"\b", norm):
                if std_cond not in conditions:
                    conditions.append(std_cond)

        # 4. Bóc tách các thuốc được nhắc đến trong câu hỏi
        drug_mentions = find_drugs_in_text(text)

        # 5. Xác định ý định người dùng (Intent)
        intent = "GENERAL_SEARCH"
        if re.search(r"\b(chao|xin chao|hello|hi)\b", norm):
            intent = "GREETING"
        elif len(drug_mentions) >= 2 or re.search(INTERACTION_PATTERN, norm):
            intent = "DRUG_INTERACTION"
        elif re.search(HOME_CARE_PATTERN, norm):
            intent = "HOME_CARE"
        elif "tac dung phu" in norm or "uong vao bi" in norm:
            intent = "SIDE_EFFECTS"
        elif "chong chi dinh" in norm or "ai khong duoc uong" in norm:
            intent = "CONTRAINDICATION"
        elif "lieu dung" in norm or "uong the nao" in norm or "ngay may vien" in norm:
            intent = "DOSAGE"
        elif symptoms:
            intent = "SYMPTOM_CONSULTATION"

        return {
            "symptoms": symptoms,
            "target_groups": target_groups,
            "demographics": demographics,
            "conditions": conditions,
            "drug_mentions": drug_mentions,
            "intent": intent,
        }


# ==============================================================================
# PHẦN 3: RAG (RETRIEVAL-AUGMENTED GENERATION) & SEMANTIC RETRIEVAL
# ==============================================================================

class MedicalRAG:
    """Hệ thống tìm kiếm ngữ nghĩa và truy xuất tri thức Dược lâm sàng"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._corpus: list[dict] = []
        self._tfidf_docs: list[dict[str, float]] = []
        self._idf: dict[str, float] = {}
        self._load_and_index()

    def _load_and_index(self):
        if not self.db_path.exists():
            return
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT d.*, g.name AS group_name
            FROM drugs d
            JOIN drug_groups g ON d.group_id = g.id
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        self._corpus = rows
        total_docs = len(rows)
        doc_freq: dict[str, int] = {}

        for doc in rows:
            text = " ".join([
                doc["name"],
                doc["active_ingredient"],
                doc["group_name"],
                doc.get("indications", ""),
                doc.get("form", ""),
                doc.get("dosage", ""),
            ])
            raw_tokens = normalize_text(text).split()
            tokens = {t for t in raw_tokens if t not in STOP_WORDS and len(t) > 1}
            for t in tokens:
                doc_freq[t] = doc_freq.get(t, 0) + 1

        self._idf = {
            t: math.log((total_docs + 1) / (df + 1)) + 1.0
            for t, df in doc_freq.items()
        }

        for doc in rows:
            text = " ".join([
                doc["name"],
                doc["active_ingredient"],
                doc["group_name"],
                doc.get("indications", ""),
                doc.get("form", ""),
            ])
            raw_tokens = normalize_text(text).split()
            tokens = [t for t in raw_tokens if t not in STOP_WORDS and len(t) > 1]
            tf: dict[str, float] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0.0) + 1.0
            doc_vec = {t: (count / (len(tokens) or 1)) * self._idf.get(t, 1.0) for t, count in tf.items()}
            self._tfidf_docs.append(doc_vec)

    def get_drug_by_id(self, drug_id: str) -> dict | None:
        for d in self._corpus:
            if d["id"] == drug_id:
                return d
        return None

    def retrieve(self, query: str, target_groups: list[str] | None = None, demographic_filter: list[str] | None = None, top_k: int = 4) -> list[dict]:
        """Truy xuất các thuốc phù hợp nhất theo Vector Cosine Similarity & Nhóm bệnh lý"""
        if not self._corpus:
            return []

        raw_q_tokens = normalize_text(query).split()
        q_tokens = [t for t in raw_q_tokens if t not in STOP_WORDS and len(t) > 1]
        if not q_tokens:
            q_tokens = raw_q_tokens

        q_tf: dict[str, float] = {}
        for t in q_tokens:
            q_tf[t] = q_tf.get(t, 0.0) + 1.0
        q_vec = {t: (count / len(q_tokens)) * self._idf.get(t, 1.0) for t, count in q_tf.items()}

        scores = []
        for idx, doc_vec in enumerate(self._tfidf_docs):
            dot_product = sum(q_vec[t] * doc_vec.get(t, 0.0) for t in q_vec)
            q_norm = math.sqrt(sum(v ** 2 for v in q_vec.values())) or 1.0
            doc_norm = math.sqrt(sum(v ** 2 for v in doc_vec.values())) or 1.0
            score = dot_product / (q_norm * doc_norm)

            doc = self._corpus[idx]

            # 1. Trọng số nhóm mục tiêu
            if target_groups and doc["group_id"] in target_groups:
                score += 0.55

            # 2. Khớp trực tiếp tên biệt dược hoặc hoạt chất
            norm_name = normalize_text(doc["name"])
            norm_active = normalize_text(doc["active_ingredient"])
            if any(t in norm_name for t in q_tokens if len(t) > 2):
                score += 0.5
            if any(t in norm_active for t in q_tokens if len(t) > 2):
                score += 0.4

            # 3. Kiểm tra An toàn & Chống chỉ định theo nhóm đối tượng
            contra = normalize_text(doc.get("contraindications", ""))
            warning = None
            if demographic_filter:
                if "Phụ nữ mang thai" in demographic_filter and ("phu nu co thai" in contra or "mang thai" in contra or "say thai" in contra):
                    warning = "⚠️ CẢNH BÁO AN TOÀN: Thuốc chống chỉ định hoặc cần thận trọng cao ở phụ nữ mang thai!"
                    score -= 0.6
                if "Trẻ sơ sinh" in demographic_filter and ("tre em duoi" in contra or "tre so sinh" in contra):
                    warning = "⚠️ CẢNH BÁO AN TOÀN: Chống chỉ định cho trẻ nhỏ/trẻ sơ sinh!"
                    score -= 0.6

            scores.append((score, doc, warning))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for s, doc, warn in scores[:top_k]:
            if s > 0.02 or len(results) == 0:
                item = dict(doc)
                item["_relevance_score"] = round(s, 3)
                item["_safety_warning"] = warn
                results.append(item)
        return results


# ==============================================================================
# PHẦN 4: GENERATIVE LLM RESPONSE SYNTHESIS (TỔNG HỢP PHẢN HỒI AI)
# ==============================================================================

class MedicalLLMGenerator:
    """Mô-đun sinh ngôn ngữ y tế: hỗ trợ Cloud LLM (Gemini/OpenAI) và Autonomous Engine nội bộ"""

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.provider = "gemini" if os.environ.get("GEMINI_API_KEY") else ("openai" if os.environ.get("OPENAI_API_KEY") else "local")

        if CONFIG_PATH.exists():
            try:
                cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                if cfg.get("gemini_api_key"):
                    self.api_key = cfg["gemini_api_key"]
                    self.provider = "gemini"
                elif cfg.get("openai_api_key"):
                    self.api_key = cfg["openai_api_key"]
                    self.provider = "openai"
            except Exception:
                pass

    def _call_gemini_api(self, prompt: str) -> str | None:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800}
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return None

    def generate(
        self,
        user_query: str,
        entities: dict,
        retrieved_drugs: list[dict],
        current_drug: dict | None = None,
        current_group: str | None = None
    ) -> tuple[str, list[dict]]:
        """Sinh câu trả lời y tế thông minh đa tình huống"""

        intent = entities["intent"]
        drug_mentions = entities.get("drug_mentions", [])
        reply_lines = []

        # ======================================================================
        # TÌNH HUỐNG 1: KIỂM TRA TƯƠNG TÁC THUỐC (DRUG INTERACTION)
        # ======================================================================
        if intent == "DRUG_INTERACTION":
            if len(drug_mentions) >= 2:
                id1, id2 = drug_mentions[0], drug_mentions[1]
                report = analyze_interaction(id1, id2)
                sev = report["severity"]

                if sev == SEVERITY_DANGER:
                    badge = "🔴 **MỨC ĐỘ NGUY HIỂM: CHỐNG CHỈ ĐỊNH PHỐI HỢP**"
                elif sev == SEVERITY_WARNING:
                    badge = "🟡 **MỨC ĐỘ CẢNH BÁO: TĂNG NGUY CƠ ĐỘC TÍNH**"
                elif sev == SEVERITY_CAUTION:
                    badge = "🟡 **MỨC ĐỘ THẬN TRỌNG: CẦN THEO DÕI LÂM SÀNG**"
                elif sev == SEVERITY_BENEFICIAL:
                    badge = "🟢 **MỨC ĐỘ ĐÁNH GIÁ: PHỐI HỢP HỖ TRỢ CÓ LỢI**"
                else:
                    badge = "🟢 **MỨC ĐỘ AN TOÀN: KHÔNG CÓ TƯƠNG TÁC ĐỐI KHÁNG ĐÁNG KỂ**"

                reply_lines.append(f"🔬 **PHÂN TÍCH TƯƠNG TÁC THUỐC BẰNG AI**")
                reply_lines.append(f"Cặp phối hợp: **{report['drug1']}** ➕ **{report['drug2']}**\n")
                reply_lines.append(badge)
                reply_lines.append(f"📌 **Đánh giá:** {report['title']}\n")
                reply_lines.append(f"⚙️ **Cơ chế tương tác:**\n{report['mechanism']}\n")
                reply_lines.append(f"📋 **Khuyến cáo xử trí y khoa:**\n{report['management']}\n")
                reply_lines.append("⚠️ *Lưu ý: Luôn tham khảo ý kiến bác sĩ hoặc dược sĩ trước khi phối hợp thuốc để đảm bảo an toàn tuyệt đối.*")

                choices = [
                    {"label": f"Xem {report['drug1']}", "query": report['drug1']},
                    {"label": f"Xem {report['drug2']}", "query": report['drug2']},
                    {"label": "Kiểm tra thuốc khác", "query": "tương tác thuốc"},
                    {"label": "Chọn nhóm khác", "query": "nhóm thuốc"},
                ]
                return "\n".join(reply_lines), choices

            elif len(drug_mentions) == 1:
                d_id = drug_mentions[0]
                d_name = DRUG_PROFILES.get(d_id, {}).get("name", "thuốc này")
                reply_lines.append(f"🔬 **Kiểm tra tương tác cho {d_name}:**")
                reply_lines.append(f"Bạn đang muốn kiểm tra tương tác giữa **{d_name}** với loại thuốc nào khác?")
                reply_lines.append("👉 Hãy nhắn tên loại thuốc thứ hai (ví dụ: *'{d_name} uống chung với Ibuprofen'* hoặc *'{d_name} và Plavix'*) hoặc chọn một thuốc bên dưới nhé!")

                choices = [{"label": d["name"], "query": f"{d_name} uống chung với {d['name']}"} for d in retrieved_drugs[:4]]
                choices.append({"label": "Chọn nhóm khác", "query": "nhóm thuốc"})
                return "\n".join(reply_lines), choices

            else:
                reply_lines.append("🔬 **Hệ thống AI Kiểm tra Tương tác Thuốc (Drug Interaction Checker):**")
                reply_lines.append("Bạn có thể kiểm tra xem 2 loại thuốc uống chung với nhau có an toàn không.\n")
                reply_lines.append("💡 **Cách hỏi:** Nhắn tin theo mẫu:")
                reply_lines.append("• *'Uống Panadol với Ibuprofen cùng lúc có sao không?'*")
                reply_lines.append("• *'Plavix kết hợp Meloxicam có được không?'*")
                reply_lines.append("• *'Concor dùng chung với Ventolin có nguy hiểm không?'*")
                reply_lines.append("\nHoặc dùng công cụ chọn thuốc tương tác bên dưới trang web để kiểm tra trực quan!")

                choices = [
                    {"label": "Panadol + Ibuprofen", "query": "Uống Panadol với Ibuprofen có sao không"},
                    {"label": "Plavix + Meloxicam", "query": "Plavix kết hợp Meloxicam có được không"},
                    {"label": "Nexium + Ibuprofen", "query": "Nexium uống chung Ibuprofen có sao không"},
                    {"label": "Chọn nhóm khác", "query": "nhóm thuốc"},
                ]
                return "\n".join(reply_lines), choices

        # ======================================================================
        # TÌNH HUỐNG 2: CHĂM SÓC PHI DƯỢC LÝ & SINH HOẠT TẠI NHÀ (HOME CARE)
        # ======================================================================
        if intent == "HOME_CARE":
            target_group = current_group
            drug_name = None

            if current_drug:
                target_group = current_drug.get("group") or current_drug.get("group_id")
                drug_name = current_drug.get("name")
            elif retrieved_drugs:
                target_group = retrieved_drugs[0].get("group") or retrieved_drugs[0].get("group_id")
                drug_name = retrieved_drugs[0].get("name")

            protocol = get_home_care_advice(target_group, drug_name)

            reply_lines.append(f"🩺 **{protocol['title']}**\n")
            reply_lines.append("Bên cạnh việc dùng thuốc đúng chỉ định, việc áp dụng đồng bộ các biện pháp chăm sóc phi dược lý sẽ giúp cơ thể nhanh hồi phục và hạn chế tái phát:\n")
            reply_lines.append(f"🛌 **1. Chế độ Nghỉ ngơi & Môi trường:**\n{protocol['rest']}\n")
            reply_lines.append(f"🌡️ **2. Biện pháp Vật lý hỗ trợ:**\n{protocol['physical']}\n")
            reply_lines.append(f"🍲 **3. Dinh dưỡng & Bù nước (Nên ăn gì / Kiêng gì):**\n{protocol['nutrition']}\n")
            reply_lines.append(f"🚨 **4. Dấu hiệu Cảnh báo đỏ (Cần đến bệnh viện ngay):**\n{protocol['red_flags']}\n")
            reply_lines.append("💡 *Nguồn: Hướng dẫn chăm sóc lâm sàng tại nhà – Cục Quản lý Dược & Dược thư Quốc gia.*")

            choices = [
                {"label": "Kiểm tra tương tác thuốc", "query": "kiểm tra tương tác thuốc"},
                {"label": "Xem thuốc cùng nhóm", "query": protocol.get("group_name", "nhóm thuốc")},
                {"label": "Chọn nhóm khác", "query": "nhóm thuốc"},
            ]
            return "\n".join(reply_lines), choices

        # ======================================================================
        # TÌNH HUỐNG 3: CLOUD LLM (NẾU CÓ CẤU HÌNH API KEY)
        # ======================================================================
        if self.provider == "gemini" and self.api_key:
            context_text = "\n\n".join([
                f"- Tên thuốc: {d['name']} ({d['active_ingredient']})\n"
                f"  Dạng bào chế: {d['form']} | Nhóm: {d['group_name']}\n"
                f"  Số ĐK: {d['registration_no']} | Hãng: {d['manufacturer']}\n"
                f"  Chỉ định: {d.get('indications', '')}\n"
                f"  Liều dùng: {d.get('dosage', '')}\n"
                f"  Chống chỉ định: {d.get('contraindications', '')}\n"
                f"  Tác dụng phụ: {d.get('side_effects', '')}"
                for d in retrieved_drugs
            ])
            prompt = (
                "Bạn là Trợ lý AI Dược phẩm 'Law GPT' của Infranixx. Trả lời bằng tiếng Việt chuyên nghiệp, ân cần và chuẩn y khoa.\n"
                "CHỈ ĐƯỢC sử dụng thông tin trong tài liệu sau đây để trả lời, TUYỆT ĐỐI KHÔNG tự bịa ra thuốc ngoài tài liệu:\n"
                "=== TÀI LIỆU DƯỢC THƯ BỘ Y TẾ ===\n"
                f"{context_text}\n"
                "=================================\n\n"
                f"Câu hỏi của người dùng: '{user_query}'\n"
                f"Thực thể nhận diện: Triệu chứng={entities['symptoms']}, Đối tượng={entities['demographics']}, Tiền sử={entities['conditions']}\n"
                "Yêu cầu:\n"
                "1. Trả lời ngắn gọn, gạch đầu dòng các thuốc phù hợp kèm liều dùng tham khảo.\n"
                "2. Nếu có cảnh báo chống chỉ định với đối tượng/tiền sử, phải in đậm cảnh báo.\n"
                "3. Luôn kết thúc bằng câu khuyến cáo tham khảo ý kiến bác sĩ/dược sĩ."
            )
            cloud_reply = self._call_gemini_api(prompt)
            if cloud_reply:
                choices = [{"label": d["name"], "query": d["name"]} for d in retrieved_drugs[:4]]
                choices.append({"label": "Chọn nhóm khác", "query": "nhóm thuốc"})
                return cloud_reply, choices

        # ======================================================================
        # TÌNH HUỐNG 4: CHÀO HỎI & HỎI TÁC DỤNG PHỤ
        # ======================================================================
        symptoms = entities["symptoms"]
        demos = entities["demographics"]
        conditions = entities["conditions"]
        q_norm = normalize_text(user_query)

        if intent == "GREETING":
            reply_lines.append(
                "👋 **Xin chào! Mình là Trợ lý AI Dược phẩm Law GPT (Infranixx).**\n"
                "Hệ thống vận hành với kiến trúc AI Y tế 6 lớp: *Medical Guardrails*, *Medical NER*, *AI Drug Interaction Checker*, *Clinical Home-Care*, *RAG Semantic Retrieval* và *Generative Synthesis*.\n\n"
                "Bạn có thể:\n"
                "• Nhắn triệu chứng bệnh (*'đau đầu sốt cao'*, *'đau bụng buồn nôn'*).\n"
                "• Kiểm tra tương tác thuốc (*'uống Panadol với Ibuprofen có sao không?'*).\n"
                "• Hỏi cách chăm sóc (*'ngoài ra tôi nên làm gì?'*).\n"
                "• Hoặc bấm chọn nhanh các nhóm thuốc bên dưới nhé!"
            )
            choices = [{"label": d["name"], "query": d["name"]} for d in retrieved_drugs[:4]]
            choices.append({"label": "Kiểm tra tương tác thuốc", "query": "tương tác thuốc"})
            choices.append({"label": "Chọn nhóm khác", "query": "nhóm thuốc"})
            return "\n\n".join(reply_lines), choices

        if intent == "SIDE_EFFECTS" and retrieved_drugs:
            d = retrieved_drugs[0]
            reply_lines.append(f"⚠️ **Thông tin an toàn & Tác dụng phụ của {d['name']} ({d['active_ingredient']}):**\n")
            reply_lines.append(f"• **Tác dụng phụ thường gặp:** {d.get('side_effects', 'Chưa ghi nhận phản ứng bất lợi ở liều thông thường.')}")
            reply_lines.append(f"• **Chống chỉ định quan trọng:** {d.get('contraindications', 'Theo hướng dẫn sử dụng.')}")
            reply_lines.append("\n*Nếu gặp phản ứng bất thường hoặc khó thở, hãy ngừng dùng thuốc ngay và tham khảo ý kiến chuyên gia y tế.*")
            choices = [
                {"label": f"Xem {d['name']}", "query": d["name"]},
                {"label": "Hành động nên làm", "query": "ngoài ra tôi nên làm gì"},
                {"label": "Thuốc cùng nhóm", "query": d["group_name"]},
                {"label": "Chọn nhóm khác", "query": "nhóm thuốc"},
            ]
            return "\n".join(reply_lines), choices

        # ======================================================================
        # TÌNH HUỐNG 5: TƯ VẤN TRIỆU CHỨNG LÂM SÀNG (SYMPTOM CONSULTATION)
        # ======================================================================
        if symptoms:
            sym_str = ", ".join(symptoms)
            demo_str = f" ở đối tượng **{', '.join(demos)}**" if demos else ""
            cond_str = f" (Tiền sử: *{', '.join(conditions)}*)" if conditions else ""
            reply_lines.append(f"🩺 **Phân tích lâm sàng:** Tiếp nhận triệu chứng **{sym_str}**{demo_str}{cond_str}.")
            reply_lines.append("Dựa trên dữ liệu Dược thư Quốc gia (Cục Quản lý Dược – Bộ Y tế), các thuốc phù hợp gồm:")

            for d in retrieved_drugs[:3]:
                warn_prefix = f"\n  {d['_safety_warning']}" if d.get("_safety_warning") else ""
                reply_lines.append(
                    f"\n💊 **{d['name']}** ({d['active_ingredient']} - {d['strength']})\n"
                    f"  • *Dạng bào chế:* {d['form']}\n"
                    f"  • *Số đăng ký:* `{d['registration_no']}` ({d['manufacturer']})\n"
                    f"  • *Chỉ định:* {d.get('indications', '')}\n"
                    f"  • *Liều dùng tham khảo:* {d.get('dosage', 'Theo chỉ định của bác sĩ')}{warn_prefix}"
                )

            reply_lines.append("\n💡 *Lưu ý: Thông tin trên mang tính chất tham khảo. Hãy tham khảo ý kiến dược sĩ/bác sĩ trước khi dùng, đặc biệt với phụ nữ mang thai hoặc trẻ nhỏ.*")
            choices = [{"label": d["name"], "query": d["name"]} for d in retrieved_drugs[:4]]
            choices.append({"label": "Hành động nên làm", "query": "ngoài ra tôi nên làm gì"})
            choices.append({"label": "Chọn nhóm khác", "query": "nhóm thuốc"})
            return "\n".join(reply_lines), choices

        # ======================================================================
        # TÌNH HUỐNG 6: TRA CỨU ĐÍCH DANH 1 LOẠI THUỐC
        # ======================================================================
        is_direct_drug_search = False
        if retrieved_drugs:
            top_d = retrieved_drugs[0]
            name_norm = normalize_text(top_d["name"])
            active_norm = normalize_text(top_d["active_ingredient"])
            if name_norm in q_norm or any(part in q_norm for part in name_norm.split() if len(part) >= 4):
                is_direct_drug_search = True
            elif active_norm in q_norm:
                is_direct_drug_search = True

        if is_direct_drug_search and retrieved_drugs:
            d = retrieved_drugs[0]
            reply_lines.append(f"📋 **Hồ sơ thuốc trích xuất từ CSDL Dược: {d['name']}**\n")
            reply_lines.append(f"• **Hoạt chất:** {d['active_ingredient']} ({d['strength']})")
            reply_lines.append(f"• **Dạng bào chế:** {d['form']} – Hãng: {d['manufacturer']} ({d.get('country', 'Việt Nam')})")
            reply_lines.append(f"• **Số đăng ký Bộ Y tế:** `{d['registration_no']}`")
            reply_lines.append(f"• **Chỉ định:** {d.get('indications', '')}")
            reply_lines.append(f"• **Liều lượng tham khảo:** {d.get('dosage', '')}")
            if d.get("contraindications"):
                reply_lines.append(f"• **Chống chỉ định:** {d['contraindications']}")
            reply_lines.append("\n👉 *Bấm vào nút bên dưới để xem chi tiết tờ thông tin thuốc.*")
            choices = [
                {"label": f"Xem {d['name']}", "query": d["name"]},
                {"label": "Hành động nên làm", "query": "ngoài ra tôi nên làm gì"},
                {"label": "Thuốc cùng nhóm", "query": d["group_name"]},
                {"label": "Chọn nhóm khác", "query": "nhóm thuốc"}
            ]
            return "\n".join(reply_lines), choices

        # ======================================================================
        # TÌNH HUỐNG 7: FALLBACK HƯỚNG DẪN TƯƠNG TÁC
        # ======================================================================
        reply_lines.append(
            f"🤔 **Ghi nhận yêu cầu:** “*{user_query}*”.\n"
            "Hệ thống chưa nhận diện rõ triệu chứng hoặc tên thuốc từ câu hỏi của bạn.\n\n"
            "💡 **Để được hỗ trợ tốt nhất, bạn có thể:**\n"
            "• Miêu tả triệu chứng (ví dụ: *'đau đầu sốt cao'*, *'đau bụng buồn nôn'*).\n"
            "• Kiểm tra tương tác thuốc (ví dụ: *'uống Panadol với Ibuprofen có sao không'*).\n"
            "• Hoặc bấm chọn nhanh các nhóm thuốc bên dưới để xem danh mục chi tiết:"
        )
        choices = [{"label": d["name"], "query": d["name"]} for d in retrieved_drugs[:4]]
        choices.append({"label": "Kiểm tra tương tác thuốc", "query": "tương tác thuốc"})
        choices.append({"label": "Chọn nhóm khác", "query": "nhóm thuốc"})
        return "\n".join(reply_lines), choices


# ==============================================================================
# BỘ ĐIỀU PHỐI AI TỔNG THỂ (MAIN AI PIPELINE)
# ==============================================================================

class MedicalAIEngine:
    """Đầu mối tích hợp quy trình AI 6 lớp của Law GPT"""

    def __init__(self):
        self.guardrails = MedicalGuardrails()
        self.ner = MedicalNER()
        self.rag = MedicalRAG()
        self.llm = MedicalLLMGenerator()
        self.last_drug_id: str | None = None
        self.last_group_id: str | None = None

    def process(
        self,
        query: str,
        current_group: str | None = None,
        current_drug_id: str | None = None
    ) -> dict:
        # Cập nhật context memory
        if current_drug_id:
            self.last_drug_id = current_drug_id
        if current_group:
            self.last_group_id = current_group

        # 1. Kiểm tra An toàn & Nguy cấp (Guardrails)
        is_emergency, reason = self.guardrails.check_emergency(query)
        if is_emergency:
            return self.guardrails.build_emergency_response(reason)

        # 2. Nhận diện Thực thể Y tế & Ý định lâm sàng (Medical NER)
        entities = self.ner.extract_entities(query)

        # 3. Truy xuất ngữ nghĩa từ CSDL Dược (RAG Retrieval)
        retrieved_drugs = self.rag.retrieve(
            query=query,
            target_groups=entities["target_groups"],
            demographic_filter=entities["demographics"],
            top_k=4
        )

        # Lấy thông tin thuốc hiện tại đang xem (nếu có)
        active_drug_id = current_drug_id or self.last_drug_id
        current_drug = self.rag.get_drug_by_id(active_drug_id) if active_drug_id else None

        if current_drug and not current_group:
            current_group = current_drug.get("group_id")

        # 4. Sinh phản hồi AI có căn cứ tri thức (LLM / Clinical KB Generation)
        reply_text, choices = self.llm.generate(
            user_query=query,
            entities=entities,
            retrieved_drugs=retrieved_drugs,
            current_drug=current_drug,
            current_group=current_group
        )

        top_drug = retrieved_drugs[0]["name"] if retrieved_drugs else (current_drug["name"] if current_drug else None)
        if retrieved_drugs:
            self.last_drug_id = retrieved_drugs[0]["id"]
            self.last_group_id = retrieved_drugs[0].get("group_id")

        return {
            "reply": reply_text,
            "choices": choices,
            "ai_metadata": {
                "is_emergency": False,
                "provider": self.llm.provider,
                "intent": entities["intent"],
                "entities": entities,
                "retrieved_count": len(retrieved_drugs),
                "top_drug": top_drug
            }
        }


# Singleton instance
ai_engine = MedicalAIEngine()
