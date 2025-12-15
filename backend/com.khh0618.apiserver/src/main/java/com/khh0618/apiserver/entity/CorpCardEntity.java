package com.khh0618.apiserver.entity;

import java.time.LocalDateTime;


import jakarta.persistence.*;
import lombok.Getter;

@Entity
@Table(name = "corp_card")
@Getter
public class CorpCardEntity {
	
	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	@Column(name = "card_id", nullable = false)
	private Long cardId;
	
	@Column(name = "last4", nullable = false)
	private String cardNumberLast4;
	
	@Column(name = "card_label", nullable = true)
	private String cardName;
	
	@Column(name = "issuer", nullable = true)
	private String issuer; // 카드 발급사
	
	@Column(name = "is_active", nullable = false)
	private Boolean isActive;
	
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
    
    protected CorpCardEntity() {
    }

    
    @PrePersist
    public void prePersist() {
    	if (this.isActive == null) {
            this.isActive = true;
        }
        LocalDateTime now = LocalDateTime.now();
        this.createdAt = now;
        this.updatedAt = now;
    }

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}
