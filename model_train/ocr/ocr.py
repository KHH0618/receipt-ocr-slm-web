from paddleocr import PaddleOCR
import os
import numpy as np


def run_ocr(img_path: str):
    # 1) 경로 체크
    if not os.path.exists(img_path):
        print("❌ 이미지 경로 없음:", img_path)
        return

    # 2) PaddleOCR 초기화
    #   - lang="korean" : 한글 모델
    #   - use_textline_orientation=True : 글줄 방향 보정
    ocr = PaddleOCR(
        lang="korean",
        use_textline_orientation=True
    )

    # 3) OCR 실행
    #   DeprecationWarning 이 뜨지만 현재 버전에서 그대로 동작하므로 사용
    result = ocr.ocr(img_path)

    if not result or not isinstance(result, list):
        print("❌ OCR 결과가 비어 있습니다.")
        return

    data = result[0]

    texts = data.get("rec_texts", [])
    scores = data.get("rec_scores", [])
    boxes = data.get("rec_boxes", None)
    doc_prep = data.get("doc_preprocessor_res", {})

    if not texts:
        print("❌ 인식된 텍스트가 없습니다.")
        return

    # 4) 각 글자/문장 박스의 y좌표 기준으로 위→아래 정렬
    #    다만 doc_preprocessor 가 angle=180 으로 이미지를 뒤집은 경우가 있어서
    #    angle 값을 보고 정렬 방향 결정
    angle = 0
    if isinstance(doc_prep, dict):
        angle = doc_prep.get("angle", 0)

    if boxes is not None:
        boxes = np.array(boxes)
        indices = list(range(len(texts)))

        # 박스 포맷: [x_min, y_min, x_max, y_max] 라고 가정
        if angle in [180, -180]:
            # 이미지가 180도 뒤집혀 있다고 판단된 경우: y 내림차순
            indices.sort(key=lambda i: (-boxes[i][1], boxes[i][0]))
        else:
            # 일반적인 경우: y 오름차순
            indices.sort(key=lambda i: (boxes[i][1], boxes[i][0]))
    else:
        indices = list(range(len(texts)))

    # 5) 정렬된 순서대로 출력
    print("\n=== OCR TEXT RESULT (위 → 아래 순서) ===")
    for out_idx, i in enumerate(indices, start=1):
        text = texts[i]
        score = scores[i] if i < len(scores) else 0.0
        print(f"[{out_idx}] {text}  (conf={score:.3f})")


if __name__ == "__main__":
    # 실제 이미지 경로
    img_path = r"E:\document_slm_project\test_receipt\img\IMG_1740.jpeg"
    run_ocr(img_path)
