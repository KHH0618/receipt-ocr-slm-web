package com.khh0618.apiserver.dto.request;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter

public class CorpCardCreateRequest {
	private String cardNumberLast4;
	private String cardName;
	private String issuer; // 카드 발급사
}
