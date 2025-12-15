import json
import random
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# =========================
# 0) 설정
# =========================
DATA_DIR = Path(r"E:\document_slm_project\test_receipt")  # txt/json 페어가 있는 폴더로 변경
OUT_JSONL = Path(r"E:\document_slm_project\data_processe\train_5000.jsonl")  # 새로 만들 train_5000.jsonl

TARGET_N = 5000
SEED = 42
random.seed(SEED)

ALLOWED_TYPES = {"food_expenses", "materials_costs", "parking", "unknown"}

FIXED_INSTRUCTION = """다음 영수증 OCR 텍스트를 지출 내역 JSON으로 변환하시오.

출력 규칙:
1. 출력은 반드시 JSON 객체 1개만 하시오.
2. JSON 앞뒤로 어떤 문자도 출력하지 마시오.
   (설명, 문장, 주석, 코드블록, 자연어 모두 금지)
3. JSON 구조는 아래 스키마를 정확히 따르시오.
4. 스키마에 없는 키를 생성하지 마시오.
5. 알 수 없는 항목은 null 또는 빈 리스트로 처리하시오.

스키마:
{
  "payment_date": "YYYY-MM-DD",
  "type": "parking | materials_costs | food_expenses | unknown",
  "item": {
    "category": [
      {
        "quantity": number,
        "item_name": string,
        "amount": number
      }
    ],
    "payment_option": "card | cash",
    "total_cost": number,
    "car_plate_number": string (parking 타입일 때만)
  }
}

주의:
- food_expenses, materials_costs에서는 category는 반드시 리스트이다.
- category가 1개여도 반드시 리스트로 감싸시오.
- item_name 대신 name 을 사용하지 마시오.
- 설명을 출력하면 오답이다.
"""

# =========================
# 1) 유틸
# =========================
def normalize_basename(p: Path) -> str:
    # 20251208-112855 vs 20251208_112855 같은 케이스 정규화
    return p.stem.lower().replace(" ", "").replace("-", "_")

def load_pairs(data_dir: Path) -> List[Tuple[Path, Path]]:
    txt_map, json_map = {}, {}
    for p in data_dir.glob("*"):
        if not p.is_file():
            continue
        key = normalize_basename(p)
        if p.suffix.lower() == ".txt":
            txt_map[key] = p
        elif p.suffix.lower() == ".json":
            json_map[key] = p

    keys = sorted(set(txt_map) & set(json_map))
    if not keys:
        raise RuntimeError("매칭되는 txt/json 페어가 없습니다. 확장자 제외 파일명이 동일한지 확인하세요.")
    return [(txt_map[k], json_map[k]) for k in keys]

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore").strip()

def read_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8", errors="ignore"))

def normalize_amount(x: Any) -> Optional[int]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return int(x)
    s = str(x)
    s = s.replace(",", "").replace("원", "").strip()
    m = re.search(r"-?\d+", s)
    return int(m.group(0)) if m else None

def normalize_payment_date(x: Any) -> Optional[str]:
    if x is None:
        return None
    s = str(x).strip()
    # 이미 YYYY-MM-DD면 그대로
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    # YYYY.MM.DD / YYYY/MM/DD 같은 것들 처리
    s2 = re.sub(r"[./]", "-", s)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s2):
        return s2
    return s  # 알 수 없으면 원문 유지(학습 데이터가 이미 정상일 가능성이 높음)

# =========================
# 2) output 스키마 강제 정규화
# =========================
def to_target_schema(obj: Any) -> Dict[str, Any]:
    # obj가 dict가 아니면 unknown으로 처리
    if not isinstance(obj, dict):
        return {
            "payment_date": None,
            "type": "unknown",
            "item": {
                "category": [],
                "payment_option": "card",
                "total_cost": None
            }
        }

    t = obj.get("type")
    if t not in ALLOWED_TYPES:
        t = "unknown"

    payment_date = normalize_payment_date(obj.get("payment_date"))

    item_in = obj.get("item") if isinstance(obj.get("item"), dict) else {}

    payment_option = item_in.get("payment_option")
    if payment_option not in ("card", "cash"):
        payment_option = "card"

    total_cost = normalize_amount(item_in.get("total_cost"))
    if total_cost is None:
        total_cost = normalize_amount(item_in.get("amount"))

    # category 정규화
    category_in = item_in.get("category")
    category_out: List[Dict[str, Any]] = []

    if t in ("food_expenses", "materials_costs"):
        if isinstance(category_in, list):
            for x in category_in:
                if not isinstance(x, dict):
                    continue
                category_out.append({
                    "quantity": int(x.get("quantity", 1) or 1),
                    "item_name": str(x.get("item_name") or x.get("name") or "").strip(),
                    "amount": normalize_amount(x.get("amount"))
                })
        else:
            # 단품 형태를 리스트로 승격
            category_out.append({
                "quantity": int(item_in.get("quantity", 1) or 1),
                "item_name": str(item_in.get("item_name") or item_in.get("name") or "").strip(),
                "amount": normalize_amount(item_in.get("amount"))
            })

        # total_cost가 비었으면 category 합으로 채움(가능한 경우)
        if total_cost is None:
            s = 0
            ok = False
            for x in category_out:
                a = normalize_amount(x.get("amount"))
                if a is None:
                    continue
                ok = True
                s += int(a)
            total_cost = s if ok else None

        out = {
            "payment_date": payment_date,
            "type": t,
            "item": {
                "category": category_out,
                "payment_option": payment_option,
                "total_cost": total_cost
            }
        }
        return out

    if t == "parking":
        car_plate = item_in.get("car_plate_number")
        out = {
            "payment_date": payment_date,
            "type": "parking",
            "item": {
                "category": [],  # 스키마 고정(항상 리스트)
                "payment_option": payment_option,
                "total_cost": total_cost,
                "car_plate_number": car_plate
            }
        }
        return out

    # unknown
    out = {
        "payment_date": payment_date,
        "type": "unknown",
        "item": {
            "category": [],  # 스키마 고정(항상 리스트)
            "payment_option": payment_option,
            "total_cost": total_cost
        }
    }
    return out

