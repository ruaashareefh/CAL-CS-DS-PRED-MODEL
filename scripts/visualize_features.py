"""
Feature Visualization for Course Outcome Prediction
Generate plots to understand relationships between features and outcomes
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

DB_PATH = Path("data/courses.db")
PLOTS_DIR = Path("plots")
PLOTS_DIR.mkdir(exist_ok=True)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10

def load_data():
    """Load all features from database"""
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        c.course_id,
        c.subject || ' ' || c.number as course,
        c.subject,
        c.avg_gpa,
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
        gs.pct_homework
    FROM courses c
    LEFT JOIN course_features cf ON c.course_id = cf.course_id
    LEFT JOIN grading_structure gs ON c.course_id = gs.course_id
    ORDER BY c.total_students DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df

def plot_gpa_vs_entropy(df):
    """Scatter plot: GPA vs Grade Entropy"""
    plt.figure(figsize=(10, 6))

    # Color by subject
    for subject in df['subject'].unique():
        subset = df[df['subject'] == subject]
        plt.scatter(subset['grade_entropy'], subset['avg_gpa'],
                   label=subject, alpha=0.7, s=100)

    plt.xlabel('Grade Entropy (higher = more spread out)', fontsize=12)
    plt.ylabel('Average GPA', fontsize=12)
    plt.title('Course Difficulty: GPA vs Grade Distribution Entropy', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Add trend line
    mask = df['grade_entropy'].notna() & df['avg_gpa'].notna()
    if mask.sum() > 1:
        z = np.polyfit(df[mask]['grade_entropy'], df[mask]['avg_gpa'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(df[mask]['grade_entropy'].min(),
                            df[mask]['grade_entropy'].max(), 100)
        plt.plot(x_line, p(x_line), "r--", alpha=0.5, label='Trend')

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / 'gpa_vs_entropy.png', dpi=300, bbox_inches='tight')
    print(f"  Saved: plots/gpa_vs_entropy.png")
    plt.close()

def plot_gpa_vs_a_range(df):
    """Scatter plot: GPA vs % A-range grades"""
    plt.figure(figsize=(10, 6))

    # Color by course level
    colors = {'lower_div': 'blue', 'upper_div': 'green'}
    for level, color in colors.items():
        subset = df[df['course_level'] == level]
        plt.scatter(subset['pct_a_range'], subset['avg_gpa'],
                   label=level.replace('_', ' ').title(),
                   color=color, alpha=0.7, s=100)

    plt.xlabel('% Students Receiving A-range Grades', fontsize=12)
    plt.ylabel('Average GPA', fontsize=12)
    plt.title('% A-range Grades vs Average GPA', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Add trend line
    mask = df['pct_a_range'].notna() & df['avg_gpa'].notna()
    if mask.sum() > 1:
        z = np.polyfit(df[mask]['pct_a_range'], df[mask]['avg_gpa'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(df[mask]['pct_a_range'].min(),
                            df[mask]['pct_a_range'].max(), 100)
        plt.plot(x_line, p(x_line), "r--", alpha=0.5, label='Trend')

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / 'gpa_vs_a_range.png', dpi=300, bbox_inches='tight')
    print(f"  Saved: plots/gpa_vs_a_range.png")
    plt.close()

def plot_gpa_distribution(df):
    """Histogram: Distribution of GPAs"""
    plt.figure(figsize=(10, 6))

    plt.hist(df['avg_gpa'], bins=15, edgecolor='black', alpha=0.7, color='steelblue')
    plt.xlabel('Average GPA', fontsize=12)
    plt.ylabel('Number of Courses', fontsize=12)
    plt.title('Distribution of Course GPAs', fontsize=14, fontweight='bold')
    plt.axvline(df['avg_gpa'].mean(), color='red', linestyle='--',
                linewidth=2, label=f'Mean: {df["avg_gpa"].mean():.2f}')
    plt.axvline(df['avg_gpa'].median(), color='green', linestyle='--',
                linewidth=2, label=f'Median: {df["avg_gpa"].median():.2f}')
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / 'gpa_distribution.png', dpi=300, bbox_inches='tight')
    print(f"  Saved: plots/gpa_distribution.png")
    plt.close()

def plot_exam_vs_project_gpa(df):
    """Box plot: GPA by course type"""
    df_grading = df[df['pct_exams'].notna()].copy()

    if len(df_grading) == 0:
        print("  Skipped: Not enough grading data")
        return

    # Categorize courses
    def categorize(row):
        if row['exam_heavy']:
            return 'Exam-Heavy\n(>60% exams)'
        elif row['project_heavy']:
            return 'Project-Heavy\n(>25% projects)'
        else:
            return 'Balanced'

    df_grading['course_type'] = df_grading.apply(categorize, axis=1)

    plt.figure(figsize=(10, 6))

    # Create box plot
    course_types = ['Exam-Heavy\n(>60% exams)', 'Project-Heavy\n(>25% projects)', 'Balanced']
    data_to_plot = [df_grading[df_grading['course_type'] == ct]['avg_gpa'].values
                    for ct in course_types if ct in df_grading['course_type'].values]
    labels_to_plot = [ct for ct in course_types if ct in df_grading['course_type'].values]

    bp = plt.boxplot(data_to_plot, labels=labels_to_plot, patch_artist=True)

    # Color boxes
    colors = ['#ff9999', '#66b3ff', '#99ff99']
    for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
        patch.set_facecolor(color)

    plt.ylabel('Average GPA', fontsize=12)
    plt.title('Course GPA by Grading Structure Type', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / 'gpa_by_course_type.png', dpi=300, bbox_inches='tight')
    print(f"  Saved: plots/gpa_by_course_type.png")
    plt.close()

def plot_enrollment_vs_gpa(df):
    """Scatter plot: Enrollment vs GPA"""
    plt.figure(figsize=(10, 6))

    # Use log scale for enrollment
    plt.scatter(df['total_students'], df['avg_gpa'], alpha=0.6, s=100, color='purple')

    plt.xlabel('Total Students (log scale)', fontsize=12)
    plt.ylabel('Average GPA', fontsize=12)
    plt.title('Course Enrollment vs Average GPA', fontsize=14, fontweight='bold')
    plt.xscale('log')
    plt.grid(True, alpha=0.3)

    # Annotate highest enrollment courses
    top_5 = df.nlargest(5, 'total_students')
    for _, row in top_5.iterrows():
        plt.annotate(row['course'], (row['total_students'], row['avg_gpa']),
                    fontsize=8, alpha=0.7,
                    xytext=(5, 5), textcoords='offset points')

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / 'enrollment_vs_gpa.png', dpi=300, bbox_inches='tight')
    print(f"  Saved: plots/enrollment_vs_gpa.png")
    plt.close()

def plot_grading_structure_heatmap(df):
    """Heatmap: Grading structure for courses with data"""
    df_grading = df[df['pct_exams'].notna()].copy()

    if len(df_grading) < 3:
        print("  Skipped: Not enough grading data")
        return

    # Prepare data
    grading_data = df_grading[['course', 'pct_exams', 'pct_projects', 'pct_homework']].set_index('course')

    plt.figure(figsize=(10, 8))

    sns.heatmap(grading_data.T, annot=True, fmt='.1f', cmap='YlOrRd',
                cbar_kws={'label': 'Percentage of Grade'})

    plt.title('Grading Structure Breakdown by Course', fontsize=14, fontweight='bold')
    plt.xlabel('Course', fontsize=12)
    plt.ylabel('Assessment Type', fontsize=12)

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / 'grading_structure_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"  Saved: plots/grading_structure_heatmap.png")
    plt.close()

def plot_correlation_matrix(df):
    """Correlation heatmap for numeric features"""
    # Select numeric features
    numeric_features = ['avg_gpa', 'grade_entropy', 'grade_skewness',
                       'pct_a_range', 'total_students', 'pct_exams',
                       'pct_projects', 'pct_homework', 'total_assessments']

    corr_data = df[numeric_features].corr()

    plt.figure(figsize=(12, 10))

    mask = np.triu(np.ones_like(corr_data, dtype=bool))
    sns.heatmap(corr_data, mask=mask, annot=True, fmt='.2f',
                cmap='coolwarm', center=0, square=True,
                linewidths=1, cbar_kws={"shrink": 0.8})

    plt.title('Feature Correlation Matrix', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / 'correlation_matrix.png', dpi=300, bbox_inches='tight')
    print(f"  Saved: plots/correlation_matrix.png")
    plt.close()

def plot_skewness_distribution(df):
    """Histogram: Distribution of grade skewness"""
    plt.figure(figsize=(10, 6))

    plt.hist(df['grade_skewness'].dropna(), bins=15, edgecolor='black',
             alpha=0.7, color='coral')

    plt.xlabel('Grade Skewness (more negative = harder)', fontsize=12)
    plt.ylabel('Number of Courses', fontsize=12)
    plt.title('Distribution of Grade Skewness', fontsize=14, fontweight='bold')
    plt.axvline(df['grade_skewness'].mean(), color='red', linestyle='--',
                linewidth=2, label=f'Mean: {df["grade_skewness"].mean():.2f}')
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / 'skewness_distribution.png', dpi=300, bbox_inches='tight')
    print(f"  Saved: plots/skewness_distribution.png")
    plt.close()

def main():
    print()
    print("=" * 80)
    print("FEATURE VISUALIZATION")
    print("=" * 80)
    print()

    print("Loading data...")
    df = load_data()
    print(f"Loaded {len(df)} courses\n")

    print("Generating plots...")

    plot_gpa_distribution(df)
    plot_gpa_vs_entropy(df)
    plot_gpa_vs_a_range(df)
    plot_enrollment_vs_gpa(df)
    plot_skewness_distribution(df)
    plot_exam_vs_project_gpa(df)
    plot_grading_structure_heatmap(df)
    plot_correlation_matrix(df)

    print()
    print("=" * 80)
    print(f"All plots saved to: {PLOTS_DIR}/")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
