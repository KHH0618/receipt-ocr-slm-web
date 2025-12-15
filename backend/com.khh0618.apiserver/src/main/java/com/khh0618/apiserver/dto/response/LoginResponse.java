package com.khh0618.apiserver.dto.response;

import lombok.Getter;

@Getter
public class LoginResponse {
    private final String accessToken;

    public LoginResponse(String accessToken) {
        this.accessToken = accessToken;
    }
    
    public String getAccessToken() {
    	return accessToken;
    }
}
