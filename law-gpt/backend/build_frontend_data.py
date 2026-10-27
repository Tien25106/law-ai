"""Law GPT – Tra cứu thuốc | Infranixx

Đọc dữ liệu (CSV) bằng pandas, thống kê bằng numpy, vẽ biểu đồ bằng matplotlib
và xuất ra thư mục frontend/ để upload thẳng lên hosting (không cần server Python).

    python backend/build_frontend_data.py

Đầu ra:
    frontend/js/sample-data.js          dữ liệu cho giao diện (window.LAWGPT_DATA)
    frontend/img/charts/*.png           biểu đồ bản sáng và bản tối

Hiện chạy trên data/drugs_sample.csv (DỮ LIỆU MẪU). Khi đã thu thập dữ liệu thật
từ Cục Quản lý Dược, đổi DRUGS_CSV sang file mới và đặt IS_SAMPLE = False.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # vẽ ra file, không cần cửa sổ

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
GROUPS_CSV = ROOT / "data" / "groups.csv"
DRUGS_CSV = ROOT / "data" / "drugs_sample.csv"
OUT_JS = ROOT / "frontend" / "js" / "sample-data.js"
OUT_CHARTS = ROOT / "frontend" / "img" / "charts"
IS_SAMPLE = True

REQUIRED_DRUG_COLUMNS = [
    "id", "name", "active_ingredient", "strength", "form",
    "group_id", "manufacturer", "registration_no",
]

# Màu biểu đồ: một màu cho một chuỗi số liệu, có bản sáng và bản tối.
THEMES = {
    "light": {"ink": "#14231F", "muted": "#5E6E69", "line": "#CBD5D1", "bar": "#0B6B52"},
    "dark": {"ink": "#E7F0EC", "muted": "#A8BBB4", "line": "#27403A", "bar": "#4FC3A1"},
}


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    groups = pd.read_csv(GROUPS_CSV, dtype=str, encoding="utf-8-sig").fillna("")
    drugs = pd.read_csv(DRUGS_CSV, dtype=str, encoding="utf-8-sig").fillna("")

    missing = [c for c in REQUIRED_DRUG_COLUMNS if c not in drugs.columns]
    if missing:
        sys.exit(f"Thiếu cột trong {DRUGS_CSV.name}: {', '.join(missing)}")

    drugs = drugs.apply(lambda col: col.str.strip())
    groups = groups.apply(lambda col: col.str.strip())

    if drugs["id"].duplicated().any():
        sys.exit("Có id thuốc bị trùng: " + ", ".join(drugs.loc[drugs["id"].duplicated(), "id"]))
    unknown = ~drugs["group_id"].isin(groups["id"])
    if unknown.any():
        sys.exit("group_id không có trong groups.csv: " + ", ".join(drugs.loc[unknown, "group_id"].unique()))
    return groups, drugs


def write_data_js(groups: pd.DataFrame, drugs: pd.DataFrame) -> None:
    payload = {
        "meta": {"isSample": IS_SAMPLE, "updatedAt": None},
        "groups": [
            {"id": r.id, "name": r.name, "hue": int(r.hue)} for r in groups.itertuples()
        ],
        "drugs": [
            {
                "id": r.id,
                "name": r.name,
                "activeIngredient": r.active_ingredient,
                "strength": r.strength,
                "form": r.form,
                "group": r.group_id,
                "manufacturer": r.manufacturer,
                "registrationNo": r.registration_no,
            }
            for r in drugs.itertuples()
        ],
    }
    header = (
        "/* FILE TỰ SINH bởi backend/build_frontend_data.py – đừng sửa tay.\n"
        " * Sửa data/*.csv rồi chạy lại script.\n"
        " * Đây là DỮ LIỆU MẪU, không phải dữ liệu thật từ Cục Quản lý Dược. */\n"
    )
    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    OUT_JS.write_text(
        header + "window.LAWGPT_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


def ranked(counts: pd.Series) -> tuple[list[str], np.ndarray]:
    """Sắp xếp giảm dần theo số lượng (ổn định để kết quả không đổi giữa các lần chạy)."""
    values = counts.to_numpy(dtype=int)
    order = np.argsort(-values, kind="stable")
    return [str(counts.index[i]) for i in order], values[order]


def hbar(labels: list[str], values: np.ndarray, stem: str) -> None:
    """Biểu đồ cột ngang một màu; ghi số ngay cuối cột thay cho trục số."""
    plt.rcParams["font.family"] = "DejaVu Sans"  # có đủ dấu tiếng Việt
    n = len(labels)
    vmax = max(int(values.max()), 1)
    for mode, t in THEMES.items():
        fig, ax = plt.subplots(figsize=(5.0, 0.42 * n + 0.4))
        y = np.arange(n)
        ax.barh(y, values, height=0.5, color=t["bar"])
        ax.set_yticks(y, labels=labels)
        ax.invert_yaxis()
        ax.set_xlim(0, vmax * 1.15)
        for yi, v in zip(y, values):
            ax.text(v + vmax * 0.02, yi, str(int(v)), va="center", ha="left",
                    color=t["ink"], fontsize=11, fontweight="bold")
        ax.tick_params(axis="y", length=0, colors=t["ink"], labelsize=11)
        ax.xaxis.set_visible(False)
        for side in ("top", "right", "bottom"):
            ax.spines[side].set_visible(False)
        ax.spines["left"].set_color(t["line"])
        OUT_CHARTS.mkdir(parents=True, exist_ok=True)
        fig.savefig(OUT_CHARTS / f"{stem}-{mode}.png", dpi=200, transparent=True,
                    bbox_inches="tight", pad_inches=0.08)
        plt.close(fig)


def main() -> None:
    groups, drugs = load()
    write_data_js(groups, drugs)

    by_group = drugs.groupby("group_id").size().reindex(groups["id"], fill_value=0)
    by_group.index = groups.set_index("id").loc[by_group.index, "name"]
    hbar(*ranked(by_group), stem="groups")

    by_form = drugs["form"].replace("", "Chưa rõ").value_counts().sort_index()
    hbar(*ranked(by_form), stem="forms")

    share = np.round(by_group.to_numpy() / max(len(drugs), 1) * 100, 1)
    print(f"Đã tạo {OUT_JS.relative_to(ROOT)} và {len(THEMES) * 2} biểu đồ trong {OUT_CHARTS.relative_to(ROOT)}")
    print(f"{len(drugs)} thuốc, {len(groups)} nhóm, {by_form.size} dạng bào chế; "
          f"nhóm lớn nhất chiếm {share.max()}%")


if __name__ == "__main__":
    main()
