import torch
import json
import re
import os
import numpy as np
from paddleocr import PaddleOCR
from peft import PeftModel
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

BASE_MODEL = r"E:\document_slm_project\model-train\model\base_model"
ADAPTER_PATH = r"E:\document_slm_project\model-train\model\qwen2.5-3b-receipt-qlora"

#=====================
# OCR Model load
#=====================

def load_ocr():
    ocr = PaddleOCR(
            lang="korean",
            use_textline_orientation=True
        )
    return ocr

#=====================
# SLM Model load
#=====================

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

#=====================
# Models Loader
#=====================

def models_loader():
    tokenizer, slm_model = load_tokenizer_and_model()
    ocr_model = load_ocr()
    return tokenizer, ocr_model, slm_model


#=====================
# OCR inference
#=====================

def normalize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text

def run_ocr(ocr, img_path: str, conf_threshold: float = 0.60) -> str:
    if not os.path.exists(img_path):
        print("❌❌❌❌❌❌❌❌❌ 이미지 경로 없음:", img_path)
        return ""

    result = ocr.ocr(img_path)

    if not result or not isinstance(result, list):
        print("❌❌❌❌❌❌❌❌❌ OCR 결과 비어 있음")
        return ""

    data = result[0]
    texts = data.get("rec_texts", [])
    scores = data.get("rec_scores", [])
    boxes = data.get("rec_boxes", None)
    doc_prep = data.get("doc_preprocessor_res", {})

    if not texts:
        print("❌❌❌❌❌❌❌❌❌ 인식된 텍스트 없음")
        return ""

    angle = doc_prep.get("angle", 0) if isinstance(doc_prep, dict) else 0

    if boxes is not None:
        boxes = np.array(boxes)
        indices = list(range(len(texts)))

        if angle in [180, -180]:
            indices.sort(key=lambda i: (-boxes[i][1], boxes[i][0]))
        else:
            indices.sort(key=lambda i: (boxes[i][1], boxes[i][0]))
    else:
        indices = list(range(len(texts)))

    filtered_lines = []

    for out_idx, i in enumerate(indices, start=1):
        raw_text = texts[i]
        score = scores[i] if i < len(scores) else 0.0
        clean_text = normalize_text(raw_text)

        if not clean_text:
            continue

        if score < conf_threshold and len(clean_text) <= 3:
            continue

        filtered_lines.append(clean_text)

    if not filtered_lines:
        return ""

    slm_text = "\\n".join(filtered_lines)

    return slm_text


#=====================
# SLM inference
#=====================

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

def run_slm(tokenizer, model, instruction: str, inp: str, max_new_tokens: int = 512) -> str:
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

    try:
        parsed = json.loads(result)
    except Exception as e:
        parsed = None
        print("\nJSON 파싱 실패:", e)
        print(result)
    return parsed