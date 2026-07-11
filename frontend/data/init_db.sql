-- 潮汕文化宣传平台 — 数据库建表 SQL
-- MySQL 8.0+, utf8mb4

CREATE DATABASE IF NOT EXISTS chaoshan_platform
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE chaoshan_platform;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(11) NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(50) DEFAULT '',
    avatar_url VARCHAR(500) DEFAULT '',
    persona_type VARCHAR(20) DEFAULT 'tourist',
    interests JSON DEFAULT NULL,
    role VARCHAR(10) DEFAULT 'user',
    is_disabled BOOL DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 邮箱验证码（复用 phone 列名存储邮箱地址）
CREATE TABLE IF NOT EXISTS sms_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(255) NOT NULL,
    code VARCHAR(10) NOT NULL,
    purpose VARCHAR(20) NOT NULL,
    used BOOL DEFAULT FALSE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sms_phone_time (phone, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 登录失败记录（复用 phone 列名存储邮箱地址）
CREATE TABLE IF NOT EXISTS login_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) DEFAULT '',
    success BOOL DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_attempts_phone_time (phone, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 美食分类
CREATE TABLE IF NOT EXISTS food_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    icon VARCHAR(255) DEFAULT '',
    sort_order INT DEFAULT 0,
    INDEX idx_cat_sort (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 美食/店铺
CREATE TABLE IF NOT EXISTS foods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    type ENUM('dish','shop') NOT NULL DEFAULT 'dish',
    description TEXT,
    image_url VARCHAR(500) DEFAULT '',
    address VARCHAR(255) DEFAULT '',
    latitude DECIMAL(10,7) DEFAULT NULL,
    longitude DECIMAL(10,7) DEFAULT NULL,
    price_range VARCHAR(20) DEFAULT '',
    tags JSON DEFAULT NULL,
    is_recommended BOOL DEFAULT FALSE,
    view_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_foods_category (category_id),
    INDEX idx_foods_type (type),
    INDEX idx_foods_recommended (is_recommended),
    FULLTEXT INDEX idx_foods_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 非遗项目
CREATE TABLE IF NOT EXISTS heritages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    image_url VARCHAR(500) DEFAULT '',
    video_url VARCHAR(500) DEFAULT '',
    inheritor VARCHAR(50) DEFAULT '',
    region VARCHAR(50) NOT NULL,
    latitude DECIMAL(10,7) DEFAULT NULL,
    longitude DECIMAL(10,7) DEFAULT NULL,
    address VARCHAR(255) DEFAULT '',
    view_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_heritages_category (category),
    INDEX idx_heritages_type (type),
    INDEX idx_heritages_region (region),
    FULLTEXT INDEX idx_heritages_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 民俗活动/节日
CREATE TABLE IF NOT EXISTS folk_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    lunar_date VARCHAR(50) DEFAULT '',
    region VARCHAR(50) NOT NULL,
    latitude DECIMAL(10,7) DEFAULT NULL,
    longitude DECIMAL(10,7) DEFAULT NULL,
    address VARCHAR(255) DEFAULT '',
    image_url VARCHAR(500) DEFAULT '',
    event_type ENUM('festival','event','custom') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_events_date (event_date),
    INDEX idx_events_type (event_type),
    INDEX idx_events_region (region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户收藏
CREATE TABLE IF NOT EXISTS user_favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    item_type ENUM('food','heritage','event') NOT NULL,
    item_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fav_user (user_id),
    UNIQUE INDEX idx_fav_unique (user_id, item_type, item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 客服对话记录
CREATE TABLE IF NOT EXISTS chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT NULL,
    session_id VARCHAR(64) NOT NULL,
    role ENUM('user','assistant') NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_chat_session (session_id, created_at),
    INDEX idx_chat_user (user_id),
    INDEX idx_chat_user_session (user_id, session_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- AI 会话状态（Phase 5.5：持久化 intent_router + cs_agent 会话）
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL UNIQUE,
    user_id INT DEFAULT NULL,
    title VARCHAR(200) DEFAULT '新对话',
    intent_state JSON DEFAULT NULL COMMENT '{intent, collected_params, turn, interest_hints, recent_exchanges}',
    status ENUM('active','closed') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_user_updated (user_id, updated_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 行程计划
CREATE TABLE IF NOT EXISTS trip_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    days INT NOT NULL,
    crowd_type VARCHAR(20) NOT NULL,
    preferences JSON NOT NULL,
    plan_content JSON DEFAULT NULL,
    status VARCHAR(20) DEFAULT 'generated',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_trip_user (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 社区动态
CREATE TABLE IF NOT EXISTS community_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    images JSON DEFAULT NULL,
    tags JSON DEFAULT NULL,
    -- 标签搜索虚拟列（从 JSON 数组提取为空格分隔字符串）
    tags_text VARCHAR(500) GENERATED ALWAYS AS (
        JSON_UNQUOTE(JSON_EXTRACT(tags, '$'))
    ) STORED,
    post_type ENUM('recommend','challenge','social','study') NOT NULL,
    view_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_post_user (user_id, created_at),
    INDEX idx_post_type (post_type),
    INDEX idx_post_time (created_at),
    FULLTEXT INDEX idx_post_tags (tags_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 评论
CREATE TABLE IF NOT EXISTS post_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    parent_id INT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_comment_post (post_id, created_at),
    INDEX idx_comment_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 点赞
CREATE TABLE IF NOT EXISTS post_likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_like_unique (post_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 私信
CREATE TABLE IF NOT EXISTS private_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    content TEXT NOT NULL,
    is_read BOOL DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_msg_sender (sender_id, receiver_id, created_at),
    INDEX idx_msg_receiver (receiver_id, sender_id, created_at),
    INDEX idx_msg_unread (receiver_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 气象数据
CREATE TABLE IF NOT EXISTS weather_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region VARCHAR(50) NOT NULL,
    temperature DECIMAL(5,1) NOT NULL,
    humidity INT NOT NULL,
    weather_desc VARCHAR(50) NOT NULL,
    wind_level INT DEFAULT 0,
    record_time DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_weather_region_time (region, record_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 人流数据
CREATE TABLE IF NOT EXISTS crowd_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region VARCHAR(50) NOT NULL,
    location_name VARCHAR(100) NOT NULL,
    crowd_level INT NOT NULL,
    estimated_count INT DEFAULT 0,
    record_time DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_crowd_region_time (region, record_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 酒店
CREATE TABLE IF NOT EXISTS hotels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    region VARCHAR(50) NOT NULL,
    address VARCHAR(255) DEFAULT '',
    latitude DECIMAL(10,7) DEFAULT NULL,
    longitude DECIMAL(10,7) DEFAULT NULL,
    stars INT DEFAULT 3,
    price_min INT DEFAULT 0,
    price_max INT DEFAULT 0,
    image_url VARCHAR(500) DEFAULT '',
    tags JSON DEFAULT NULL,
    description TEXT,
    is_recommended BOOL DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_hotels_region (region),
    INDEX idx_hotels_stars (stars),
    INDEX idx_hotels_recommended (is_recommended)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 人流监测点（经纬度字典表）
CREATE TABLE IF NOT EXISTS crowd_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL,
    region VARCHAR(50) NOT NULL,
    latitude DECIMAL(10,7) NOT NULL,
    longitude DECIMAL(10,7) NOT NULL,
    base_capacity INT DEFAULT 1000,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_crowdloc_region (region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 兼容已有数据库的增量 DDL（若列已存在则忽略错误）
-- ============================================================

-- heritages 表新增地理坐标字段
ALTER TABLE heritages
    ADD COLUMN IF NOT EXISTS latitude DECIMAL(10,7) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS longitude DECIMAL(10,7) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS address VARCHAR(255) DEFAULT '';

-- folk_events 表新增地理坐标字段
ALTER TABLE folk_events
    ADD COLUMN IF NOT EXISTS latitude DECIMAL(10,7) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS longitude DECIMAL(10,7) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS address VARCHAR(255) DEFAULT '';
