import json
from dataclasses import dataclass
from typing import Dict, List

import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig
from transformers import TrainingArguments
from transformers import TrainerCallback

import json
import os
from transformers import TrainerCallback

class EntropySaveStopCallback(TrainerCallback):
    """
    조기종료 콜백
    1. 지정한 entropy 달성시 저장 후 학습 종료
    2. 학습률 (loss, lr, acc 등등)을 txt로 저장 -> ./checkpoint_meta 안에 저장함
    """
    def __init__(self, entropy_threshold=0.22, meta_dir="checkpoint_meta"):
        self.entropy_threshold = entropy_threshold
        self.meta_dir = meta_dir
        os.makedirs(meta_dir, exist_ok=True)

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not logs:
            return

        entropy = logs.get("entropy")
        lr = logs.get("learning_rate")

        if entropy is None or lr is None:
            return

        if entropy < self.entropy_threshold:
            step = state.global_step
            epoch = state.epoch

            print(
                f"[CALLBACK] entropy={entropy:.4f} | lr={lr:.6e} "
                f"| step={step} | epoch={epoch:.3f}"
            )

            # 메타 정보 저장
            meta = {
                "global_step": step,
                "epoch": float(epoch),
                "entropy": float(entropy),
                "learning_rate": float(lr),
            }

            meta_path = os.path.join(
                self.meta_dir, f"best_checkpoint_step_{step}.json"
            )
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)

            # 저장 + 종료
            control.should_save = True
            control.should_training_stop = True




# 1. 기본 설정
MODEL_NAME = r"E:\document_slm_project\model\base_model"  # 허깅페이스 경로 기준
DATA_PATH = r"E:\document_slm_project\data_processe\train_5000.jsonl"
OUTPUT_DIR = "./qwen2.5-3b-receipt-qlora"


# 2. 데이터 로딩
def load_receipt_dataset(path: str):
    dataset = load_dataset("json", data_files={"train": path})
    # output이 dict면 string으로 변환
    def ensure_output_str(example):
        if not isinstance(example["output"], str):
            example["output"] = json.dumps(example["output"], ensure_ascii=False, default=str)
        return example

    dataset = dataset.map(ensure_output_str)
    return dataset


# 3. 프롬프트 포맷 함수
def format_example(example: Dict) -> str:
    instruction = example.get("instruction", "").strip()
    inp = example.get("input", "").strip()
    out = example.get("output", "").strip()

    text = (
        "[INSTRUCTION]\n"
        f"{instruction}\n\n"
        "[INPUT]\n"
        f"{inp}\n\n"
        "[OUTPUT]\n"
        f"{out}"
    )
    return text


# 4. 토크나이저 및 모델 로딩 (4bit QLoRA)
def load_tokenizer_and_model():
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True
    )
    # Qwen 쪽은 pad_token 없을 수 있어서 EOS로 맞춰줌
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 4bit 양자화 설정
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=quant_config,
        device_map="auto",
        trust_remote_code=True,
    )

    return tokenizer, model


# 5. LoRA 설정
def apply_lora(model):
    lora_config = LoraConfig(
        r=64,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model


def main():
    # 데이터
    dataset = load_receipt_dataset(DATA_PATH)

    # prompt 필드 추가
    def add_text_field(example):
        example["text"] = format_example(example)
        return example

    dataset = dataset.map(add_text_field)

    # 토크나이저 + 모델
    tokenizer, base_model = load_tokenizer_and_model()
    model = apply_lora(base_model)

    # 6. 학습 인자 설정
    training_args = SFTConfig(
        # Trainer 공통 옵션
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=5e-5,
        num_train_epochs=2,
        fp16=False,
        bf16=False,
        logging_steps=10,
        save_steps=10,
        save_total_limit=3,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        report_to="none",

        # SFT 전용 옵션 (원래 SFTTrainer 에 주던 것)
        # max_seq_length=2048,
        packing=False,
        dataset_text_field="text",
    )


    # 7. SFTTrainer 사용
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        processing_class=tokenizer,
        callbacks=[
            EntropySaveStopCallback(
                entropy_threshold=0.22,
                meta_dir="./checkpoint_meta"
            )
        ],
    )

    trainer.train()

    # 8. LoRA 어댑터 저장
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("학습 완료 & 저장:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
