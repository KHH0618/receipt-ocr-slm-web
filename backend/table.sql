-- 0) Database
CREATE DATABASE IF NOT EXISTS receipt_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE receipt_db;

-- 1) 회원 테이블
CREATE TABLE IF NOT EXISTS user_account (
  user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  login_id VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(100) NOT NULL,
  department_name VARCHAR(100) NULL,
  job_title VARCHAR(50) NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'USER',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (user_id),
  UNIQUE KEY uk_user_login_id (login_id),
  INDEX idx_user_department (department_name),
  INDEX idx_user_job_title (job_title)
) ENGINE=InnoDB;

-- 2) 영수증 사진 업로드 테이블
CREATE TABLE IF NOT EXISTS receipt_upload (
  image_id CHAR(36) NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  uploaded_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  storage_path VARCHAR(700) NOT NULL,
  original_filename VARCHAR(255) NULL,
  mime_type VARCHAR(100) NULL,
  file_size_bytes BIGINT UNSIGNED NULL,
  sha256 CHAR(64) NULL,
  upload_status VARCHAR(20) NOT NULL DEFAULT 'UPLOADED',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (image_id),
  INDEX idx_upload_user_time (user_id, uploaded_at),
  INDEX idx_upload_sha256 (sha256),
  CONSTRAINT fk_upload_user
    FOREIGN KEY (user_id) REFERENCES user_account(user_id)
    ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 3) 추론 테이블 (image_id 당 1건)
CREATE TABLE IF NOT EXISTS receipt_inference (
  image_id CHAR(36) NOT NULL,
  ocr_text LONGTEXT NULL,
  inferred_json LONGTEXT NULL,
  inference_status VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
  model_name VARCHAR(100) NULL,
  model_version VARCHAR(50) NULL,
  inference_time_ms INT UNSIGNED NULL,
  error_message VARCHAR(1000) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (image_id),
  INDEX idx_infer_status (inference_status),
  INDEX idx_infer_model (model_name, model_version),
  CONSTRAINT fk_infer_upload
    FOREIGN KEY (image_id) REFERENCES receipt_upload(image_id)
    ON DELETE CASCADE,
  CONSTRAINT chk_inferred_json_valid
    CHECK (inferred_json IS NULL OR JSON_VALID(inferred_json))
) ENGINE=InnoDB;

-- 4) MLOps용 유저 수정 데이터 테이블
CREATE TABLE IF NOT EXISTS receipt_correction (
  correction_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  image_id CHAR(36) NOT NULL,
  corrected_by_user_id BIGINT UNSIGNED NOT NULL,
  corrected_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  ocr_text LONGTEXT NULL,
  corrected_json LONGTEXT NOT NULL,
  note VARCHAR(500) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (correction_id),
  INDEX idx_correction_image_time (image_id, corrected_at),
  INDEX idx_correction_user_time (corrected_by_user_id, corrected_at),
  CONSTRAINT fk_corr_upload
    FOREIGN KEY (image_id) REFERENCES receipt_upload(image_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_corr_user
    FOREIGN KEY (corrected_by_user_id) REFERENCES user_account(user_id)
    ON DELETE RESTRICT,
  CONSTRAINT chk_corrected_json_valid
    CHECK (JSON_VALID(corrected_json))
) ENGINE=InnoDB;

-- 5) 법인 카드 관리 테이블
CREATE TABLE IF NOT EXISTS corp_card (
  card_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  last4 CHAR(4) NOT NULL,
  card_label VARCHAR(100) NULL,
  issuer VARCHAR(50) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (card_id),
  INDEX idx_card_last4 (last4),
  INDEX idx_card_active (is_active)
) ENGINE=InnoDB;

-- 6) 영수증-법인카드 매핑 테이블
CREATE TABLE IF NOT EXISTS receipt_card_map (
  image_id CHAR(36) NOT NULL,
  card_id BIGINT UNSIGNED NOT NULL,
  mapped_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (image_id),
  INDEX idx_map_card (card_id),
  CONSTRAINT fk_map_upload
    FOREIGN KEY (image_id) REFERENCES receipt_upload(image_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_map_card
    FOREIGN KEY (card_id) REFERENCES corp_card(card_id)
    ON DELETE RESTRICT
) ENGINE=InnoDB;
