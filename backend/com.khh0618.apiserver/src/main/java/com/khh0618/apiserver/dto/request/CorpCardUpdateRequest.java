package com.khh0618.apiserver.dto.request;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class CorpCardUpdateRequest {
	private String cardNumberLast4;
	private String cardName;
	private String issuer;
}
