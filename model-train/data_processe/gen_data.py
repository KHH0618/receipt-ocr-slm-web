import json
import random
import re
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(r"E:\document_slm_project\test_receipt")
OUT_PATH = Path(r"E:\document_slm_project\data_processe\train_5000.jsonl")
TARGET_N = 5000
random.seed(42)

INSTRUCTION = """다음 영수증 OCR 텍스트를 지출 내역 JSON으로 변환하시오.

규칙:
- 출력은 JSON 객체 1개만 하시오.
- JSON 앞뒤로 어떤 문자도 출력하지 마시오.
- 키는 payment_date, type, item 만 사용하시오.
- item은 category(list), payment_option, total_cost, car_plate_number(parking만)를 포함하시오.
- food_expenses/materials_costs의 category는 항상 리스트이며 각 원소는 quantity, item_name, amount를 가진다.
- item_name 대신 name을 쓰지 마시오.
"""

ALLOWED_TYPES = {"food_expenses", "materials_costs", "parking", "unknown"}

def extract_date_from_text(text: str):
    m = re.search(r"(20\d{2})[./-](\d{2})[./-](\d{2})", text)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

def normalize_amount(x):
    if x is None:
        return None
    if isinstance(x, int):
        return x
    s = str(x).replace(",", "").replace("원", "")
    m = re.search(r"\d+", s)
    return int(m.group()) if m else None

def to_schema(raw, input_text):
    if not isinstance(raw, dict):
        raw = {}

    t = raw.get("type")
    if t not in ALLOWED_TYPES:
        t = "unknown"

    payment_date = raw.get("payment_date") or extract_date_from_text(input_text)

    item_in = raw.get("item", {}) if isinstance(raw.get("item"), dict) else {}

    payment_option = item_in.get("payment_option")
    if payment_option not in ("card", "cash"):
        payment_option = "card"

    total_cost = normalize_amount(item_in.get("total_cost"))
    if total_cost is None:
        total_cost = normalize_amount(item_in.get("amount"))

    out = {
        "payment_date": payment_date,
        "type": t,
        "item": {
            "category": [],
            "payment_option": payment_option,
            "total_cost": total_cost
        }
    }

    if t in ("food_expenses", "materials_costs"):
        cat = item_in.get("category")
        if isinstance(cat, list):
            for x in cat:
                if not isinstance(x, dict):
                    continue
                out["item"]["category"].append({
                    "quantity": int(x.get("quantity", 1)),
                    "item_name": x.get("item_name") or "",
                    "amount": normalize_amount(x.get("amount"))
                })
        else:
            out["item"]["category"].append({
                "quantity": int(item_in.get("quantity", 1)),
                "item_name": item_in.get("item_name") or "",
                "amount": normalize_amount(item_in.get("amount"))
            })

    if t == "parking":
        out["item"]["car_plate_number"] = item_in.get("car_plate_number")

    return out

def load_pairs():
    txts = {p.stem: p for p in DATA_DIR.glob("*.txt")}
    jsons = {p.stem: p for p in DATA_DIR.glob("*.json")}
    keys = sorted(set(txts) & set(jsons))
    return [(txts[k], jsons[k]) for k in keys]

def main():
    pairs = load_pairs()
    records = []

    for txt_p, json_p in pairs:
        input_text = txt_p.read_text(encoding="utf-8", errors="ignore").strip()
        raw = json.loads(json_p.read_text(encoding="utf-8", errors="ignore"))
        fixed = to_schema(raw, input_text)
        records.append({
            "instruction": INSTRUCTION,
            "input": input_text,
            "output": json.dumps(fixed, ensure_ascii=False)
        })

    while len(records) < TARGET_N:
        records.append(random.choice(records))

    random.shuffle(records)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in records[:TARGET_N]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("train_5000.jsonl 생성 완료:", len(records[:TARGET_N]))

if __name__ == "__main__":
    main()
