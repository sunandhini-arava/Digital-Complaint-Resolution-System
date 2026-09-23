-- ============================================================
-- Complaint Management System - Complete Database Setup
-- Run: mysql -u root -p < setup_database.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS complaint_management
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE complaint_management;

-- ============================================================
-- TABLE: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     VARCHAR(50) UNIQUE NOT NULL COMMENT 'e.g. STU2024001, FAC001, ADM001',
    password    VARCHAR(255) NOT NULL,
    full_name   VARCHAR(100) NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    phone       VARCHAR(20),
    user_type   ENUM('student','faculty','administration','admin') NOT NULL,
    birthdate   DATE NOT NULL COMMENT 'Used for first-time activation',
    is_activated BOOLEAN DEFAULT FALSE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id   (user_id),
    INDEX idx_user_type (user_type)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: complaints
-- ============================================================
CREATE TABLE IF NOT EXISTS complaints (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id    VARCHAR(30) UNIQUE NOT NULL COMMENT 'e.g. CMP20240101ABCDEF',
    user_id         VARCHAR(50) NOT NULL,
    title           VARCHAR(200) NOT NULL,
    description     TEXT NOT NULL,
    category        ENUM('academic','infrastructure','administrative','technical','hostel','transport','other') NOT NULL,
    status          ENUM('pending','in-progress','resolved','closed','rejected') DEFAULT 'pending',
    priority        ENUM('low','medium','high','urgent') DEFAULT 'medium',
    admin_remarks   TEXT,
    assigned_to     INT,
    attachment_path VARCHAR(255),
    resolved_at     DATETIME,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES users(id)      ON DELETE SET NULL,
    INDEX idx_status    (status),
    INDEX idx_category  (category),
    INDEX idx_priority  (priority),
    INDEX idx_user_id   (user_id),
    INDEX idx_created   (created_at)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: complaint_updates  (audit trail)
-- ============================================================
CREATE TABLE IF NOT EXISTS complaint_updates (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id VARCHAR(30) NOT NULL,
    updated_by   INT NOT NULL,
    update_type  ENUM('status_change','comment','assignment','priority_change') NOT NULL,
    old_status   VARCHAR(20),
    new_status   VARCHAR(20),
    message      TEXT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    FOREIGN KEY (updated_by)   REFERENCES users(id)                ON DELETE CASCADE,
    INDEX idx_complaint_id (complaint_id)
) ENGINE=InnoDB;

-- ============================================================
-- SEED DATA: Default accounts
-- Passwords are bcrypt-hashed. Accounts need activation first
-- (except super admin who is pre-activated below).
-- ============================================================

-- Super Admin (pre-activated, password: Admin@1234)
-- Hash generated with: bcrypt.hashpw(b'Admin@1234', bcrypt.gensalt())
-- Re-generate after setup for security!
INSERT IGNORE INTO users
    (user_id, password, full_name, email, phone, user_type, birthdate, is_activated)
VALUES
    ('ADMIN001',
     '$2b$12$placeholder_run_seed_script_to_generate_real_hash',
     'Sunandhini',
     'admin@institution.edu',
     '9999999999',
     'admin',
     '2005-02-06',
     TRUE);

-- ============================================================
-- NOTES
-- ============================================================
-- 1. Replace the password hash above by running:
--       python seed_admin.py
--    which will insert the real bcrypt hash.
--
-- 2. For other users (students, faculty, administration):
--    - Create via Super Admin dashboard, OR insert with is_activated=FALSE
--    - User activates via /activate.html using their birthdate
--
-- Example insert for a student (not yet activated):
INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate)
VALUES ('23U51A0513','$2b$12$...','Arava Lakshmi Sowmya Sunandhini','alss@student.edu','9876543210','student','2005-02-06');

INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate)
VALUES ('23U51A0508','$2b$12$...','Allampally Nani','an@student.edu','9876543210','student','2005-12-09');

INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate)
VALUES ('23U51A0558','$2b$12$...','Kandukuri Roja Rani','krr@student.edu','9876543210','student','2005-09-07');

INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate)
VALUES ('23U51A0556','$2b$12$...','J.Sumanth','js@student.edu','9876543210','student','2002-05-15');

INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate)
VALUES ('23U51A0524','$2b$12$...','Bokka NavyaSri','bns@student.edu','9876543210','student','2005-09-10');

INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate)
VALUES ('23U51A0538','$2b$12$...','Duddi Nageshwari','dn@student.edu','9876543210','student','2005-01-27');

INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate)
VALUES ('23U51A0532','$2b$12$...','B.Ganesh Goud','bgg@student.edu','9876543210','student','2005-05-15');

INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate)
VALUES ('23U51A0514','$2b$12$...','A.Mani Kantha','amk@student.edu','9876543210','student','2004-05-15');

INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate)
VALUES ('23U51A0551','$2b$12$...','G.Bharath Kumar','gbk@student.edu','9876543210','student','2006-06-15');

INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate)
VALUES ('23U51A0552','$2b$12$...','H.Anjaneyulu','ha@student.edu','9876543210','student','2004-03-20');

INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate)
VALUES ('23U51A0539','$2b$12$...','D.Vinay','dv@student.edu','9876543210','student','2004-05-15');
