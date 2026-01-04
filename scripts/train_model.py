"""
Course Outcome Prediction Model Training
Build and evaluate models to predict course difficulty and grade distributions
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import cross_val_score, LeaveOneOut
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

DB_PATH = Path("data/courses.db")
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

def load_training_data():
    """Load features for model training"""
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        c.course_id,
        c.subject || ' ' || c.number as course,
        c.avg_gpa as target,
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

        -- Course level (encode as binary)
        CASE WHEN cf.course_level = 'upper_div' THEN 1 ELSE 0 END as is_upper_div,

        -- Grading percentages
        gs.pct_exams,
        gs.pct_projects,
        gs.pct_homework

    FROM courses c
    JOIN course_features cf ON c.course_id = cf.course_id
    LEFT JOIN grading_structure gs ON c.course_id = gs.course_id
    WHERE c.avg_gpa IS NOT NULL
    ORDER BY c.total_students DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df

def evaluate_model(model, X, y, model_name):
    """Evaluate model using Leave-One-Out Cross-Validation"""
    print(f"\n{model_name}:")
    print("-" * 60)

    # Leave-One-Out CV (good for small datasets)
    loo = LeaveOneOut()

    predictions = []
    actuals = []

    for train_idx, test_idx in loo.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model.fit(X_train, y_train)
        pred = model.predict(X_test)

        predictions.append(pred[0])
        actuals.append(y_test.values[0])

    predictions = np.array(predictions)
    actuals = np.array(actuals)

    # Calculate metrics
    mae = mean_absolute_error(actuals, predictions)
    rmse = np.sqrt(mean_squared_error(actuals, predictions))
    r2 = r2_score(actuals, predictions)

    print(f"  Mean Absolute Error (MAE): {mae:.3f}")
    print(f"  Root Mean Squared Error (RMSE): {rmse:.3f}")
    print(f"  R² Score: {r2:.3f}")

    # Show some predictions
    print(f"\n  Sample predictions:")
    for i in range(min(5, len(predictions))):
        error = predictions[i] - actuals[i]
        print(f"    Actual: {actuals[i]:.2f}  Predicted: {predictions[i]:.2f}  Error: {error:+.2f}")

    return {
        'model_name': model_name,
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'predictions': predictions,
        'actuals': actuals
    }

def train_baseline_model(df):
    """Baseline: Predict mean GPA"""
    print("\n" + "=" * 80)
    print("BASELINE MODEL: Mean GPA")
    print("=" * 80)

    mean_gpa = df['target'].mean()
    predictions = np.full(len(df), mean_gpa)
    actuals = df['target'].values

    mae = mean_absolute_error(actuals, predictions)
    rmse = np.sqrt(mean_squared_error(actuals, predictions))
    r2 = r2_score(actuals, predictions)

    print(f"\n  Mean GPA: {mean_gpa:.3f}")
    print(f"  Mean Absolute Error (MAE): {mae:.3f}")
    print(f"  Root Mean Squared Error (RMSE): {rmse:.3f}")
    print(f"  R² Score: {r2:.3f}")

    return {
        'model_name': 'Baseline (Mean)',
        'mae': mae,
        'rmse': rmse,
        'r2': r2
    }

def train_grade_distribution_model(df):
    """Model 1: Using only grade distribution features"""
    print("\n" + "=" * 80)
    print("MODEL 1: Grade Distribution Features Only")
    print("=" * 80)

    features = ['grade_entropy', 'grade_skewness', 'pct_a_range', 'pct_passing']

    X = df[features].copy()
    y = df['target']

    # Handle missing values
    X = X.fillna(X.mean())

    # Train model
    model = Ridge(alpha=1.0)
    results = evaluate_model(model, X, y, "Ridge Regression (Grade Distribution)")

    # Train final model on all data for deployment
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model.fit(X_scaled, y)

    # Save model
    joblib.dump({'model': model, 'scaler': scaler, 'features': features},
                MODELS_DIR / 'model_grade_distribution.pkl')

    print(f"\n  Model saved to: {MODELS_DIR}/model_grade_distribution.pkl")

    return results

def train_full_model(df):
    """Model 2: Using all available features"""
    print("\n" + "=" * 80)
    print("MODEL 2: All Features (Grade Distribution + Grading Structure)")
    print("=" * 80)

    # Select features (only use courses with grading structure data)
    df_full = df[df['pct_exams'].notna()].copy()

    print(f"\n  Training on {len(df_full)} courses with complete grading structure data")

    if len(df_full) < 5:
        print("  Not enough data for full model (need grading structures)")
        return None

    features = [
        'grade_entropy', 'grade_skewness', 'pct_a_range',
        'exam_heavy', 'project_heavy', 'has_projects',
        'pct_exams', 'pct_projects', 'pct_homework',
        'total_assessments', 'is_upper_div'
    ]

    X = df_full[features].copy()
    y = df_full['target']

    # Handle missing values
    X = X.fillna(X.mean())

    # Train model
    model = RandomForestRegressor(n_estimators=100, max_depth=3,
                                  random_state=42, min_samples_split=2)
    results = evaluate_model(model, X, y, "Random Forest (All Features)")

    # Feature importance
    model.fit(X, y)
    importances = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"\n  Feature Importances:")
    for _, row in importances.head(5).iterrows():
        print(f"    {row['feature']:20s} {row['importance']:.3f}")

    # Save model
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model.fit(X_scaled, y)

    joblib.dump({'model': model, 'scaler': scaler, 'features': features},
                MODELS_DIR / 'model_full.pkl')

    print(f"\n  Model saved to: {MODELS_DIR}/model_full.pkl")

    return results

def compare_models(results_list):
    """Compare all models"""
    print("\n" + "=" * 80)
    print("MODEL COMPARISON SUMMARY")
    print("=" * 80)
    print()

    results_df = pd.DataFrame(results_list)
    results_df = results_df.sort_values('mae')

    print(f"{'Model':<40s} {'MAE':>8s} {'RMSE':>8s} {'R²':>8s}")
    print("-" * 70)

    for _, row in results_df.iterrows():
        print(f"{row['model_name']:<40s} {row['mae']:>8.3f} {row['rmse']:>8.3f} {row['r2']:>8.3f}")

    print()
    print("Best model (lowest MAE):", results_df.iloc[0]['model_name'])
    print()

    # Save comparison
    results_df.to_csv(MODELS_DIR / 'model_comparison.csv', index=False)
    print(f"Comparison saved to: {MODELS_DIR}/model_comparison.csv")

def main():
    print()
    print("=" * 80)
    print("COURSE OUTCOME PREDICTION: MODEL TRAINING")
    print("=" * 80)

    # Load data
    print("\nLoading training data...")
    df = load_training_data()
    print(f"Loaded {len(df)} courses")
    print(f"  - Courses with grading structure: {df['pct_exams'].notna().sum()}")

    # Train models
    results = []

    # Baseline
    baseline_results = train_baseline_model(df)
    results.append(baseline_results)

    # Model 1: Grade distribution only
    model1_results = train_grade_distribution_model(df)
    results.append(model1_results)

    # Model 2: Full features
    model2_results = train_full_model(df)
    if model2_results:
        results.append(model2_results)

    # Compare
    compare_models(results)

    print("\n" + "=" * 80)
    print("TRAINING COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Review model comparison in models/model_comparison.csv")
    print("  2. Use trained models to make predictions")
    print("  3. Build UI for course predictions")
    print()

if __name__ == "__main__":
    main()
