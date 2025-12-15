package com.khh0618.apiserver.dto.request;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UserLoginRequest {
    private String loginId;
    private String password;
    
    public String getLoginId() {
    	return loginId;
    }
    
    public String getPassword() {
    	return password;
    }
    
}
