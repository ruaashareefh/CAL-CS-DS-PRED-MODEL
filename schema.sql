-- Database schema for UC Berkeley Course Outcome Prediction Model
-- Phase 1.2: Database Design

-- Core course information
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY,
    subject TEXT NOT NULL,
    number TEXT NOT NULL,
    avg_gpa REAL,
    total_students INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subject, number)
);

-- Grade distributions for each course
CREATE TABLE IF NOT EXISTS grade_distributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    letter_grade TEXT NOT NULL,
    student_count INTEGER NOT NULL,
    percentage REAL,
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    UNIQUE(course_id, letter_grade)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_courses_subject ON courses(subject);
CREATE INDEX IF NOT EXISTS idx_courses_gpa ON courses(avg_gpa);
CREATE INDEX IF NOT EXISTS idx_grade_dist_course ON grade_distributions(course_id);
