import datetime
import json
import random
import re
from typing import Optional, Dict, Any, List, Tuple

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# =========================
# 설정
# =========================
BASE_MODEL_DIR = r"E:\document_slm_project\model\base_model"
MODEL_DIR = r"E:\document_slm_project\slm_train\qwen2.5-3b-receipt-qlora"
TRAIN_JSONL = r"E:\document_slm_project\data_processe\train_5000.jsonl"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAX_NEW_TOKENS = 256
random.seed(42)

ALLOWED_TYPES = {"parking", "materials_costs", "food_expenses", "unknown"}
ALLOWED_PAY_OPT = {"card", "cash"}

# OCR 노이즈 강도(0~1): 0.05~0.12 정도가 "살짝 깨짐" 수준
OCR_NOISE_LEVEL = 0.5

# =========================
# 모델 로드
# =========================
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR,
    trust_remote_code=True,
    torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
).to(DEVICE)
model.eval()

# =========================
# 프롬프트 (chat template 우선)
# =========================
def build_prompt(instruction: str, input_text: str) -> str:
    messages = [
        {"role": "system", "content": "You are a strict JSON generator. Output ONLY a single JSON object. No extra text."},
        {"role": "user", "content": f"{instruction}\n\ninput:\n{input_text}\n\noutput:"},
    ]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except Exception:
        return f"{instruction}\n\ninput:\n{input_text}\n\noutput:\n"

# =========================
# 생성
# =========================
def generate_raw(prompt: str) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )

    prompt_len = inputs["input_ids"].shape[-1]
    gen_ids = out[0][prompt_len:]
    decoded = tokenizer.decode(gen_ids, skip_special_tokens=True)
    return decoded.strip()

# =========================
# JSON 추출
# =========================
def _strip_bad_chars(s: str) -> str:
    s = s.replace("\ufeff", "")
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    return s

def _remove_trailing_commas(s: str) -> str:
    s = re.sub(r",\s*\]", "]", s)
    s = re.sub(r",\s*\}", "}", s)
    return s

def extract_first_json_object(text: str) -> Optional[Dict[str, Any]]:
    text = _strip_bad_chars(text).strip()
    low = text.lower()
    for key in ["output:", "(output)", "[output]"]:
        k = key.lower()
        if k in low:
            idx = low.find(k)
            text = text[idx + len(key):].strip()
            low = text.lower()

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_str = False
    esc = False

    for i in range(start, len(text)):
        ch = text[i]

        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue

        if ch == '"':
            in_str = True
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                blob = text[start:i+1]
                blob = _remove_trailing_commas(blob)
                try:
                    obj = json.loads(blob)
                    return obj if isinstance(obj, dict) else None
                except Exception:
                    return None
    return None

# =========================
# 스키마 검증 (name 기준)
# =========================
def schema_ok_name(obj: Dict[str, Any]) -> bool:
    if not isinstance(obj, dict):
        return False
    if "payment_date" not in obj or "type" not in obj or "item" not in obj:
        return False
    if obj["type"] not in ALLOWED_TYPES:
        return False

    item = obj["item"]
    if not isinstance(item, dict):
        return False
    for k in ["category", "payment_option", "total_cost"]:
        if k not in item:
            return False
    if item["payment_option"] not in ALLOWED_PAY_OPT:
        return False
    if not isinstance(item["category"], list):
        return False

    for row in item["category"]:
        if not isinstance(row, dict):
            return False
        if "quantity" not in row or "name" not in row or "amount" not in row:
            return False

    if obj["type"] == "parking":
        if "car_plate_number" not in item:
            return False

    return True

# =========================
# 정합성 체크(가벼운 유효성)
# =========================
def try_int(x):
    try:
        if isinstance(x, bool):
            return None
        if isinstance(x, (int, float)):
            return int(x)
        if isinstance(x, str):
            t = re.sub(r"[^0-9]", "", x)
            return int(t) if t else None
    except Exception:
        return None
    return None

