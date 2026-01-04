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

-- Grading structure metadata (manually collected)
CREATE TABLE IF NOT EXISTS grading_structure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    pct_exams REAL,
    pct_projects REAL,
    pct_homework REAL,
    pct_participation REAL,
    pct_other REAL,
    num_exams INTEGER,
    num_projects INTEGER,
    num_homeworks INTEGER,
    has_final_exam BOOLEAN,
    notes TEXT,
    source_url TEXT,
    collection_date TEXT,
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    UNIQUE(course_id)
);

-- Engineered features for modeling
CREATE TABLE IF NOT EXISTS course_features (
    course_id INTEGER PRIMARY KEY,

    -- Grade distribution features
    grade_entropy REAL,              -- Entropy of grade distribution (higher = more spread)
    grade_skewness REAL,             -- Skewness (negative = harder course)
    pct_a_range REAL,                -- % of students getting A+/A/A-
    pct_passing REAL,                -- % of students passing (C- or better)

    -- Grading structure features
    exam_heavy BOOLEAN,              -- TRUE if exams > 60%
    project_heavy BOOLEAN,           -- TRUE if projects > 25%
    has_projects BOOLEAN,            -- TRUE if any projects
    total_assessments INTEGER,       -- Total number of graded items

    -- Course characteristics
    course_level TEXT,               -- 'lower_div' (10-99) or 'upper_div' (100+)
    is_theory_course BOOLEAN,        -- TRUE if no projects (theory/math heavy)

    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_courses_subject ON courses(subject);
CREATE INDEX IF NOT EXISTS idx_courses_gpa ON courses(avg_gpa);
CREATE INDEX IF NOT EXISTS idx_grade_dist_course ON grade_distributions(course_id);
CREATE INDEX IF NOT EXISTS idx_grading_structure_course ON grading_structure(course_id);
CREATE INDEX IF NOT EXISTS idx_course_features_exam_heavy ON course_features(exam_heavy);
CREATE INDEX IF NOT EXISTS idx_course_features_level ON course_features(course_level);
