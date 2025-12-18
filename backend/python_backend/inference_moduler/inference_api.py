from inference_module import models_loader,run_ocr, run_slm
import numpy as np
import json
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
from fastapi.responses import JSONResponse

instruction = "다음 영수증 OCR 텍스트를 지출 내역 JSON으로 변환하시오.\n\n규칙:\n- 출력은 JSON 객체 1개만 하시오.\n- JSON 앞뒤로 어떤 문자도 출력하지 마시오.\n- 키는 payment_date, type, item 만 사용하시오.\n- item은 category(list), payment_option, total_cost, car_plate_number(parking만)를 포함하시오.\n- food_expenses/materials_costs의 category는 항상 리스트이며 각 원소는 quantity, item_name, amount를 가진다."

app = FastAPI()

tokenizer, ocr_model, slm_model = models_loader()

class PredictRequest(BaseModel):
    image_path: str
    max_new_tokens: int = 256
    temperature: float = 0.2

executor = ThreadPoolExecutor(max_workers=3)

def infer_one(image_path, max_new_tokens):
    ocr_output = run_ocr(ocr_model, image_path)
    if not ocr_output:
        return {"error": "OCR empty"}
    slm_output = run_slm(tokenizer, slm_model, instruction, ocr_output, max_new_tokens=max_new_tokens)
    return {"image_path": image_path, "slm_output": slm_output}

@app.post("/predict")
async def predict(payload: PredictRequest):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, infer_one, payload.image_path, payload.max_new_tokens)
    return result


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {
        "service": "ocr-path-api",
        "engine": "PaddleOCR, qwen2.5 3B QLoRA tuning",
        "lang": "korean",
        "version": "python fastAPI",
    }