def sanity_score(obj: Dict[str, Any]) -> Tuple[int, List[str]]:
    """
    0~100 가벼운 점수:
    - category 합계와 total_cost가 일치/근접
    - date 형식
    - type/payment_option 정상
    """
    problems = []
    score = 100

    # date
    d = obj.get("payment_date")
    if not isinstance(d, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        problems.append("bad_payment_date")
        score -= 15

    # total vs sum(category)
    item = obj.get("item", {})
    total = try_int(item.get("total_cost"))
    if total is None:
        problems.append("missing_total_cost")
        score -= 20
    else:
        s = 0
        for r in item.get("category", []):
            amt = try_int(r.get("amount"))
            if amt is None:
                score -= 5
                problems.append("missing_amount")
            else:
                s += amt
        if s > 0:
            # 완전 일치 or 5% 이내면 OK
            diff = abs(total - s)
            if diff == 0:
                pass
            elif diff / max(total, 1) <= 0.05:
                score -= 5
                problems.append(f"total_mismatch_small(diff={diff})")
            else:
                score -= 25
                problems.append(f"total_mismatch_big(sum={s}, total={total})")

    if score < 0:
        score = 0
    return score, problems

# =========================
# OCR 노이즈 주입(살짝 깨짐 시뮬레이션)
# =========================
def inject_ocr_noise(text: str, p: float = 0.08) -> str:
    """
    살짝 깨진 OCR을 흉내:
    - 공백/개행 랜덤 삭제/추가
    - 숫자/한글 비슷한 문자 치환(0/O, 1/I, 5/S 등)
    - 일부 문자 누락
    """
    if p <= 0:
        return text

    subs = {
        "0": "O",
        "1": "I",
        "5": "S",
        "8": "B",
        "O": "0",
        "I": "1",
        ",": "",
        "원": "윈",   # 흔한 오인식
        "카드": "카드 ",
    }

    out = []
    for ch in text:
        r = random.random()
        if r < p * 0.20:
            # 문자 누락
            continue
        if r < p * 0.45 and ch in subs:
            out.append(subs[ch])
        elif r < p * 0.65 and ch == " ":
            # 공백 제거
            continue
        elif r < p * 0.80 and ch == "\n":
            # 개행 제거 -> 한 줄로 붙어버림
            continue
        else:
            out.append(ch)

        # 랜덤 추가 공백
        if random.random() < p * 0.10:
            out.append(" ")

    # 일부 케이스: "2024-03-06" -> "2024-3-06" 같은 형식 깨짐
    s = "".join(out)
    if random.random() < p * 0.30:
        s = re.sub(r"-(0)(\d)-", r"-\2-", s)  # 03 -> 3
    return s

# =========================
# 신규 OCR input 생성(정답도 같이 만들어 비교 가능)
# =========================
def generate_new_ocr_input_with_gt() -> Tuple[str, Dict[str, Any]]:
    stores = ["GS25 역삼점", "CU 논현점", "이마트24 강남점", "돈까스클럽", "김밥천국 역삼점"]
    cards = ["국민카드", "우리카드", "신한카드", "삼성카드"]
    dates = ["2024-03-06", "2025-01-17", "2023-11-23", "2025-10-17"]

    items_pool = [
        ("코카콜라 제로 350ml", 1, 1900),
        ("삼각김밥", 2, 1600),
        ("듀라셀 알카라인건전지 LR", 1, 2000),
        ("네오셀 알카라인건전지 LR", 1, 2000),
        ("데미그라스 돈까스", 1, 11000),
        ("치킨카레우동", 1, 10500),
    ]

    store = random.choice(stores)
    card = random.choice(cards)
    date = random.choice(dates)

    k = random.randint(1, 3)
    picked = random.sample(items_pool, k)

    lines = []
    cat = []
    total = 0
    for name, qty, unit in picked:
        amt = qty * unit
        total += amt
        lines.append(f"{name}  {qty}  {amt:,}원")
        cat.append({"quantity": qty, "name": name, "amount": amt})

    ocr = f"""{store}

카드 승인전표
카드종류   {card}
거래일시   {date} 12:34:56

품목
{chr(10).join(lines)}

합계금액   {total:,}원
"""

    gt = {
        "payment_date": date,
        "type": "food_expenses" if "돈까스" in ocr or "우동" in ocr or "김밥" in ocr else "materials_costs",
        # 위 type GT는 단순룰이라, 여기선 테스트 목적상 food_expenses로 고정해도 됨
        "type": "food_expenses",
        "item": {
            "category": cat,
            "payment_option": "card",
            "total_cost": total,
        }
    }
    return ocr, gt

# =========================
# 실행
# =========================
def run_case(instruction: str, input_text: str, tag: str) -> Tuple[Optional[Dict[str, Any]], str]:
    prompt = build_prompt(instruction, input_text)
    raw = generate_raw(prompt)

    print("\n" + "=" * 120)
    print(f"[{tag}] RAW GENERATED (before parsing)")
    print(prompt)
    print("-" * 120)
    print(raw)
    print("=" * 120)

    obj = extract_first_json_object(raw)
    print(f"[{tag}] PARSED:", obj)

    if obj is None:
        return None, raw

    ok = schema_ok_name(obj)
    print(f"[{tag}] SCHEMA_OK(name):", ok)

    if ok:
        score, probs = sanity_score(obj)
        print(f"[{tag}] SANITY_SCORE:", score, "|", probs)

    return obj, raw

def main():
    print("\n\n########## LOAD TRAIN INSTRUCTION ##########\n")
    with open(TRAIN_JSONL, encoding="utf-8") as f:
        train_samples = [json.loads(x) for x in f.readlines()[:3]]
    base_instruction = train_samples[0]["instruction"]

    print("\n\n########## NEW OCR INPUT TEST (clean vs noisy) ##########\n")
    n = 10
    success_clean = 0
    success_noisy = 0

    for i in range(1, n + 1):
        clean_inp, gt = generate_new_ocr_input_with_gt()
        noisy_inp = inject_ocr_noise(clean_inp, p=OCR_NOISE_LEVEL)

        pred_clean, _ = run_case(base_instruction, clean_inp, f"NEW-CLEAN-{i}")
        pred_noisy, _ = run_case(base_instruction, noisy_inp, f"NEW-NOISY-{i}")

        if pred_clean is not None and schema_ok_name(pred_clean):
            success_clean += 1
        if pred_noisy is not None and schema_ok_name(pred_noisy):
            success_noisy += 1

        # GT도 같이 출력해두면 디버깅 쉬움
        print(f"[GT-{i}]:", json.dumps(gt, ensure_ascii=False))

    print("\n\n########## SUMMARY ##########")
    print(f"clean schema_ok: {success_clean}/{n}")
    print(f"noisy schema_ok: {success_noisy}/{n}")
    print(f"noise_level: {OCR_NOISE_LEVEL}")

if __name__ == "__main__":
    now = datetime.datetime.now()
    main()
    finish = datetime.datetime.now()
    print(f"finish: {finish - now}")
