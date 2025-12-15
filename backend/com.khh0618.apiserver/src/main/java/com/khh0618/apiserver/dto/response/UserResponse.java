package com.khh0618.apiserver.dto.response;

import java.time.LocalDateTime;
import lombok.Getter;

@Getter
public class UserResponse {
    private final Long userId;
    private final String loginId;
    private final String name;
    private final String departmentName;
    private final String job_title;
    private final LocalDateTime createdAt;

    public UserResponse(Long userId, String loginId, String name, String departmentName, String job_title, LocalDateTime createdAt) {
        this.userId = userId;
        this.loginId = loginId;
        this.name = name;
        this.departmentName = departmentName;
        this.job_title = job_title;
        this.createdAt = createdAt;
    }
}
