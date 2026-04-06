-- =============================================================================
-- CẤU TRÚC TẤT CẢ BẢNG - DSBC (Danh sách bầu cử)
-- Database: scrapy_products
-- Charset: utf8mb4
-- =============================================================================

CREATE DATABASE IF NOT EXISTS scrapy_products
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE scrapy_products;

-- -----------------------------------------------------------------------------
-- 2. HĐND CẤP TỈNH
-- -----------------------------------------------------------------------------

-- 2a. hdnd_candidates - Danh sách ứng cử viên HĐND cấp tỉnh
CREATE TABLE IF NOT EXISTS hdnd_candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    province VARCHAR(255),
    party VARCHAR(255),
    constituency VARCHAR(500),
    description TEXT,
    detail_url VARCHAR(767),
    candidate_id VARCHAR(100),
    candidate_uuid VARCHAR(100),
    position VARCHAR(500),
    birthdate VARCHAR(50),
    hometown VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_detail_url (detail_url),
    INDEX idx_province (province),
    INDEX idx_candidate_id (candidate_id),
    INDEX idx_candidate_uuid (candidate_uuid)
);

-- 2b. hdnd_detail_info - Chi tiết ứng viên HĐND cấp tỉnh (liên kết qua candidate_uuid)
CREATE TABLE IF NOT EXISTS hdnd_detail_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_uuid VARCHAR(100) NOT NULL,
    detail_url VARCHAR(767),
    province VARCHAR(255),
    constituency VARCHAR(500),
    name VARCHAR(255),
    birthdate VARCHAR(50),
    position VARCHAR(500),
    hometown VARCHAR(500),
    gender VARCHAR(50),
    nationality VARCHAR(100),
    ethnic VARCHAR(100),
    religion VARCHAR(100),
    current_address VARCHAR(500),
    education VARCHAR(255),
    foreign_lang VARCHAR(255),
    degree VARCHAR(255),
    party_theory VARCHAR(255),
    professional VARCHAR(500),
    work_place VARCHAR(500),
    party_join_date VARCHAR(50),
    qh_rep VARCHAR(255),
    hdnd_rep VARCHAR(255),
    image_url VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_candidate_uuid (candidate_uuid),
    INDEX idx_detail_url (detail_url)
);

-- -----------------------------------------------------------------------------
-- 3. QUỐC HỘI (QH)
-- -----------------------------------------------------------------------------

-- 3a. hdnd_qh_candidates - Danh sách ứng cử viên Quốc hội
CREATE TABLE IF NOT EXISTS hdnd_qh_candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    province VARCHAR(255),
    party VARCHAR(255),
    constituency VARCHAR(500),
    description TEXT,
    detail_url VARCHAR(767),
    candidate_id VARCHAR(100),
    candidate_uuid VARCHAR(100),
    position VARCHAR(500),
    birthdate VARCHAR(50),
    hometown VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_detail_url (detail_url),
    INDEX idx_province (province),
    INDEX idx_candidate_uuid (candidate_uuid)
);

-- 3b. hdnd_qh_detail_info - Chi tiết ứng viên Quốc hội
CREATE TABLE IF NOT EXISTS hdnd_qh_detail_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_uuid VARCHAR(100) NOT NULL,
    detail_url VARCHAR(767),
    province VARCHAR(255),
    constituency VARCHAR(500),
    name VARCHAR(255),
    birthdate VARCHAR(50),
    position VARCHAR(500),
    hometown VARCHAR(500),
    gender VARCHAR(50),
    nationality VARCHAR(100),
    ethnic VARCHAR(100),
    religion VARCHAR(100),
    current_address VARCHAR(500),
    education VARCHAR(255),
    foreign_lang VARCHAR(255),
    degree VARCHAR(255),
    party_theory VARCHAR(255),
    professional VARCHAR(500),
    work_place VARCHAR(500),
    party_join_date VARCHAR(50),
    qh_rep VARCHAR(255),
    hdnd_rep VARCHAR(255),
    image_url VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_candidate_uuid (candidate_uuid),
    INDEX idx_detail_url (detail_url)
);

-- -----------------------------------------------------------------------------
-- 4. HĐND CẤP XÃ
-- -----------------------------------------------------------------------------

