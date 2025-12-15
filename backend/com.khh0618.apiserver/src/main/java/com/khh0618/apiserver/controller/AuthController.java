package com.khh0618.apiserver.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import com.khh0618.apiserver.dto.request.UserLoginRequest;
import com.khh0618.apiserver.dto.request.UserSignupRequest;
import com.khh0618.apiserver.dto.response.LoginResponse;
import com.khh0618.apiserver.service.AuthService;
import com.khh0618.apiserver.util.JwtUtil;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;
    private final JwtUtil jwtUtil;

    public AuthController(AuthService authService, JwtUtil jwtUtil) {
        this.authService = authService;
        this.jwtUtil = jwtUtil;
    }

    @PostMapping("/signup")
    public ResponseEntity<Void> signup(@RequestBody UserSignupRequest req) {
        authService.signup(req);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/login")
    public LoginResponse login(@RequestBody UserLoginRequest req) {
        var user = authService.validateLogin(req);
        String token = jwtUtil.createAccessToken(user.getLoginId());
        return new LoginResponse(token);
    }
}
