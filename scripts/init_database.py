"""
Initialize database and load BerkleyTime grade data
Phase 1.2: Database Setup
"""

import sqlite3
import json
from pathlib import Path

# Paths
DB_PATH = Path("data/courses.db")
SCHEMA_PATH = Path("schema.sql")
DATA_DIR = Path("data/raw/berkeleytime")

def init_database():
    """Create database and tables from schema"""
    print("Initializing database...")

    # Create data directory if needed
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database if present
    if DB_PATH.exists():
        print(f"Removing existing database at {DB_PATH}")
        DB_PATH.unlink()

    # Connect and create schema
    conn = sqlite3.connect(DB_PATH)

    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)
    conn.commit()

    print(f"Database created at {DB_PATH}")
    return conn

def load_course_data(conn):
    """Load all course data from JSON files into database"""
    print("\nLoading course data...")

    cursor = conn.cursor()
    courses_loaded = 0
    grades_loaded = 0

    for json_file in sorted(DATA_DIR.glob("*.json")):
        with open(json_file, 'r') as f:
            data = json.load(f)

        course_data = data.get("data", {}).get("course")

        if not course_data:
            print(f"  Skipping {json_file.name} - no course data")
            continue

        # Extract course info
        course_id = int(course_data["courseId"])
        subject = course_data["subject"]
        number = course_data["number"]
        avg_gpa = course_data["gradeDistribution"].get("average")
        distribution = course_data["gradeDistribution"].get("distribution", [])

        # Calculate total students
        total_students = sum(item["count"] for item in distribution)

        # Insert course
        try:
            cursor.execute("""
                INSERT INTO courses (course_id, subject, number, avg_gpa, total_students)
                VALUES (?, ?, ?, ?, ?)
            """, (course_id, subject, number, avg_gpa, total_students))
            courses_loaded += 1
            print(f"  Loaded {subject} {number} (ID: {course_id}, Students: {total_students})")
        except sqlite3.IntegrityError as e:
            print(f"  Error loading {subject} {number}: {e}")
            continue

        # Insert grade distribution
        for item in distribution:
            letter_grade = item["letter"]
            student_count = item["count"]
            percentage = (student_count / total_students * 100) if total_students > 0 else 0

            cursor.execute("""
                INSERT INTO grade_distributions (course_id, letter_grade, student_count, percentage)
                VALUES (?, ?, ?, ?)
            """, (course_id, letter_grade, student_count, percentage))
            grades_loaded += 1

    conn.commit()
    print(f"\nLoaded {courses_loaded} courses and {grades_loaded} grade records")
    return courses_loaded, grades_loaded

def validate_database(conn):
    """Run validation queries to check data integrity"""
    print("\n" + "=" * 80)
    print("DATABASE VALIDATION")
    print("=" * 80)

    cursor = conn.cursor()

    # Count courses
    cursor.execute("SELECT COUNT(*) FROM courses")
    course_count = cursor.fetchone()[0]
    print(f"Total courses in database: {course_count}")

    # Count grade records
    cursor.execute("SELECT COUNT(*) FROM grade_distributions")
    grade_count = cursor.fetchone()[0]
    print(f"Total grade distribution records: {grade_count}")

    # Check for courses with most students
    print("\nTop 5 courses by enrollment:")
    cursor.execute("""
        SELECT subject, number, total_students, avg_gpa
        FROM courses
        ORDER BY total_students DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} {row[1]}: {row[2]} students (GPA: {row[3]:.3f})")

    # Check hardest courses
    print("\nHardest courses (lowest GPA):")
    cursor.execute("""
        SELECT subject, number, avg_gpa, total_students
        FROM courses
        WHERE avg_gpa IS NOT NULL
        ORDER BY avg_gpa ASC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} {row[1]}: {row[2]:.3f} GPA ({row[3]} students)")

    # Check easiest courses
    print("\nEasiest courses (highest GPA):")
    cursor.execute("""
        SELECT subject, number, avg_gpa, total_students
        FROM courses
        WHERE avg_gpa IS NOT NULL
        ORDER BY avg_gpa DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} {row[1]}: {row[2]:.3f} GPA ({row[3]} students)")

    # Sample grade distribution
    print("\nSample grade distribution (COMPSCI 61A):")
    cursor.execute("""
        SELECT gd.letter_grade, gd.student_count, gd.percentage
        FROM grade_distributions gd
        JOIN courses c ON gd.course_id = c.course_id
        WHERE c.subject = 'COMPSCI' AND c.number = '61A'
        ORDER BY gd.student_count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:3s}: {row[1]:5d} students ({row[2]:5.2f}%)")

    print("\n" + "=" * 80)
    print("Database validation complete!")

def main():
    # Initialize database
    conn = init_database()

    # Load data
    load_course_data(conn)

    # Validate
    validate_database(conn)

    # Close connection
    conn.close()
    print(f"\nDatabase ready at: {DB_PATH}")

if __name__ == "__main__":
    main()
