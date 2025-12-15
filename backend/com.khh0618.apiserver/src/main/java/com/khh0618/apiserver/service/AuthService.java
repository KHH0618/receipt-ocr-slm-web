package com.khh0618.apiserver.service;

import com.khh0618.apiserver.dto.request.UserLoginRequest;
import com.khh0618.apiserver.dto.request.UserSignupRequest;
import com.khh0618.apiserver.entity.UserAccountEntity;
import com.khh0618.apiserver.repository.UserAccountRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

    private final UserAccountRepository userAccountRepository;
    private final PasswordEncoder passwordEncoder;

    public AuthService(UserAccountRepository userAccountRepository, PasswordEncoder passwordEncoder) {
        this.userAccountRepository = userAccountRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public void signup(UserSignupRequest request) {
        if (userAccountRepository.existsByLoginId(request.getLoginId())) {
            throw new IllegalArgumentException("이미 사용 중인 아이디입니다.");
        }

        String loginId = request.getLoginId();
        String passwordHash = passwordEncoder.encode(request.getPassword());
        String name = request.getName();
        String departmentName = request.getDepartmentName();
        String jobTitle = request.getJobTitle();

        UserAccountEntity e = UserAccountEntity.createUser(loginId, passwordHash, name, departmentName, jobTitle);
        userAccountRepository.save(e);
    }

    public UserAccountEntity validateLogin(UserLoginRequest req) {
        var userOpt = userAccountRepository.findByLoginIdAndIsActive(req.getLoginId(), 1);
        if (userOpt.isEmpty()) {
            throw new IllegalArgumentException("아이디 또는 비밀번호가 올바르지 않습니다.");
        }

        var user = userOpt.get();

        if (!passwordEncoder.matches(req.getPassword(), user.getPasswordHash())) {
            throw new IllegalArgumentException("아이디 또는 비밀번호가 올바르지 않습니다.");
        }

        return user;
    }
}