# =========================
# 3) input 증강 (라벨 변조 X)
# =========================
def aug_whitespace_noise(s: str) -> str:
    lines = s.splitlines()
    out = []
    for ln in lines:
        if random.random() < 0.20:
            ln = re.sub(r"\s+", " ", ln).strip()
        if random.random() < 0.10:
            ln = " " * random.randint(0, 2) + ln
        out.append(ln)
        if random.random() < 0.05:
            out.append("")
    return "\n".join(out).strip()

def aug_common_ocr_typos(s: str) -> str:
    reps = [
        (",", ""), (":", ""), ("-", ""), ("·", "."),
        ("0", "O"), ("O", "0"),
    ]
    out = s
    for a, b in reps:
        if random.random() < 0.03:
            out = out.replace(a, b)
    return out

def aug_drop_random_tokens(s: str) -> str:
    toks = re.split(r"(\s+)", s)
    for i in range(len(toks)):
        if toks[i].strip() and random.random() < 0.01:
            toks[i] = ""
    return "".join(toks).strip()

def augment_input(s: str) -> str:
    out = s
    if random.random() < 0.7:
        out = aug_whitespace_noise(out)
    if random.random() < 0.4:
        out = aug_common_ocr_typos(out)
    if random.random() < 0.2:
        out = aug_drop_random_tokens(out)
    return out

# =========================
# 4) 합성 데이터 (정답도 같이 바뀌는 샘플)
#    - 스키마는 동일하게 유지
# =========================
CARD_COMPANIES = ["현대카드", "국민카드", "신한카드", "롯데카드", "우리카드"]
RESTAURANTS = ["맘스터치", "홍콩반점", "김밥천국", "돈까스클럽", "우동집"]
STORES = ["GS25 역삼점", "CU 신사역점", "세븐일레븐 서초점", "이마트24 강남점"]
PARKINGS = ["○○주차장", "시청 공영주차장", "역삼역 공영주차장", "강남 주차타워"]

FOOD_ITEMS = ["김치볶음밥", "데미그라스 돈까스", "치킨카레우동", "코카콜라 제로 350ml", "공깃밥"]
MATERIAL_ITEMS = ["네오셀 알카라인건전지 LR", "듀라셀 알카라인건전지 LR", "엘라스틴 맨인매트 클레이왁", "비타할로 일회용 치실 + 케이스"]

