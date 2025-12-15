import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL = r"E:\document_slm_project\model\base_model"
ADAPTER_PATH = r"E:\document_slm_project\slm_train\qwen2.5-3b-receipt-qlora"  # 최종 LoRA 폴더


def load_tokenizer_and_model():
    # 토크나이저: 학습 때 저장한 걸 그대로 사용
    tokenizer = AutoTokenizer.from_pretrained(
        ADAPTER_PATH,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 4bit QLoRA와 동일한 설정
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
    )

    # 베이스 Qwen 모델 로드
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quant_config,
        device_map="auto",
        trust_remote_code=True,
    )

    # LoRA 어댑터 적용
    model = PeftModel.from_pretrained(
        base_model,
        ADAPTER_PATH,
    )
    model.eval()
    return tokenizer, model


def build_prompt(instruction: str, inp: str) -> str:
    # 학습 때 쓴 포맷 그대로 맞춰줌
    text = (
        "[INSTRUCTION]\n"
        f"{instruction}\n\n"
        "[INPUT]\n"
        f"{inp}\n\n"
        "[OUTPUT]\n"
    )
    return text


def generate_receipt_json(instruction: str, inp: str, max_new_tokens: int = 512) -> str:
    tokenizer, model = load_tokenizer_and_model()
    prompt = build_prompt(instruction, inp)

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
    ).to(model.device)

    with torch.inference_mode():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,          # 일단 greedy로
            temperature=0.0,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )

    full_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

    # 프롬프트 부분 잘라내고 [OUTPUT] 뒤에 나온 것만 사용
    if "[OUTPUT]" in full_text:
        result = full_text.split("[OUTPUT]")[-1].strip()
    else:
        result = full_text.strip()
    return result


if __name__ == "__main__":
    instruction = "다음 영수증 OCR 텍스트를 지출 내역 JSON으로 변환하시오.\n\n규칙:\n- 출력은 JSON 객체 1개만 하시오.\n- JSON 앞뒤로 어떤 문자도 출력하지 마시오.\n- 키는 payment_date, type, item 만 사용하시오.\n- item은 category(list), payment_option, total_cost, car_plate_number(parking만)를 포함하시오.\n- food_expenses/materials_costs의 category는 항상 리스트이며 각 원소는 quantity, item_name, amount를 가진다."

    # 테스트용 입력 영수증 텍스트 예시 (원하는 걸로 바꿔도 됨)
    input_text = """재미있는\n일상\nGS23\nH\nXX\nX\nunlabl\nGS25한강뚝섬1점\n0809995425\nOBR\n7394501132\n광진구 자양\n서울\n427-13번지1\n2025/12/15이*명\nN0:26906\n*정부방침에\n의해\n잘하서아 하며,\n2\n카드\n30\n(01214일)0내\n카드와\n'가능합니다\n시\n선도민간상포\n지오\n그란데라떼\n1\n2,350\n압계수량?\n2,350\n1\n과세 매출\n2,136\n부가세\n214\n2,350\n합\n계\n신 용 카\n2,350\n신용카드 전크(고객용)\n카드번오\n5327-505308\n사용\n액\nl\n2.350원\n0 (매입사:오완카트)\n인번\n호\n24108801\n25712/15 15:47:11\n편의절\n1등\n대\n동네\nGS26\n2
"""

    result = generate_receipt_json(instruction, input_text)
    print("모델 출력:")
    print(result)

    # 진짜 JSON 형식인지 파싱 테스트
    try:
        parsed = json.loads(result)
        print("\nJSON 파싱 성공:")
        print(parsed)
    except Exception as e:
        print("\nJSON 파싱 실패:", e)
