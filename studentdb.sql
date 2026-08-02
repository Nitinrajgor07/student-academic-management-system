-- ============================================================
--  STUDENT MANAGEMENT SYSTEM — COMPLETE DATABASE SETUP
--  Student Management System | Run this full file in MySQL Workbench
-- ============================================================

CREATE DATABASE IF NOT EXISTS studentdb;
USE studentdb;

SET SQL_SAFE_UPDATES = 0;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- STEP 1 : STUDENTS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS students (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100),
    email         VARCHAR(100) UNIQUE,
    course        VARCHAR(50),
    marks         INT,
    password      VARCHAR(100),
    java          INT,
    python        INT,
    ml            INT,
    blockchain    INT,
    ds            INT,
    adbms         INT,
    phone         VARCHAR(15),
    dob           DATE,
    gender        VARCHAR(10),
    address       TEXT,
    enrollment_no VARCHAR(20),
    semester      INT DEFAULT 1,
    profile_photo VARCHAR(255)
);

-- If table already exists, safely add only missing columns
ALTER TABLE students ADD COLUMN IF NOT EXISTS phone         VARCHAR(15);
ALTER TABLE students ADD COLUMN IF NOT EXISTS dob           DATE;
ALTER TABLE students ADD COLUMN IF NOT EXISTS gender        VARCHAR(10);
ALTER TABLE students ADD COLUMN IF NOT EXISTS address       TEXT;
ALTER TABLE students ADD COLUMN IF NOT EXISTS enrollment_no VARCHAR(20);
ALTER TABLE students ADD COLUMN IF NOT EXISTS semester      INT DEFAULT 1;
ALTER TABLE students ADD COLUMN IF NOT EXISTS profile_photo VARCHAR(255);

-- ============================================================
-- STEP 2 : TIMETABLE TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS timetable (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    day     VARCHAR(20),
    subject VARCHAR(50),
    time    VARCHAR(20)
);

DELETE FROM timetable;

INSERT INTO timetable (day, subject, time) VALUES
('Monday',    'Java',       '11:45 - 12:30'),
('Monday',    'Python',     '12:35 - 1:20'),
('Monday',    'Break',      '1:25 - 2:10'),
('Monday',    'ML',         '2:15 - 3:00'),
('Tuesday',   'ML',         '11:45 - 12:30'),
('Tuesday',   'Python',     '12:35 - 1:20'),
('Tuesday',   'Break',      '1:25 - 2:10'),
('Tuesday',   'Java',       '2:15 - 3:00'),
('Wednesday', 'Python',     '11:45 - 12:30'),
('Wednesday', 'ML',         '12:35 - 1:20'),
('Wednesday', 'Break',      '1:25 - 2:10'),
('Wednesday', 'Blockchain', '2:15 - 3:00'),
('Thursday',  'DS',         '11:45 - 12:30'),
('Thursday',  'Java',       '12:35 - 1:20'),
('Thursday',  'Break',      '1:25 - 2:10'),
('Thursday',  'Python',     '2:15 - 3:00'),
('Friday',    'ADBMS',      '11:45 - 12:30'),
('Friday',    'DS',         '12:35 - 1:20'),
('Friday',    'Break',      '1:25 - 2:10'),
('Friday',    'ML',         '2:15 - 3:00');

-- ============================================================
-- STEP 3 : ATTENDANCE TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS attendance (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    date       DATE,
    java       VARCHAR(10),
    python     VARCHAR(10),
    ml         VARCHAR(10),
    blockchain VARCHAR(10),
    ds         VARCHAR(10),
    adbms      VARCHAR(10)
);

-- ============================================================
-- STEP 4 : MARKS TABLE
-- ============================================================

DROP TABLE IF EXISTS marks;

CREATE TABLE marks (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    type       VARCHAR(20),
    java       INT,
    python     INT,
    ml         INT,
    blockchain INT,
    ds         INT,
    adbms      INT,
    UNIQUE KEY unique_student_type (student_id, type)
);

-- ============================================================
-- STEP 5 : UPDATE EXISTING STUDENT PASSWORDS
-- ============================================================

UPDATE students SET password='Rahul@123'  WHERE email='rahul@gmail.com';
UPDATE students SET password='Pulkit@123' WHERE email='pulkit22@gmail.com';
UPDATE students SET password='Manav@123'  WHERE email='manav22@gmail.com';
UPDATE students SET password='Aum@123'    WHERE email='aum13@gmail.com';
UPDATE students SET password='Dixit@2307' WHERE email='dixit22@gmail.com';

-- ============================================================
-- STEP 6 : VERIFY ALL TABLES
-- ============================================================

DESC students;
SELECT * FROM students;
DESC timetable;
SELECT * FROM timetable;
DESC attendance;
DESC marks;

-- ============================================================
-- STEP 7 : USER PERMISSIONS (uncomment if user missing)
-- ============================================================

-- CREATE USER IF NOT EXISTS 'studentuser'@'localhost' IDENTIFIED WITH mysql_native_password BY '1234';
-- GRANT ALL PRIVILEGES ON studentdb.* TO 'studentuser'@'localhost';
-- FLUSH PRIVILEGES;
