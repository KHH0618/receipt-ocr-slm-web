package com.khh0618.apiserver.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.Getter;

@Entity
@Getter
@Table(name = "receipt_card_map")
public class ReceiptCardMapEntity {

    @Id
    @Column(name = "image_id", length = 36, nullable = false)
    private String imageId;

    // FK -> corp_card.card_id (AUTO_INCREMENT)
    @Column(name = "card_id", nullable = false)
    private Long cardId;

    @Column(name = "mapped_at", nullable = false)
    private LocalDateTime mappedAt;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    protected ReceiptCardMapEntity() {
    }

    public ReceiptCardMapEntity(String imageId, Long cardId) {
        this.imageId = imageId;
        this.cardId = cardId;
    }

    public void changeCard(Long newCardId) {
        this.cardId = newCardId;
        this.mappedAt = LocalDateTime.now();
    }

    @PrePersist
    public void prePersist() {
        LocalDateTime now = LocalDateTime.now();
        if (this.mappedAt == null) this.mappedAt = now;
        this.createdAt = now;
        this.updatedAt = now;
    }

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}
