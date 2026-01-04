"""
Feature Engineering for Course Outcome Prediction
Phase 2: Calculate features from grade distributions and grading structures

Features calculated:
1. Grade distribution features (entropy, skewness, % A-range)
2. Grading structure features (exam_heavy, project_heavy)
3. Course characteristics (level, is_theory)
"""

import sqlite3
import numpy as np
from pathlib import Path
from scipy.stats import entropy, skew

DB_PATH = Path("data/courses.db")

# Grade to GPA mapping for calculations
GRADE_TO_GPA = {
    "A+": 4.0, "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0, "D-": 0.7,
    "F": 0.0
}

A_RANGE_GRADES = ["A+", "A", "A-"]
PASSING_GRADES = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def calculate_grade_distribution_features(conn):
    """Calculate features from grade distributions"""
    print("Calculating grade distribution features...")

    cursor = conn.cursor()

    # Get all courses with grade distributions
    cursor.execute("""
        SELECT DISTINCT course_id FROM grade_distributions
    """)

    course_ids = [row[0] for row in cursor.fetchall()]
    features_calculated = 0

    for course_id in course_ids:
        # Get grade distribution for this course
        cursor.execute("""
            SELECT letter_grade, student_count, percentage
            FROM grade_distributions
            WHERE course_id = ?
            ORDER BY student_count DESC
        """, (course_id,))

        grades = cursor.fetchall()

        if not grades:
            continue

        # Calculate features
        features = calculate_distribution_features(grades)

        # Insert or update course_features
        cursor.execute("""
            INSERT OR REPLACE INTO course_features (
                course_id, grade_entropy, grade_skewness,
                pct_a_range, pct_passing
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            course_id,
            features['entropy'],
            features['skewness'],
            features['pct_a_range'],
            features['pct_passing']
        ))

        features_calculated += 1

    conn.commit()
    print(f"  Calculated features for {features_calculated} courses")
    return features_calculated

def calculate_distribution_features(grades):
    """Calculate statistical features from grade distribution"""

    # Filter to letter grades only (exclude P/NP/S/U)
    letter_grades = [(g[0], g[1], g[2]) for g in grades if g[0] in GRADE_TO_GPA]

    if not letter_grades:
        return {
            'entropy': None,
            'skewness': None,
            'pct_a_range': None,
            'pct_passing': None
        }

    # Extract data
    grade_labels = [g[0] for g in letter_grades]
    counts = np.array([g[1] for g in letter_grades])
    percentages = counts / counts.sum()

    # Calculate entropy (higher = more spread out distribution)
    grade_entropy = entropy(percentages, base=2)

    # Calculate skewness using GPA values (negative = left-skewed = harder)
    gpa_values = np.array([GRADE_TO_GPA[g] for g in grade_labels])
    weighted_gpas = np.repeat(gpa_values, counts)
    grade_skewness = skew(weighted_gpas)

    # Calculate % A-range
    a_count = sum(c for g, c, _ in letter_grades if g in A_RANGE_GRADES)
    pct_a_range = (a_count / counts.sum()) * 100

    # Calculate % passing (C- or better)
    passing_count = sum(c for g, c, _ in letter_grades if g in PASSING_GRADES)
    pct_passing = (passing_count / counts.sum()) * 100

    return {
        'entropy': grade_entropy,
        'skewness': grade_skewness,
        'pct_a_range': pct_a_range,
        'pct_passing': pct_passing
    }

def calculate_grading_structure_features(conn):
    """Calculate features from grading structure"""
    print("\nCalculating grading structure features...")

    cursor = conn.cursor()

    # Get all courses with grading structure
    cursor.execute("""
        SELECT
            gs.course_id,
            gs.pct_exams,
            gs.pct_projects,
            gs.num_exams,
            gs.num_projects,
            gs.num_homeworks
        FROM grading_structure gs
    """)

    features_calculated = 0

    for row in cursor.fetchall():
        course_id, pct_exams, pct_projects, num_exams, num_projects, num_homeworks = row

        # Calculate boolean flags
        exam_heavy = 1 if pct_exams and pct_exams > 60 else 0
        project_heavy = 1 if pct_projects and pct_projects > 25 else 0
        has_projects = 1 if pct_projects and pct_projects > 0 else 0
        is_theory = 1 if not has_projects else 0

        # Calculate total assessments
        total_assessments = 0
        if num_exams:
            total_assessments += num_exams
        if num_projects:
            total_assessments += num_projects
        if num_homeworks:
            total_assessments += num_homeworks

        # Update course_features
        cursor.execute("""
            INSERT INTO course_features (course_id, exam_heavy, project_heavy,
                                        has_projects, is_theory_course, total_assessments)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(course_id) DO UPDATE SET
                exam_heavy = excluded.exam_heavy,
                project_heavy = excluded.project_heavy,
                has_projects = excluded.has_projects,
                is_theory_course = excluded.is_theory_course,
                total_assessments = excluded.total_assessments
        """, (course_id, exam_heavy, project_heavy, has_projects, is_theory, total_assessments))

        features_calculated += 1

    conn.commit()
    print(f"  Calculated features for {features_calculated} courses")
    return features_calculated

def calculate_course_characteristics(conn):
    """Calculate course-level characteristics"""
    print("\nCalculating course characteristics...")

    cursor = conn.cursor()

    # Get all courses
    cursor.execute("SELECT course_id, number FROM courses")

    features_calculated = 0

    for course_id, number in cursor.fetchall():
        # Determine course level based on course number
        # Extract numeric part
        numeric_part = ''.join(filter(str.isdigit, number))

        if numeric_part:
            course_num = int(numeric_part)
            course_level = 'lower_div' if course_num < 100 else 'upper_div'
        else:
            course_level = 'unknown'

        # Update course_features
        cursor.execute("""
            INSERT INTO course_features (course_id, course_level)
            VALUES (?, ?)
            ON CONFLICT(course_id) DO UPDATE SET
                course_level = excluded.course_level
        """, (course_id, course_level))

        features_calculated += 1

    conn.commit()
    print(f"  Calculated characteristics for {features_calculated} courses")
    return features_calculated

def display_feature_summary(conn):
    """Display summary of engineered features"""
    print("\n" + "=" * 80)
    print("FEATURE ENGINEERING SUMMARY")
    print("=" * 80)

    cursor = conn.cursor()

    # Count features
    cursor.execute("SELECT COUNT(*) FROM course_features")
    total = cursor.fetchone()[0]
    print(f"Total courses with features: {total}")

    # Show sample features
    print("\nSample engineered features (top 5 courses by enrollment):")
    cursor.execute("""
        SELECT
            c.subject || ' ' || c.number as course,
            c.avg_gpa,
            cf.grade_entropy,
            cf.grade_skewness,
            cf.pct_a_range,
            cf.exam_heavy,
            cf.project_heavy,
            cf.has_projects,
            cf.course_level
        FROM course_features cf
        JOIN courses c ON cf.course_id = c.course_id
        ORDER BY c.total_students DESC
        LIMIT 5
    """)

    print("\n{:15} {:5} {:8} {:8} {:8} {:10} {:12} {:12} {:10}".format(
        "Course", "GPA", "Entropy", "Skew", "%A", "ExamHeavy", "ProjHeavy", "HasProj", "Level"
    ))
    print("-" * 110)

    for row in cursor.fetchall():
        course, gpa, ent, skew, pct_a, exam_h, proj_h, has_p, level = row

        # Handle None values
        ent_str = f"{ent:.2f}" if ent is not None else "N/A"
        skew_str = f"{skew:.2f}" if skew is not None else "N/A"
        pct_a_str = f"{pct_a:.1f}%" if pct_a is not None else "N/A"
        exam_h_str = "Yes" if exam_h else "No"
        proj_h_str = "Yes" if proj_h else "No"
        has_p_str = "Yes" if has_p else "No"
        level_str = level if level else "N/A"

        print(f"{course:15} {gpa:5.2f} {ent_str:8} {skew_str:8} {pct_a_str:8} {exam_h_str:10} {proj_h_str:12} {has_p_str:12} {level_str:10}")

    # Feature statistics
    print("\n" + "=" * 80)
    print("Feature Statistics:")
    print("=" * 80)

    # Entropy stats
    cursor.execute("SELECT AVG(grade_entropy), MIN(grade_entropy), MAX(grade_entropy) FROM course_features WHERE grade_entropy IS NOT NULL")
    avg_ent, min_ent, max_ent = cursor.fetchone()
    print(f"Grade Entropy: avg={avg_ent:.2f}, range=[{min_ent:.2f}, {max_ent:.2f}]")

    # Skewness stats
    cursor.execute("SELECT AVG(grade_skewness), MIN(grade_skewness), MAX(grade_skewness) FROM course_features WHERE grade_skewness IS NOT NULL")
    avg_skew, min_skew, max_skew = cursor.fetchone()
    print(f"Grade Skewness: avg={avg_skew:.2f}, range=[{min_skew:.2f}, {max_skew:.2f}]")

    # % A-range stats
    cursor.execute("SELECT AVG(pct_a_range), MIN(pct_a_range), MAX(pct_a_range) FROM course_features WHERE pct_a_range IS NOT NULL")
    avg_a, min_a, max_a = cursor.fetchone()
    print(f"% A-range grades: avg={avg_a:.1f}%, range=[{min_a:.1f}%, {max_a:.1f}%]")

    # Categorical features
    cursor.execute("SELECT COUNT(*) FROM course_features WHERE exam_heavy = 1")
    exam_heavy_count = cursor.fetchone()[0]
    print(f"\nExam-heavy courses (>60% exams): {exam_heavy_count}/{total}")

    cursor.execute("SELECT COUNT(*) FROM course_features WHERE project_heavy = 1")
    proj_heavy_count = cursor.fetchone()[0]
    print(f"Project-heavy courses (>25% projects): {proj_heavy_count}/{total}")

    cursor.execute("SELECT COUNT(*) FROM course_features WHERE is_theory_course = 1")
    theory_count = cursor.fetchone()[0]
    print(f"Theory courses (no projects): {theory_count}/{total}")

    cursor.execute("SELECT COUNT(*) FROM course_features WHERE course_level = 'upper_div'")
    upper_div_count = cursor.fetchone()[0]
    print(f"Upper division courses: {upper_div_count}/{total}")

    print("\n" + "=" * 80)

def main():
    print("=" * 80)
    print("PHASE 2: FEATURE ENGINEERING")
    print("=" * 80)
    print()

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    # Calculate all features
    calculate_grade_distribution_features(conn)
    calculate_grading_structure_features(conn)
    calculate_course_characteristics(conn)

    # Display summary
    display_feature_summary(conn)

    # Close connection
    conn.close()

    print(f"\nFeature engineering complete!")
    print(f"Database: {DB_PATH}")

if __name__ == "__main__":
    main()
