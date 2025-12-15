package com.khh0618.apiserver.dto.response;

import java.time.LocalDateTime;
import lombok.Getter;

@Getter
public class ReceiptUploadResponse {

    private final String imageId;
    private final Long userId;
    private final LocalDateTime uploadedAt;
    private final String storagePath;
    private final String originalFilename;
    private final String mimeType;
    private final Long fileSizeBytes;
    private final String sha256;
    private final String uploadStatus;
    private final LocalDateTime createdAt;
    private final LocalDateTime updatedAt;

    public ReceiptUploadResponse(
            String imageId,
            Long userId,
            LocalDateTime uploadedAt,
            String storagePath,
            String originalFilename,
            String mimeType,
            Long fileSizeBytes,
            String sha256,
            String uploadStatus,
            LocalDateTime createdAt,
            LocalDateTime updatedAt
    ) {
        this.imageId = imageId;
        this.userId = userId;
        this.uploadedAt = uploadedAt;
        this.storagePath = storagePath;
        this.originalFilename = originalFilename;
        this.mimeType = mimeType;
        this.fileSizeBytes = fileSizeBytes;
        this.sha256 = sha256;
        this.uploadStatus = uploadStatus;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }
}