-- 4a. hdnd_xa_candidates - Danh sách ứng cử viên HĐND cấp xã
CREATE TABLE IF NOT EXISTS hdnd_xa_candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_uuid VARCHAR(100) NOT NULL,
    detail_url VARCHAR(767),
    province VARCHAR(255),
    constituency VARCHAR(500),
    name VARCHAR(255),
    birthdate VARCHAR(50),
    position VARCHAR(500),
    hometown VARCHAR(500),
    gender VARCHAR(50),
    nationality VARCHAR(100),
    ethnic VARCHAR(100),
    religion VARCHAR(100),
    current_address VARCHAR(500),
    education VARCHAR(255),
    foreign_lang VARCHAR(255),
    degree VARCHAR(255),
    party_theory VARCHAR(255),
    professional VARCHAR(500),
    work_place VARCHAR(500),
    party_join_date VARCHAR(50),
    qh_rep VARCHAR(255),
    hdnd_rep VARCHAR(255),
    image_url VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_candidate_uuid (candidate_uuid),
    INDEX idx_province (province),
    INDEX idx_constituency (constituency)
);

-- 4b. hdnd_xa_detail_info - Chi tiết ứng viên HĐND cấp xã
CREATE TABLE IF NOT EXISTS hdnd_xa_detail_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_uuid VARCHAR(100) NOT NULL,
    detail_url VARCHAR(767),
    province VARCHAR(255),
    constituency VARCHAR(500),
    name VARCHAR(255),
    birthdate VARCHAR(50),
    position VARCHAR(500),
    hometown VARCHAR(500),
    gender VARCHAR(50),
    nationality VARCHAR(100),
    ethnic VARCHAR(100),
    religion VARCHAR(100),
    current_address VARCHAR(500),
    education VARCHAR(255),
    foreign_lang VARCHAR(255),
    degree VARCHAR(255),
    party_theory VARCHAR(255),
    professional VARCHAR(500),
    work_place VARCHAR(500),
    party_join_date VARCHAR(50),
    qh_rep VARCHAR(255),
    hdnd_rep VARCHAR(255),
    image_url VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_candidate_uuid (candidate_uuid),
    INDEX idx_detail_url (detail_url),
    INDEX idx_province (province)
);

-- -----------------------------------------------------------------------------
-- 5. TRÚNG CỬ HĐND CẤP XÃ (đại biểu — spider hdnd_tc_xa)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS hdbc_candidates_tc_cx (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_uuid VARCHAR(100) NOT NULL,
    detail_url VARCHAR(767),
    province VARCHAR(255),
    constituency VARCHAR(500),
    name VARCHAR(255),
    birthdate VARCHAR(50),
    position VARCHAR(500),
    hometown VARCHAR(500),
    gender VARCHAR(50),
    nationality VARCHAR(100),
    ethnic VARCHAR(100),
    religion VARCHAR(100),
    current_address VARCHAR(500),
    education VARCHAR(255),
    foreign_lang VARCHAR(255),
    degree VARCHAR(255),
    party_theory VARCHAR(255),
    professional VARCHAR(500),
    work_place VARCHAR(500),
    party_join_date VARCHAR(50),
    qh_rep VARCHAR(255),
    hdnd_rep VARCHAR(255),
    image_url VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_candidate_uuid (candidate_uuid),
    INDEX idx_province (province),
    INDEX idx_constituency (constituency)
);

CREATE TABLE IF NOT EXISTS hdbc_candidates_tc_cx_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_uuid VARCHAR(100) NOT NULL,
    detail_url VARCHAR(767),
    province VARCHAR(255),
    constituency VARCHAR(500),
    name VARCHAR(255),
    birthdate VARCHAR(50),
    position VARCHAR(500),
    hometown VARCHAR(500),
    gender VARCHAR(50),
    nationality VARCHAR(100),
    ethnic VARCHAR(100),
    religion VARCHAR(100),
    current_address VARCHAR(500),
    education VARCHAR(255),
    foreign_lang VARCHAR(255),
    degree VARCHAR(255),
    party_theory VARCHAR(255),
    professional VARCHAR(500),
    work_place VARCHAR(500),
    party_join_date VARCHAR(50),
    qh_rep VARCHAR(255),
    hdnd_rep VARCHAR(255),
    image_url VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_candidate_uuid (candidate_uuid),
    INDEX idx_detail_url (detail_url),
    INDEX idx_province (province)
);
