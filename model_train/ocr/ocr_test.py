from paddleocr import PaddleOCR
import os
import numpy as np
import re


def normalize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def run_ocr_for_slm(img_path: str, conf_threshold: float = 0.60) -> str:
    if not os.path.exists(img_path):
        print("❌ 이미지 경로 없음:", img_path)
        return ""

    ocr = PaddleOCR(
        lang="korean",
        use_textline_orientation=True
    )

    result = ocr.ocr(img_path)

    if not result or not isinstance(result, list):
        print("❌ OCR 결과 비어 있음")
        return ""

    data = result[0]
    texts = data.get("rec_texts", [])
    scores = data.get("rec_scores", [])
    boxes = data.get("rec_boxes", None)
    doc_prep = data.get("doc_preprocessor_res", {})

    if not texts:
        print("❌ 인식된 텍스트 없음")
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

    print("\n=== OCR DEBUG OUTPUT ===")
    filtered_lines = []

    for out_idx, i in enumerate(indices, start=1):
        raw_text = texts[i]
        score = scores[i] if i < len(scores) else 0.0
        clean_text = normalize_text(raw_text)

        if not clean_text:
            continue

        if score < conf_threshold and len(clean_text) <= 3:
            print(f"[{out_idx}] (SKIP) {clean_text} (conf={score:.3f})")
            continue

        print(f"[{out_idx}] {clean_text} (conf={score:.3f})")
        filtered_lines.append(clean_text)

    if not filtered_lines:
        print("❌ 필터링 후 남은 텍스트 없음")
        return ""

    # 👉 핵심: \n 이 실제 줄바꿈이 아니라 문자로 출력되게 join
    slm_text = "\\n".join(filtered_lines)

    print("\n=== 📌 FINAL SLM OUTPUT (복붙용) ===")
    print(slm_text)

    return slm_text


if __name__ == "__main__":
    base_path = r"E:\document_slm_project\test_receipt\img"
    for img_name in os.listdir(base_path):
        if not img_name.endswith(".json") and not img_name.endswith(".txt"):
            img_path = os.path.join(base_path,img_name)
            print(img_path)
            print(img_name.split(".")[0] + ".txt")
            slm_test = run_ocr_for_slm(img_path)
            with open(os.path.join(base_path, img_name.split(".")[0] + ".txt"), "w", encoding="utf-8") as f:
                f.write(slm_test)
