package com.khh0618.apiserver.dto.response;

import java.time.LocalDateTime;
import lombok.Getter;

@Getter
public class ReceiptInferenceResponse {

    private final String imageId;
    private final String ocrText;
    private final String inferredJson;
    private final String inferenceStatus;
    private final String modelName;
    private final String modelVersion;
    private final Integer inferenceTimeMs;
    private final String errorMessage;
    private final LocalDateTime createdAt;
    private final LocalDateTime updatedAt;

    public ReceiptInferenceResponse(
            String imageId,
            String ocrText,
            String inferredJson,
            String inferenceStatus,
            String modelName,
            String modelVersion,
            Integer inferenceTimeMs,
            String errorMessage,
            LocalDateTime createdAt,
            LocalDateTime updatedAt
    ) {
        this.imageId = imageId;
        this.ocrText = ocrText;
        this.inferredJson = inferredJson;
        this.inferenceStatus = inferenceStatus;
        this.modelName = modelName;
        this.modelVersion = modelVersion;
        this.inferenceTimeMs = inferenceTimeMs;
        this.errorMessage = errorMessage;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }
}
