package com.khh0618.apiserver.dto.request;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ReceiptCorrectionUpsertRequest {
    private String imageId;
    private String ocrText;
    private String correctedJson;
    private String note;
}
