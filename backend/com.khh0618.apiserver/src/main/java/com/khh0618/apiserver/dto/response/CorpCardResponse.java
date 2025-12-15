package com.khh0618.apiserver.dto.response;

import java.time.LocalDateTime;
import lombok.Getter;

@Getter
public class CorpCardResponse {
	
	private final String cardNumberLast4;
	private final String cardName;
	private final String issuer;
	private final LocalDateTime createdAt;
	
	public CorpCardResponse(String cardNumberLast4, String cardName, String issuer, LocalDateTime createdAt) {
		this.cardNumberLast4 = cardNumberLast4;
		this.cardName = cardName;
		this.issuer = issuer;
		this.createdAt = createdAt;
	}
}
