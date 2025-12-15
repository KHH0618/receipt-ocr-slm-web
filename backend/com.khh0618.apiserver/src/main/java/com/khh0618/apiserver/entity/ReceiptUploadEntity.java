package com.khh0618.apiserver.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.Getter;

@Entity
@Getter
@Table(name = "receipt_upload")
public class ReceiptUploadEntity {

    @Id
    @Column(name = "image_id", length = 36, nullable = false)
    private String imageId;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "uploaded_at", nullable = false)
    private LocalDateTime uploadedAt;

    @Column(name = "storage_path", nullable = false, length = 700)
    private String storagePath;

    @Column(name = "original_filename", length = 255)
    private String originalFilename;

    @Column(name = "mime_type", length = 100)
    private String mimeType;

    @Column(name = "file_size_bytes")
    private Long fileSizeBytes;

    @Column(name = "sha256", length = 64)
    private String sha256;

    @Column(name = "upload_status", nullable = false, length = 20)
    private String uploadStatus;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
    
    protected ReceiptUploadEntity() {
    	
    }

    public ReceiptUploadEntity(
            String imageId,
            Long userId,
            String storagePath,
            String originalFilename,
            String mimeType,
            Long fileSizeBytes,
            String sha256
    ) {
        this.imageId = imageId;
        this.userId = userId;
        this.storagePath = storagePath;
        this.originalFilename = originalFilename;
        this.mimeType = mimeType;
        this.fileSizeBytes = fileSizeBytes;
        this.sha256 = sha256;
        this.uploadStatus = "UPLOADED";
    }

    public void markStored() {
        this.uploadStatus = "STORED";
    }

    public void markFailed(String newStatus) {
        this.uploadStatus = newStatus;
    }

    public void changeStoragePath(String newStoragePath) {
        this.storagePath = newStoragePath;
    }

    @PrePersist
    public void prePersist() {
        LocalDateTime now = LocalDateTime.now();
        if (this.uploadedAt == null) this.uploadedAt = now;
        this.createdAt = now;
        this.updatedAt = now;
        if (this.uploadStatus == null) this.uploadStatus = "UPLOADED";
    }

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}
