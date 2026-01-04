-- Useful SQL Queries for Exploring Course Data
-- Run these with: sqlite3 data/courses.db < docs/useful_queries.sql
-- Or interactively: sqlite3 data/courses.db

-- =============================================================================
-- BASIC EXPLORATION
-- =============================================================================

-- Show all features for a specific course
SELECT c.*, cf.*, gs.*
FROM courses c
LEFT JOIN course_features cf ON c.course_id = cf.course_id
LEFT JOIN grading_structure gs ON c.course_id = gs.course_id
WHERE c.subject = 'COMPSCI' AND c.number = '61A';

-- Top 10 courses by enrollment
SELECT subject || ' ' || number as course, total_students, avg_gpa
FROM courses
ORDER BY total_students DESC
LIMIT 10;

-- =============================================================================
-- FEATURE ANALYSIS
-- =============================================================================

-- Correlation between exam percentage and GPA
SELECT
    c.subject || ' ' || c.number as course,
    c.avg_gpa,
    gs.pct_exams,
    cf.pct_a_range
FROM courses c
JOIN grading_structure gs ON c.course_id = gs.course_id
JOIN course_features cf ON c.course_id = cf.course_id
ORDER BY gs.pct_exams DESC;

-- Find courses with specific characteristics
SELECT
    c.subject || ' ' || c.number as course,
    c.avg_gpa,
    cf.exam_heavy,
    cf.project_heavy,
    cf.is_theory_course
FROM courses c
JOIN course_features cf ON c.course_id = cf.course_id
WHERE cf.exam_heavy = 1 OR cf.is_theory_course = 1;

-- =============================================================================
-- GRADE DISTRIBUTION QUERIES
-- =============================================================================

-- Get full grade distribution for a course
SELECT
    c.subject || ' ' || c.number as course,
    gd.letter_grade,
    gd.student_count,
    gd.percentage
FROM courses c
JOIN grade_distributions gd ON c.course_id = gd.course_id
WHERE c.subject = 'COMPSCI' AND c.number = '170'
ORDER BY gd.student_count DESC;

-- Courses with highest entropy (most spread out grades)
SELECT
    c.subject || ' ' || c.number as course,
    c.avg_gpa,
    cf.grade_entropy,
    cf.pct_a_range
FROM courses c
JOIN course_features cf ON c.course_id = cf.course_id
ORDER BY cf.grade_entropy DESC
LIMIT 10;

-- =============================================================================
-- COMPARATIVE ANALYSIS
-- =============================================================================

-- Compare CS vs DATA courses
SELECT
    c.subject,
    COUNT(*) as num_courses,
    ROUND(AVG(c.avg_gpa), 3) as avg_gpa,
    ROUND(AVG(cf.pct_a_range), 1) as avg_pct_a
FROM courses c
JOIN course_features cf ON c.course_id = cf.course_id
GROUP BY c.subject;

-- Lower vs Upper division comparison
SELECT
    cf.course_level,
    COUNT(*) as num_courses,
    ROUND(AVG(c.avg_gpa), 3) as avg_gpa,
    ROUND(AVG(cf.pct_a_range), 1) as avg_pct_a,
    ROUND(AVG(cf.grade_entropy), 2) as avg_entropy
FROM courses c
JOIN course_features cf ON c.course_id = cf.course_id
GROUP BY cf.course_level;

-- =============================================================================
-- GRADING STRUCTURE ANALYSIS
-- =============================================================================

-- Courses ordered by exam percentage
SELECT
    c.subject || ' ' || c.number as course,
    c.avg_gpa,
    gs.pct_exams,
    gs.pct_projects,
    gs.pct_homework,
    gs.num_exams
FROM courses c
JOIN grading_structure gs ON c.course_id = gs.course_id
ORDER BY gs.pct_exams DESC;

-- Courses with most assessments
SELECT
    c.subject || ' ' || c.number as course,
    cf.total_assessments,
    gs.num_exams,
    gs.num_projects,
    gs.num_homeworks
FROM courses c
JOIN course_features cf ON c.course_id = cf.course_id
JOIN grading_structure gs ON c.course_id = gs.course_id
ORDER BY cf.total_assessments DESC;

-- =============================================================================
-- FINDING OUTLIERS
-- =============================================================================

-- Hardest courses (lowest GPA, most negative skew)
SELECT
    c.subject || ' ' || c.number as course,
    c.avg_gpa,
    c.total_students,
    cf.grade_skewness,
    cf.pct_a_range
FROM courses c
JOIN course_features cf ON c.course_id = cf.course_id
ORDER BY c.avg_gpa ASC
LIMIT 5;

-- Easiest courses (highest GPA)
SELECT
    c.subject || ' ' || c.number as course,
    c.avg_gpa,
    c.total_students,
    cf.pct_a_range
FROM courses c
JOIN course_features cf ON c.course_id = cf.course_id
ORDER BY c.avg_gpa DESC
LIMIT 5;

-- =============================================================================
-- MODELING PREPARATION
-- =============================================================================

-- All features for all courses (ready for ML)
SELECT
    c.course_id,
    c.subject || ' ' || c.number as course,
    c.avg_gpa as target,
    c.total_students,
    cf.grade_entropy,
    cf.grade_skewness,
    cf.pct_a_range,
    cf.pct_passing,
    cf.exam_heavy,
    cf.project_heavy,
    cf.has_projects,
    cf.is_theory_course,
    cf.total_assessments,
    cf.course_level,
    gs.pct_exams,
    gs.pct_projects,
    gs.pct_homework,
    gs.num_exams,
    gs.num_projects
FROM courses c
LEFT JOIN course_features cf ON c.course_id = cf.course_id
LEFT JOIN grading_structure gs ON c.course_id = gs.course_id
ORDER BY c.total_students DESC;
