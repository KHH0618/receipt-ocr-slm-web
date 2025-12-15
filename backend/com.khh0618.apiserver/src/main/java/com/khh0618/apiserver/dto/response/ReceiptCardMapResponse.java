package com.khh0618.apiserver.dto.response;

import java.time.LocalDateTime;
import lombok.Getter;

@Getter
public class ReceiptCardMapResponse {

    private final String imageId;
    private final Long cardId;
    private final LocalDateTime mappedAt;
    private final LocalDateTime createdAt;
    private final LocalDateTime updatedAt;

    public ReceiptCardMapResponse(
            String imageId,
            Long cardId,
            LocalDateTime mappedAt,
            LocalDateTime createdAt,
            LocalDateTime updatedAt
    ) {
        this.imageId = imageId;
        this.cardId = cardId;
        this.mappedAt = mappedAt;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }
}
