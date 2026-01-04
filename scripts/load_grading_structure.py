"""
Load grading structure CSV into database
Phase 2: Feature Engineering - Step 1

This script:
1. Updates database schema with new tables
2. Loads grading structure data from CSV
3. Links to existing courses by subject+number
"""

import sqlite3
import csv
from pathlib import Path

DB_PATH = Path("data/courses.db")
SCHEMA_PATH = Path("schema.sql")
GRADING_CSV = Path("data/grading_structure.csv")

def update_schema(conn):
    """Add new tables to database schema"""
    print("Updating database schema...")

    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)
    conn.commit()
    print("Schema updated successfully")

def load_grading_structure(conn):
    """Load grading structure data from CSV"""
    print("\nLoading grading structure data...")

    cursor = conn.cursor()
    loaded = 0
    skipped = 0

    with open(GRADING_CSV, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Skip if not collected yet
            if row['collected'] != 'yes':
                skipped += 1
                continue

            subject = row['subject']
            number = row['number']

            # Get course_id from courses table
            cursor.execute("""
                SELECT course_id FROM courses
                WHERE subject = ? AND number = ?
            """, (subject, number))

            result = cursor.fetchone()
            if not result:
                print(f"  Warning: Course {subject} {number} not found in database")
                skipped += 1
                continue

            course_id = result[0]

            # Convert boolean
            has_final = 1 if row['has_final_exam'].lower() == 'yes' else 0

            # Convert empty strings to None for numeric fields
            def to_float(val):
                return float(val) if val and val.strip() else None

            def to_int(val):
                # Handle approximate values like "~12"
                if val and val.strip():
                    val_clean = val.strip().replace('~', '')
                    try:
                        return int(val_clean)
                    except ValueError:
                        return None
                return None

            # Insert grading structure
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO grading_structure (
                        course_id, pct_exams, pct_projects, pct_homework,
                        pct_participation, pct_other, num_exams, num_projects,
                        num_homeworks, has_final_exam, notes, source_url, collection_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    course_id,
                    to_float(row['pct_exams']),
                    to_float(row['pct_projects']),
                    to_float(row['pct_homework']),
                    to_float(row['pct_participation']),
                    to_float(row['pct_other']),
                    to_int(row['num_exams']),
                    to_int(row['num_projects']),
                    to_int(row['num_homeworks']),
                    has_final,
                    row['notes'],
                    row['source_url'],
                    row['collection_date']
                ))

                loaded += 1
                print(f"  Loaded {subject} {number}")

            except sqlite3.IntegrityError as e:
                print(f"  Error loading {subject} {number}: {e}")
                skipped += 1

    conn.commit()
    print(f"\nLoaded {loaded} grading structures, skipped {skipped}")
    return loaded

def validate_data(conn):
    """Check what was loaded"""
    print("\n" + "=" * 80)
    print("VALIDATION: Grading Structure Data")
    print("=" * 80)

    cursor = conn.cursor()

    # Count loaded records
    cursor.execute("SELECT COUNT(*) FROM grading_structure")
    count = cursor.fetchone()[0]
    print(f"Total grading structures in database: {count}")

    # Show sample data with joins
    print("\nSample grading structures:")
    cursor.execute("""
        SELECT
            c.subject,
            c.number,
            c.avg_gpa,
            gs.pct_exams,
            gs.pct_projects,
            gs.pct_homework,
            gs.num_exams,
            gs.num_projects
        FROM grading_structure gs
        JOIN courses c ON gs.course_id = c.course_id
        ORDER BY c.total_students DESC
        LIMIT 5
    """)

    print("\n{:15} {:5} {:7} {:8} {:9} {:8}".format(
        "Course", "GPA", "Exams%", "Proj%", "HW%", "# Exams"
    ))
    print("-" * 70)

    for row in cursor.fetchall():
        subject, number, gpa, pct_ex, pct_proj, pct_hw, num_ex, num_proj = row
        course = f"{subject} {number}"
        print(f"{course:15} {gpa:5.2f} {pct_ex:7.1f}% {pct_proj:8.1f}% {pct_hw:7.1f}% {num_ex:7d}")

    print("\n" + "=" * 80)

def main():
    print("Phase 2: Loading Grading Structure Data")
    print("=" * 80)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    # Update schema
    update_schema(conn)

    # Load data
    loaded = load_grading_structure(conn)

    if loaded > 0:
        # Validate
        validate_data(conn)

    # Close connection
    conn.close()

    print(f"\nDone! Database updated at: {DB_PATH}")

if __name__ == "__main__":
    main()
