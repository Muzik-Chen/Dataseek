-- 认证系统迁移：手机号 → 邮箱
-- 执行前请备份数据库！

-- 1. 清空旧数据
DELETE FROM login_attempts;
DELETE FROM sms_codes;
DELETE FROM chat_messages;
DELETE FROM chat_sessions;
DELETE FROM post_likes;
DELETE FROM post_comments;
DELETE FROM community_posts;
DELETE FROM private_messages;
DELETE FROM trip_plans;
DELETE FROM user_favorites;
DELETE FROM users;

-- 2. 改 users 表结构
ALTER TABLE users ADD COLUMN email VARCHAR(255) UNIQUE NOT NULL AFTER id;
ALTER TABLE users MODIFY COLUMN phone VARCHAR(11) NULL;
ALTER TABLE users DROP INDEX idx_users_phone;
ALTER TABLE users ADD INDEX idx_users_email (email);

-- 3. 改 sms_codes 表结构（复用 phone 字段存邮箱）
ALTER TABLE sms_codes MODIFY COLUMN phone VARCHAR(255) NOT NULL;

-- 4. 改 login_attempts 表结构（复用 phone 字段存邮箱）
ALTER TABLE login_attempts MODIFY COLUMN phone VARCHAR(255) NOT NULL;
