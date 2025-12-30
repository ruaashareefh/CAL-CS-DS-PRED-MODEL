"""
Data Exploration and Validation for BerkleyTime Grade Data
Step 1.1: Understand what we have and identify any data quality issues
"""

import json
from pathlib import Path
import numpy as np
import sys

DATA_DIR = Path("data/raw/berkeleytime")
OUTPUT_FILE = Path("data/exploration_output.txt")

class Tee:
    """Write to both stdout and file"""
    def __init__(self, *files):
        self.files = files

    def write(self, data):
        for f in self.files:
            f.write(data)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()

def load_all_courses():
    """Load all course data from JSON files"""
    courses = []

    for json_file in DATA_DIR.glob("*.json"):
        with open(json_file, 'r') as f:
            data = json.load(f)

        # Extract course info
        course_data = data.get("data", {}).get("course")

        if course_data:
            courses.append({
                "file": json_file.name,
                "courseId": course_data.get("courseId"),
                "subject": course_data.get("subject"),
                "number": course_data.get("number"),
                "average": course_data.get("gradeDistribution", {}).get("average"),
                "distribution": course_data.get("gradeDistribution", {}).get("distribution"),
                "raw_data": course_data
            })

    return courses

def analyze_distribution(distribution):
    """Analyze a grade distribution"""
    if not distribution:
        return None

    # Convert to dict for easier access
    grade_counts = {item["letter"]: item["count"] for item in distribution}

    total_students = sum(grade_counts.values())

    # Skip if no students (data quality issue)
    if total_students == 0:
        return None

    # Calculate grade percentages
    grade_pcts = {grade: count/total_students for grade, count in grade_counts.items()}

    # Grade to GPA mapping
    grade_to_gpa = {
        "A+": 4.0, "A": 4.0, "A-": 3.7,
        "B+": 3.3, "B": 3.0, "B-": 2.7,
        "C+": 2.3, "C": 2.0, "C-": 1.7,
        "D+": 1.3, "D": 1.0, "D-": 0.7,
        "F": 0.0, "P": None, "NP": None
    }

    # Calculate weighted GPA (verify against reported average)
    weighted_gpa = sum(
        grade_to_gpa.get(grade, 0) * count
        for grade, count in grade_counts.items()
        if grade_to_gpa.get(grade) is not None
    )

    graded_students = sum(
        count for grade, count in grade_counts.items()
        if grade_to_gpa.get(grade) is not None
    )

    calculated_avg = weighted_gpa / graded_students if graded_students > 0 else None

    return {
        "total_students": total_students,
        "grade_counts": grade_counts,
        "grade_percentages": grade_pcts,
        "calculated_avg_gpa": calculated_avg,
        "num_unique_grades": len(grade_counts)
    }

def print_summary(courses):
    """Print summary statistics"""
    print("=" * 80)
    print("BERKELEYTIME GRADE DATA - EXPLORATION SUMMARY")
    print("=" * 80)
    print()

    print(f"Total courses fetched: {len(courses)}")
    print()

    # Group by subject
    subjects = {}
    for course in courses:
        subj = course["subject"]
        if subj not in subjects:
            subjects[subj] = []
        subjects[subj].append(course)

    print("Courses by subject:")
    for subj, subj_courses in subjects.items():
        print(f"  {subj}: {len(subj_courses)} courses")
    print()

    # Check data completeness
    print("Data Completeness Check:")
    courses_with_avg = sum(1 for c in courses if c["average"] is not None)
    courses_with_dist = sum(1 for c in courses if c["distribution"])

    print(f"  Courses with average GPA: {courses_with_avg}/{len(courses)}")
    print(f"  Courses with grade distribution: {courses_with_dist}/{len(courses)}")
    print()

    # GPA statistics
    gpas = [c["average"] for c in courses if c["average"] is not None]
    if gpas:
        print("GPA Statistics (across all courses):")
        print(f"  Mean GPA: {np.mean(gpas):.3f}")
        print(f"  Median GPA: {np.median(gpas):.3f}")
        print(f"  Std Dev: {np.std(gpas):.3f}")
        print(f"  Min GPA: {np.min(gpas):.3f} (easiest)")
        print(f"  Max GPA: {np.max(gpas):.3f} (hardest)")
        print()

    # Find extreme courses
    if gpas:
        sorted_courses = sorted(courses, key=lambda x: x["average"] if x["average"] else 0)

        print("Hardest Courses (lowest GPA):")
        for course in sorted_courses[:5]:
            if course["average"]:
                print(f"  {course['subject']} {course['number']}: {course['average']:.3f}")
        print()

        print("Easiest Courses (highest GPA):")
        for course in sorted_courses[-5:]:
            if course["average"]:
                print(f"  {course['subject']} {course['number']}: {course['average']:.3f}")
        print()

    return subjects

