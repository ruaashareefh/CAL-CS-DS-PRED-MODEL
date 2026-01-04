"""
Database query functions for accessing course data
"""
import sqlite3
from typing import Dict, List, Optional


def get_course_features(conn: sqlite3.Connection, course_id: int) -> Dict:
    """
    Fetch all features for a specific course to use in prediction

    Args:
        conn: Database connection
        course_id: Course ID

    Returns:
        dict: Feature values with feature names as keys

    Raises:
        ValueError: If course_id not found
    """
    query = """
    SELECT
        -- Grade distribution features (available for all courses)
        cf.grade_entropy,
        cf.grade_skewness,
        cf.pct_a_range,
        cf.pct_passing,

        -- Grading structure boolean flags
        cf.exam_heavy,
        cf.project_heavy,
        cf.has_projects,
        cf.is_theory_course,
        cf.total_assessments,
        cf.course_level,

        -- Grading percentages (only available for some courses)
        gs.pct_exams,
        gs.pct_projects,
        gs.pct_homework,

        -- For upper_div encoding
        CASE WHEN cf.course_level = 'upper_div' THEN 1 ELSE 0 END as is_upper_div

    FROM course_features cf
    LEFT JOIN grading_structure gs ON cf.course_id = gs.course_id
    WHERE cf.course_id = ?
    """

    cursor = conn.cursor()
    cursor.execute(query, (course_id,))
    row = cursor.fetchone()

    if not row:
        raise ValueError(f"Course ID {course_id} not found in database")

    return dict(row)


def get_all_courses(
    conn: sqlite3.Connection,
    subject: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """
    Fetch all courses with their features

    Args:
        conn: Database connection
        subject: Optional filter by subject (e.g., "COMPSCI")
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        list: List of course dictionaries
    """
    query = """
    SELECT
        c.course_id,
        c.subject,
        c.number,
        c.subject || ' ' || c.number as full_name,
        c.avg_gpa,
        c.total_students,

        -- Features
        cf.grade_entropy,
        cf.grade_skewness,
        cf.pct_a_range,
        cf.pct_passing,

        -- Check if course has grading structure
        EXISTS(SELECT 1 FROM grading_structure gs WHERE gs.course_id = c.course_id) as has_grading_structure

    FROM courses c
    LEFT JOIN course_features cf ON c.course_id = cf.course_id
    WHERE (? IS NULL OR c.subject = ?)
    ORDER BY c.total_students DESC
    LIMIT ? OFFSET ?
    """

    cursor = conn.cursor()
    cursor.execute(query, (subject, subject, limit, offset))
    rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_course_by_id(conn: sqlite3.Connection, course_id: int) -> Optional[Dict]:
    """
    Fetch single course with grade distribution and grading structure

    Args:
        conn: Database connection
        course_id: Course ID

    Returns:
        dict: Course data including grade distribution, or None if not found
    """
    # Get course metadata and features
    course_query = """
    SELECT
        c.course_id,
        c.subject,
        c.number,
        c.subject || ' ' || c.number as full_name,
        c.avg_gpa,
        c.total_students,

        -- Features
        cf.grade_entropy,
        cf.grade_skewness,
        cf.pct_a_range,
        cf.pct_passing

    FROM courses c
    LEFT JOIN course_features cf ON c.course_id = cf.course_id
    WHERE c.course_id = ?
    """

    cursor = conn.cursor()
    cursor.execute(course_query, (course_id,))
    course_row = cursor.fetchone()

    if not course_row:
        return None

    course_data = dict(course_row)

    # Get grade distribution
    grade_query = """
    SELECT letter_grade, percentage
    FROM grade_distributions
    WHERE course_id = ?
    ORDER BY
        CASE letter_grade
            WHEN 'A+' THEN 1 WHEN 'A' THEN 2 WHEN 'A-' THEN 3
            WHEN 'B+' THEN 4 WHEN 'B' THEN 5 WHEN 'B-' THEN 6
            WHEN 'C+' THEN 7 WHEN 'C' THEN 8 WHEN 'C-' THEN 9
            WHEN 'D+' THEN 10 WHEN 'D' THEN 11 WHEN 'D-' THEN 12
            WHEN 'F' THEN 13
            ELSE 14
        END
    """

    cursor.execute(grade_query, (course_id,))
    grade_rows = cursor.fetchall()
    course_data['grade_distribution'] = [dict(row) for row in grade_rows]

    # Get grading structure (if available)
    grading_query = """
    SELECT
        pct_exams,
        pct_projects,
        pct_homework,
        pct_participation,
        pct_other,
        num_exams,
        num_projects,
        num_homeworks,
        has_final_exam,
        notes,
        source_url
    FROM grading_structure
    WHERE course_id = ?
    """

    cursor.execute(grading_query, (course_id,))
    grading_row = cursor.fetchone()
    course_data['grading_structure'] = dict(grading_row) if grading_row else None

    return course_data


def get_total_courses(conn: sqlite3.Connection, subject: Optional[str] = None) -> int:
    """
    Count total courses for pagination

    Args:
        conn: Database connection
        subject: Optional filter by subject

    Returns:
        int: Total number of courses
    """
    query = """
    SELECT COUNT(*) as count
    FROM courses
    WHERE (? IS NULL OR subject = ?)
    """

    cursor = conn.cursor()
    cursor.execute(query, (subject, subject))
    row = cursor.fetchone()

    return row['count'] if row else 0


def get_course_by_name(
    conn: sqlite3.Connection,
    subject: str,
    number: str
) -> Optional[Dict]:
    """
    Find course by subject and number

    Args:
        conn: Database connection
        subject: Course subject (e.g., "COMPSCI")
        number: Course number (e.g., "61A")

    Returns:
        dict: Course data, or None if not found
    """
    query = """
    SELECT course_id
    FROM courses
    WHERE subject = ? AND number = ?
    """

    cursor = conn.cursor()
    cursor.execute(query, (subject, number))
    row = cursor.fetchone()

    if not row:
        return None

    return get_course_by_id(conn, row['course_id'])


def get_course_averages(
    conn: sqlite3.Connection,
    course_names: List[str]
) -> Dict[str, float]:
    """
    Get average GPAs for multiple courses by name.

    Args:
        conn: Database connection
        course_names: List of course names (e.g., ['COMPSCI 61A', 'DATA C8'])

    Returns:
        dict: Mapping of course_name -> avg_gpa
              Only includes courses found in database
    """
    result = {}

    for course_name in course_names:
        # Parse course name (e.g., "COMPSCI 61A" -> subject="COMPSCI", number="61A")
        parts = course_name.strip().split()
        if len(parts) < 2:
            continue  # Invalid format, skip

        subject = parts[0]
        number = ' '.join(parts[1:])  # Handle numbers like "C8" or "169A"

        # Query for this course
        query = """
        SELECT avg_gpa
        FROM courses
        WHERE subject = ? AND number = ?
        """

        cursor = conn.cursor()
        cursor.execute(query, (subject, number))
        row = cursor.fetchone()

        if row and row['avg_gpa'] is not None:
            result[course_name] = row['avg_gpa']

    return result
