package com.khh0618.apiserver.repository;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import com.khh0618.apiserver.entity.UserAccountEntity;

public interface UserAccountRepository extends JpaRepository<UserAccountEntity, Long> {
    Optional<UserAccountEntity> findByLoginId(String loginId);
    boolean existsByLoginId(String loginId);
    Optional<UserAccountEntity> findByLoginIdAndIsActive(String loginId, Integer isActive);

}