def detailed_course_analysis(courses):
    """Detailed analysis of grade distributions"""
    print("=" * 80)
    print("DETAILED GRADE DISTRIBUTION ANALYSIS")
    print("=" * 80)
    print()

    all_stats = []

    for course in courses:
        if not course["distribution"]:
            continue

        stats = analyze_distribution(course["distribution"])
        if stats:
            stats["course"] = f"{course['subject']} {course['number']}"
            stats["reported_avg"] = course["average"]
            all_stats.append(stats)

    # Sample: Show detailed breakdown for a few courses
    print("Sample Course Breakdowns:")
    print()

    sample_courses = ["COMPSCI 61A", "COMPSCI 170", "DATA C100"]

    for course_name in sample_courses:
        matching = [s for s in all_stats if s["course"] == course_name]
        if matching:
            stats = matching[0]
            print(f"{stats['course']}:")
            print(f"  Total Students: {stats['total_students']}")
            print(f"  Reported Avg GPA: {stats['reported_avg']:.3f}")
            print(f"  Calculated Avg GPA: {stats['calculated_avg_gpa']:.3f}")
            print(f"  Grade Distribution:")

            # Sort by GPA value
            grade_order = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]
            for grade in grade_order:
                if grade in stats['grade_percentages']:
                    pct = stats['grade_percentages'][grade] * 100
                    count = stats['grade_counts'][grade]
                    print(f"    {grade:3s}: {pct:5.1f}% ({count:4d} students)")
            print()

    # Distribution characteristics
    print("Distribution Characteristics:")
    print()

    total_students = [s["total_students"] for s in all_stats]
    print(f"  Avg students per course: {np.mean(total_students):.0f}")
    print(f"  Median students per course: {np.median(total_students):.0f}")
    print(f"  Range: {np.min(total_students):.0f} - {np.max(total_students):.0f}")
    print()

    # A grade percentages
    a_percentages = []
    for stats in all_stats:
        a_pct = sum(
            stats['grade_percentages'].get(grade, 0)
            for grade in ["A+", "A", "A-"]
        )
        a_percentages.append(a_pct)

    print(f"  Avg % receiving A-range grades: {np.mean(a_percentages)*100:.1f}%")
    print(f"  Range: {np.min(a_percentages)*100:.1f}% - {np.max(a_percentages)*100:.1f}%")
    print()

def data_quality_check(courses):
    """Check for data quality issues"""
    print("=" * 80)
    print("DATA QUALITY CHECKS")
    print("=" * 80)
    print()

    issues = []

    for course in courses:
        course_name = f"{course['subject']} {course['number']}"

        # Check for missing data
        if course["average"] is None:
            issues.append(f"{course_name}: Missing average GPA")

        if not course["distribution"]:
            issues.append(f"{course_name}: Missing grade distribution")

        # Check for inconsistencies
        if course["average"] and course["distribution"]:
            stats = analyze_distribution(course["distribution"])
            if stats and stats["calculated_avg_gpa"]:
                diff = abs(stats["calculated_avg_gpa"] - course["average"])
                if diff > 0.05:  # Tolerance of 0.05
                    issues.append(
                        f"{course_name}: GPA mismatch - "
                        f"Reported: {course['average']:.3f}, "
                        f"Calculated: {stats['calculated_avg_gpa']:.3f}"
                    )

    if issues:
        print(f"Found {len(issues)} potential issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")
    else:
        print("No data quality issues detected!")

    print()
    print("=" * 80)

def main():
    # Create output directory if needed
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Redirect stdout to both console and file
    with open(OUTPUT_FILE, 'w') as f:
        original_stdout = sys.stdout
        sys.stdout = Tee(sys.stdout, f)

        try:
            print("Loading course data...")
            courses = load_all_courses()
            print(f"Loaded {len(courses)} courses\n")

            # Run analyses
            print_summary(courses)
            detailed_course_analysis(courses)
            data_quality_check(courses)

            print("\nData exploration complete!")
            print(f"Data location: {DATA_DIR}")
            print(f"Output saved to: {OUTPUT_FILE}")
        finally:
            sys.stdout = original_stdout

if __name__ == "__main__":
    main()