def random_datetime(start_year=2023, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    dt = start + timedelta(days=random.randint(0, delta.days),
                           seconds=random.randint(0, 24 * 3600 - 1))
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")

def random_korean_plate():
    first = random.choice([str(random.randint(10, 99)), str(random.randint(100, 999))])
    mid = random.choice(list("가나다라마바사아자차카타파하"))
    last = f"{random.randint(0, 9999):04d}"
    return f"{first}{mid}{last}"

def synth_food():
    store = random.choice(RESTAURANTS)
    date_str, time_str = random_datetime()
    card = random.choice(CARD_COMPANIES)
    n = random.randint(1, 4)

    items = []
    for _ in range(n):
        name = random.choice(FOOD_ITEMS)
        qty = random.randint(1, 2)
        unit = random.randint(1000, 12000)
        items.append({"name": name, "qty": qty, "amount": unit * qty})

    total = sum(i["amount"] for i in items)

    out = {
        "payment_date": date_str,
        "type": "food_expenses",
        "item": {
            "category": [{"quantity": i["qty"], "item_name": i["name"], "amount": i["amount"]} for i in items],
            "payment_option": "card",
            "total_cost": total
        }
    }
    out = to_target_schema(out)

    lines = [store, "", "결제정보", f"카드종류   {card}", f"거래일시   {date_str} {time_str}", "", "상품명 / 금액"]
    for it in items:
        lines.append(f"- {it['name']} x{it['qty']}  {it['amount']:,}원")
    lines.append(f"합계금액   {total:,}원")
    return "\n".join(lines), out

def synth_materials():
    store = random.choice(STORES)
    date_str, time_str = random_datetime()
    card = random.choice(CARD_COMPANIES)
    n = random.randint(1, 5)

    items = []
    for _ in range(n):
        name = random.choice(MATERIAL_ITEMS)
        qty = random.randint(1, 3)
        unit = random.randint(500, 10000)
        items.append({"name": name, "qty": qty, "amount": unit * qty})

    total = sum(i["amount"] for i in items)

    out = {
        "payment_date": date_str,
        "type": "materials_costs",
        "item": {
            "category": [{"quantity": i["qty"], "item_name": i["name"], "amount": i["amount"]} for i in items],
            "payment_option": "card",
            "total_cost": total
        }
    }
    out = to_target_schema(out)

    lines = [store, "", "결제정보", f"카드종류   {card}", f"거래일시   {date_str} {time_str}", "", "상품명 / 금액"]
    for it in items:
        lines.append(f"- {it['name']} x{it['qty']}  {it['amount']:,}원")
    lines.append(f"합계금액   {total:,}원")
    return "\n".join(lines), out

def synth_parking():
    store = random.choice(PARKINGS)
    date_str, time_str = random_datetime()
    card = random.choice(CARD_COMPANIES)
    plate = random_korean_plate()
    amount = random.choice([2000, 3000, 4000, 5000, 8000, 10000])

    out = {
        "payment_date": date_str,
        "type": "parking",
        "item": {
            "car_plate_number": plate,
            "payment_option": "card",
            "total_cost": amount
        }
    }
    out = to_target_schema(out)

    lines = [
        store, "",
        "결제정보",
        f"카드종류   {card}",
        f"거래일시   {date_str} {time_str}",
        "",
        "주차내역",
        f"차량번호   {plate}",
        f"합계금액   {amount:,}원"
    ]
    return "\n".join(lines), out

def synth_unknown():
    date_str, time_str = random_datetime()
    store = random.choice(RESTAURANTS + STORES)
    card = random.choice(CARD_COMPANIES)
    total = random.choice([40700, 61400, 9000, 12500, 18000, 25300])

    out = {
        "payment_date": date_str,
        "type": "unknown",
        "item": {
            "payment_option": "card",
            "total_cost": total
        }
    }
    out = to_target_schema(out)

    lines = [
        store, "",
        "카드 승인전표",
        f"카드종류   {card}",
        f"거래일시   {date_str} {time_str}",
        "",
        f"합계금액   {total:,}원"
    ]
    return "\n".join(lines), out

SYNTH_FUNCS = [synth_food, synth_materials, synth_parking, synth_unknown]

# =========================
# 5) 레코드 생성/저장
# =========================
def make_record(input_text: str, output_obj: Dict[str, Any]) -> Dict[str, Any]:
    t = output_obj.get("type")
    if t not in ALLOWED_TYPES:
        raise ValueError(f"type 허용 범위 밖: {t}")
    # output은 JSON 문자열로 저장 (JSON-only 학습 강화)
    output_str = json.dumps(output_obj, ensure_ascii=False)
    return {"instruction": FIXED_INSTRUCTION, "input": input_text, "output": output_str}

def main():
    pairs = load_pairs(DATA_DIR)

    # 1) 원본 페어 기반 base_records 만들기 (output은 스키마 강제)
    base_records = []
    for txt_path, json_path in pairs:
        inp = read_text(txt_path)
        raw_out = read_json(json_path)
        fixed_out = to_target_schema(raw_out)
        base_records.append(make_record(inp, fixed_out))

    if not base_records:
        raise RuntimeError("base_records가 비었습니다. DATA_DIR을 확인하세요.")

    # 2) 원본 먼저 넣기
    records = list(base_records)

    # 3) 원본 기반 input 증강(라벨 그대로)로 채우기
    while len(records) < TARGET_N:
        src = random.choice(base_records)
        records.append(make_record(augment_input(src["input"]), json.loads(src["output"])))

        # 너무 단조로우면 합성도 섞기
        if len(records) < TARGET_N and random.random() < 0.25:
            inp2, out2 = random.choice(SYNTH_FUNCS)()
            records.append(make_record(inp2, out2))

    random.shuffle(records)
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for r in records[:TARGET_N]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("완료:", str(OUT_JSONL), "개수:", TARGET_N)
    print("instruction 고정 여부:", "OK" if records[0]["instruction"] == FIXED_INSTRUCTION else "CHECK")
    # 샘플 1개 출력(검증용)
    print("샘플 output:", records[0]["output"])

if __name__ == "__main__":
    main()
