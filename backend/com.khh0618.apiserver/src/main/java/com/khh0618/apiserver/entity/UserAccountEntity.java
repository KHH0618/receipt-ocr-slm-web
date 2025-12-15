package com.khh0618.apiserver.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.Getter;

@Entity
@Getter
@Table(name = "user_account")
public class UserAccountEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "user_id")
    private Long userId;

    @Column(name = "login_id", nullable = false, unique = true, length = 50)
    private String loginId;

    @Column(name = "password_hash", nullable = false, length = 255)
    private String passwordHash;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Column(name = "department_name", nullable = true, length = 100)
    private String departmentName;
    
    @Column(name = "job_title", nullable = true, length = 50)
    private String jobTitle;
    
    @Column(name = "role", nullable = false, length = 20)
    private String role;

    @Column(name = "is_active", nullable = false)
    private Integer isActive;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    protected UserAccountEntity() {
    }

    // Getter
    public Long getUserId() {
        return userId;
    }

    public String getLoginId() {
        return loginId;
    }

    public String getPasswordHash() {
        return passwordHash;
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

    public Integer getIsActive() {
        return isActive;
    }
    
    // Setter
    public static UserAccountEntity createUser(
            String loginId,
            String passwordHash,
            String name,
            String departmentName,
            String jobTitle
    ) {
        UserAccountEntity u = new UserAccountEntity();
        u.loginId = loginId;
        u.passwordHash = passwordHash;
        u.name = name;
        u.departmentName = departmentName;
        u.jobTitle = jobTitle;

        u.role = "USER";
        u.isActive = 1;
        return u;
    }

    
    public void changePassword(String newPasswordHash) {
        this.passwordHash = newPasswordHash;
    }
    
    public void deactivate() {
        this.isActive = 0;
    }
    
    @PrePersist
    public void prePersist() {
        LocalDateTime now = LocalDateTime.now();
        this.createdAt = now;
        this.updatedAt = now;
        if (this.role == null) this.role = "USER";
        if (this.isActive == null) this.isActive = 1;
    }

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
    
   
}
