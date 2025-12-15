package com.khh0618.apiserver.dto.request;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UserUpdateRequest {
    private String name;
    private String departmentName;
    private String jobTitle;
}