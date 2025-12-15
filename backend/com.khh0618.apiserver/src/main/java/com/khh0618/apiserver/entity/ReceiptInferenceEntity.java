package com.khh0618.apiserver.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.Getter;

@Entity
@Getter
@Table(name = "receipt_inference")
public class ReceiptInferenceEntity {

    @Id
    @Column(name = "image_id", length = 36, nullable = false)
    private String imageId; // receipt_upload.image_id 와 1:1

    @Lob
    @Column(name = "ocr_text")
    private String ocrText; // LONGTEXT

    @Lob
    @Column(name = "inferred_json")
    private String inferredJson; // LONGTEXT (JSON 문자열)

    @Column(name = "inference_status", nullable = false, length = 20)
    private String inferenceStatus; // SUCCESS / FAIL / PENDING 등

    @Column(name = "model_name", length = 100)
    private String modelName;

    @Column(name = "model_version", length = 50)
    private String modelVersion;

    @Column(name = "inference_time_ms")
    private Integer inferenceTimeMs;

    @Column(name = "error_message", length = 1000)
    private String errorMessage;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
    
    protected ReceiptInferenceEntity() {
    	
    }
    
    public ReceiptInferenceEntity(String imageId) {
        this.imageId = imageId;
        this.inferenceStatus = "PENDING";
    }

    public void markSuccess(
            String ocrText,
            String inferredJson,
            String modelName,
            String modelVersion,
            Integer inferenceTimeMs
    ) {
        this.ocrText = ocrText;
        this.inferredJson = inferredJson;
        this.modelName = modelName;
        this.modelVersion = modelVersion;
        this.inferenceTimeMs = inferenceTimeMs;
        this.errorMessage = null;
        this.inferenceStatus = "SUCCESS";
    }

    public void markFail(String errorMessage) {
        this.errorMessage = errorMessage;
        this.inferenceStatus = "FAIL";
    }

    @PrePersist
    public void prePersist() {
        LocalDateTime now = LocalDateTime.now();
        this.createdAt = now;
        this.updatedAt = now;
        if (this.inferenceStatus == null) this.inferenceStatus = "PENDING";
    }

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}
