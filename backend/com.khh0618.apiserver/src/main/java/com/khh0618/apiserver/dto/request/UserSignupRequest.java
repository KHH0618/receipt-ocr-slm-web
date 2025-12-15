package com.khh0618.apiserver.dto.request;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UserSignupRequest {
    private String loginId;
    private String password;
    private String name;
    private String departmentName;
    private String jobTitle;
    
    public String getLoginId() {
        return loginId;
    }

    public String getPassword() {
        return password;
    }

    public String getName() {
        return name;
    }

    public String getDepartmentName() {
        return departmentName;
    }
    
    public String getJobTitle() {
    	return jobTitle;
    }
}
