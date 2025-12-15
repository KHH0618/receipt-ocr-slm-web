package com.khh0618.apiserver.dto.request;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ReceiptCorrectionCreateRequest {
    private String imageId;        // 어떤 영수증인지
    private String ocrText;        // 선택 (원문 저장용)
    private String correctedJson;  // 필수 (수정된 JSON)
    private String note;           // 선택 (메모)
}
