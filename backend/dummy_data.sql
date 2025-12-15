-- ========================================
-- receipt_db 더미데이터
-- ========================================

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE receipt_card_map;
TRUNCATE receipt_correction;
TRUNCATE receipt_inference;
TRUNCATE receipt_upload;
TRUNCATE corp_card;
TRUNCATE user_account;
SET FOREIGN_KEY_CHECKS = 1;


USE receipt_db;

-- 1) 회원 더미데이터
INSERT INTO user_account
(login_id, password_hash, name, department_name, job_title, role, is_active)
VALUES
('admin', '$2a$10$dummyhashadmin', '관리자', 'IT', '팀장', 'ADMIN', 1),
('user1', '$2a$10$dummyhashuser1', '김호현', '개발팀', '대리', 'USER', 1),
('user2', '$2a$10$dummyhashuser2', '이영희', '회계팀', '사원', 'USER', 1);

-- 2) 법인카드 더미데이터
INSERT INTO corp_card
(last4, card_label, issuer, is_active)
VALUES
('1234', '개발팀 법인카드', 'KB', 1),
('5678', '회계팀 법인카드', 'SHINHAN', 1);

-- 3) 영수증 업로드 더미데이터
INSERT INTO receipt_upload
(image_id, user_id, storage_path, original_filename, mime_type, file_size_bytes, sha256)
VALUES
('11111111-1111-1111-1111-111111111111', 2,
 '/data/receipts/receipt1.jpg', 'receipt1.jpg', 'image/jpeg', 345678,
 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'),

('22222222-2222-2222-2222-222222222222', 2,
 '/data/receipts/receipt2.jpg', 'receipt2.jpg', 'image/jpeg', 456789,
 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'),

('33333333-3333-3333-3333-333333333333', 3,
 '/data/receipts/receipt3.jpg', 'receipt3.jpg', 'image/jpeg', 567890,
 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc');

-- 4) 추론 결과 더미데이터
INSERT INTO receipt_inference
(image_id, ocr_text, inferred_json, model_name, model_version, inference_time_ms)
VALUES
('11111111-1111-1111-1111-111111111111',
 '아메리카노 4500원',
 '{"items":[{"name":"아메리카노","price":4500}],"total":4500}',
 'ocr-slm', 'v1.0', 120),

('22222222-2222-2222-2222-222222222222',
 '점심식대 12000원',
 '{"items":[{"name":"점심식대","price":12000}],"total":12000}',
 'ocr-slm', 'v1.0', 140),

('33333333-3333-3333-3333-333333333333',
 '사무용품 30000원',
 '{"items":[{"name":"사무용품","price":30000}],"total":30000}',
 'ocr-slm', 'v1.0', 160);

-- 5) 영수증-법인카드 매핑 더미데이터
INSERT INTO receipt_card_map
(image_id, card_id)
VALUES
('11111111-1111-1111-1111-111111111111', 1),
('22222222-2222-2222-2222-222222222222', 2);

-- 6) 사용자 수정 이력 더미데이터
INSERT INTO receipt_correction
(image_id, corrected_by_user_id, ocr_text, corrected_json, note)
VALUES
(
 '11111111-1111-1111-1111-111111111111',
 1,
 '아메리카노 4500원',
 '{"items":[{"name":"아메리카노","price":4500}],"total":4500,"category":"식비"}',
 '카테고리 추가'
);
