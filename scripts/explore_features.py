"""
Feature Exploration and Analysis
Interactive exploration of engineered features for course outcome prediction
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

DB_PATH = Path("data/courses.db")
OUTPUT_DIR = Path("data/analysis")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_all_features():
    """Load all features from database into pandas DataFrame"""
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        c.course_id,
        c.subject,
        c.number,
        c.subject || ' ' || c.number as course,
        c.avg_gpa,
        c.total_students,

        -- Grade distribution features
        cf.grade_entropy,
        cf.grade_skewness,
        cf.pct_a_range,
        cf.pct_passing,

        -- Grading structure features
        cf.exam_heavy,
        cf.project_heavy,
        cf.has_projects,
        cf.is_theory_course,
        cf.total_assessments,
        cf.course_level,

        -- Grading percentages (if available)
        gs.pct_exams,
        gs.pct_projects,
        gs.pct_homework,
        gs.num_exams,
        gs.num_projects,
        gs.num_homeworks

    FROM courses c
    LEFT JOIN course_features cf ON c.course_id = cf.course_id
    LEFT JOIN grading_structure gs ON c.course_id = gs.course_id
    ORDER BY c.total_students DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df

def analyze_correlations(df):
    """Analyze correlations between features and GPA"""
    print("=" * 80)
    print("FEATURE CORRELATIONS WITH AVERAGE GPA")
    print("=" * 80)
    print()

    # Select numeric columns for correlation
    numeric_cols = [
        'grade_entropy', 'grade_skewness', 'pct_a_range', 'pct_passing',
        'total_assessments', 'pct_exams', 'pct_projects', 'pct_homework',
        'total_students'
    ]

    correlations = []
    for col in numeric_cols:
        if col in df.columns:
            corr = df[['avg_gpa', col]].dropna().corr().iloc[0, 1]
            if not np.isnan(corr):
                correlations.append({'feature': col, 'correlation': corr})

    corr_df = pd.DataFrame(correlations).sort_values('correlation', ascending=False)

    print("Correlation with Average GPA (sorted by strength):")
    print()
    for _, row in corr_df.iterrows():
        feature = row['feature']
        corr = row['correlation']
        direction = "positive" if corr > 0 else "negative"
        strength = "strong" if abs(corr) > 0.5 else "moderate" if abs(corr) > 0.3 else "weak"

        print(f"  {feature:25s} {corr:+.3f}  ({strength} {direction})")

    print()
    return corr_df

def compare_course_types(df):
    """Compare exam-heavy vs project-heavy courses"""
    print("=" * 80)
    print("COURSE TYPE COMPARISON")
    print("=" * 80)
    print()

    # Filter to courses with grading structure data
    df_grading = df[df['pct_exams'].notna()].copy()

    if len(df_grading) == 0:
        print("No grading structure data available for comparison")
        return

    # Exam-heavy courses
    exam_heavy = df_grading[df_grading['exam_heavy'] == 1]
    # Project-heavy courses
    project_heavy = df_grading[df_grading['project_heavy'] == 1]
    # Balanced courses (neither exam nor project heavy)
    balanced = df_grading[(df_grading['exam_heavy'] == 0) & (df_grading['project_heavy'] == 0)]

    print(f"Total courses with grading data: {len(df_grading)}")
    print(f"  - Exam-heavy (>60% exams):    {len(exam_heavy)}")
    print(f"  - Project-heavy (>25% proj):  {len(project_heavy)}")
    print(f"  - Balanced:                   {len(balanced)}")
    print()

    print("Average GPA by course type:")
    print(f"  Exam-heavy:    {exam_heavy['avg_gpa'].mean():.3f}")
    print(f"  Project-heavy: {project_heavy['avg_gpa'].mean():.3f}")
    print(f"  Balanced:      {balanced['avg_gpa'].mean():.3f}")
    print()

    print("Average % A-range grades by course type:")
    print(f"  Exam-heavy:    {exam_heavy['pct_a_range'].mean():.1f}%")
    print(f"  Project-heavy: {project_heavy['pct_a_range'].mean():.1f}%")
    print(f"  Balanced:      {balanced['pct_a_range'].mean():.1f}%")
    print()

    print("Exam-heavy courses:")
    for _, row in exam_heavy.iterrows():
        print(f"  {row['course']:15s} GPA={row['avg_gpa']:.2f}  Exams={row['pct_exams']:.0f}%")

    print()
    print("Project-heavy courses:")
    for _, row in project_heavy.iterrows():
        print(f"  {row['course']:15s} GPA={row['avg_gpa']:.2f}  Projects={row['pct_projects']:.0f}%")

    print()

def analyze_grade_distributions(df):
    """Analyze grade distribution patterns"""
    print("=" * 80)
    print("GRADE DISTRIBUTION ANALYSIS")
    print("=" * 80)
    print()

    # Find courses with extreme distributions
    print("Most spread-out grade distributions (highest entropy):")
    top_entropy = df.nlargest(5, 'grade_entropy')[['course', 'avg_gpa', 'grade_entropy', 'pct_a_range']]
    for _, row in top_entropy.iterrows():
        print(f"  {row['course']:15s} GPA={row['avg_gpa']:.2f}  Entropy={row['grade_entropy']:.2f}  %A={row['pct_a_range']:.1f}%")

    print()
    print("Most concentrated grade distributions (lowest entropy):")
    bottom_entropy = df.nsmallest(5, 'grade_entropy')[['course', 'avg_gpa', 'grade_entropy', 'pct_a_range']]
    for _, row in bottom_entropy.iterrows():
        print(f"  {row['course']:15s} GPA={row['avg_gpa']:.2f}  Entropy={row['grade_entropy']:.2f}  %A={row['pct_a_range']:.1f}%")

    print()
    print("Most negatively skewed (hardest distributions):")
    most_neg_skew = df.nsmallest(5, 'grade_skewness')[['course', 'avg_gpa', 'grade_skewness', 'pct_a_range']]
    for _, row in most_neg_skew.iterrows():
        print(f"  {row['course']:15s} GPA={row['avg_gpa']:.2f}  Skew={row['grade_skewness']:.2f}  %A={row['pct_a_range']:.1f}%")

    print()
    print("Least negatively skewed (easier distributions):")
    least_neg_skew = df.nlargest(5, 'grade_skewness')[['course', 'avg_gpa', 'grade_skewness', 'pct_a_range']]
    for _, row in least_neg_skew.iterrows():
        print(f"  {row['course']:15s} GPA={row['avg_gpa']:.2f}  Skew={row['grade_skewness']:.2f}  %A={row['pct_a_range']:.1f}%")

    print()

def find_interesting_patterns(df):
    """Find interesting patterns and outliers"""
    print("=" * 80)
    print("INTERESTING PATTERNS & OUTLIERS")
    print("=" * 80)
    print()

    # High enrollment courses
    print("Highest enrollment courses (top 5):")
    top_enrollment = df.nlargest(5, 'total_students')[['course', 'avg_gpa', 'total_students', 'pct_a_range']]
    for _, row in top_enrollment.iterrows():
        print(f"  {row['course']:15s} {row['total_students']:6.0f} students  GPA={row['avg_gpa']:.2f}  %A={row['pct_a_range']:.1f}%")

    print()

    # Easiest vs hardest courses
    print("Easiest courses (highest GPA):")
    easiest = df.nlargest(5, 'avg_gpa')[['course', 'avg_gpa', 'pct_a_range', 'exam_heavy', 'project_heavy']]
    for _, row in easiest.iterrows():
        exam = "exam-heavy" if row['exam_heavy'] == 1 else ""
        proj = "project-heavy" if row['project_heavy'] == 1 else ""
        tags = f"{exam} {proj}".strip() or "balanced"
        print(f"  {row['course']:15s} GPA={row['avg_gpa']:.2f}  %A={row['pct_a_range']:.1f}%  ({tags})")

    print()
    print("Hardest courses (lowest GPA):")
    hardest = df.nsmallest(5, 'avg_gpa')[['course', 'avg_gpa', 'pct_a_range', 'exam_heavy', 'project_heavy']]
    for _, row in hardest.iterrows():
        exam = "exam-heavy" if row['exam_heavy'] == 1 else ""
        proj = "project-heavy" if row['project_heavy'] == 1 else ""
        tags = f"{exam} {proj}".strip() or "balanced"
        print(f"  {row['course']:15s} GPA={row['avg_gpa']:.2f}  %A={row['pct_a_range']:.1f}%  ({tags})")

    print()

    # Upper vs lower division
    print("Upper division vs Lower division:")
    upper = df[df['course_level'] == 'upper_div']
    lower = df[df['course_level'] == 'lower_div']

    if len(upper) > 0 and len(lower) > 0:
        print(f"  Lower division: {len(lower)} courses, avg GPA={lower['avg_gpa'].mean():.3f}")
        print(f"  Upper division: {len(upper)} courses, avg GPA={upper['avg_gpa'].mean():.3f}")

    print()

def export_summary(df, corr_df):
    """Export summary statistics to CSV"""
    summary_file = OUTPUT_DIR / "feature_summary.csv"

    # Create summary
    summary = df[['course', 'avg_gpa', 'total_students', 'grade_entropy',
                   'grade_skewness', 'pct_a_range', 'exam_heavy', 'project_heavy',
                   'course_level']].copy()

    summary.to_csv(summary_file, index=False)
    print(f"Summary exported to: {summary_file}")

    # Export correlations
    corr_file = OUTPUT_DIR / "feature_correlations.csv"
    corr_df.to_csv(corr_file, index=False)
    print(f"Correlations exported to: {corr_file}")

    print()

def main():
    print()
    print("=" * 80)
    print("FEATURE EXPLORATION & ANALYSIS")
    print("=" * 80)
    print()

    # Load data
    print("Loading features from database...")
    df = load_all_features()
    print(f"Loaded {len(df)} courses with features")
    print()

    # Run analyses
    corr_df = analyze_correlations(df)
    compare_course_types(df)
    analyze_grade_distributions(df)
    find_interesting_patterns(df)

    # Export
    export_summary(df, corr_df)

    print("=" * 80)
    print("EXPLORATION COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Review exported CSV files in data/analysis/")
    print("  2. Run custom SQL queries on data/courses.db")
    print("  3. Proceed to modeling when ready")
    print()

if __name__ == "__main__":
    main()
