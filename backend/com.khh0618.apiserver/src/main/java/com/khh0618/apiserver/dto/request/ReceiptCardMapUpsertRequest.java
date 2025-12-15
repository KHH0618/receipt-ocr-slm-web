package com.khh0618.apiserver.dto.request;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ReceiptCardMapUpsertRequest {
    private String imageId; // UUID 문자열
    private Long cardId;    // corp_card.card_id
}
