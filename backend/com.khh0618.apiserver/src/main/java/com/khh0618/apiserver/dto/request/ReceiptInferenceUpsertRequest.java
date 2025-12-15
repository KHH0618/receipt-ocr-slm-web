package com.khh0618.apiserver.dto.request;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ReceiptInferenceUpsertRequest {

    private String imageId;
    private String ocrText;
    private String inferredJson;
    private String inferenceStatus;
    private String modelName; 
    private String modelVersion;
    private Integer inferenceTimeMs;
    private String errorMessage;
}
