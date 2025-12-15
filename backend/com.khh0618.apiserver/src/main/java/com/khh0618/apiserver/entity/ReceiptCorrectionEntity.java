package com.khh0618.apiserver.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.Getter;

@Entity
@Getter
@Table(name = "receipt_correction")
public class ReceiptCorrectionEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "correction_id", nullable = false)
    private Long correctionId;

    @Column(name = "image_id", length = 36, nullable = false)
    private String imageId;

    @Column(name = "corrected_by_user_id", nullable = false)
    private Long correctedByUserId;

    @Column(name = "corrected_at", nullable = false)
    private LocalDateTime correctedAt;

    @Lob
    @Column(name = "ocr_text")
    private String ocrText; // LONGTEXT

    @Lob
    @Column(name = "corrected_json", nullable = false)
    private String correctedJson; // LONGTEXT (JSON 문자열)

    @Column(name = "note", length = 500)
    private String note;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    protected  ReceiptCorrectionEntity() {
    	
    }
    
    public ReceiptCorrectionEntity(
            String imageId,
            Long correctedByUserId,
            String ocrText,
            String correctedJson,
            String note
    ) {
        this.imageId = imageId;
        this.correctedByUserId = correctedByUserId;
        this.ocrText = ocrText;
        this.correctedJson = correctedJson;
        this.note = note;
    }

    public void updateCorrection(String newOcrText, String newCorrectedJson, String newNote) {
        this.ocrText = newOcrText;
        this.correctedJson = newCorrectedJson;
        this.note = newNote;
        this.correctedAt = LocalDateTime.now();
    }

    @PrePersist
    public void prePersist() {
        LocalDateTime now = LocalDateTime.now();
        if (this.correctedAt == null) this.correctedAt = now;
        this.createdAt = now;
        this.updatedAt = now;
    }

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}
