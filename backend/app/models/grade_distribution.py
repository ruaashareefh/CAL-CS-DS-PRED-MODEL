"""
Grade distribution utilities for personalized predictions.
Converts GPA mean/std to letter grade probabilities.
"""
import numpy as np
from scipy import stats
from typing import Dict


# Grade boundaries (GPA ranges)
GRADE_BOUNDS = {
    'A': (3.85, 4.0),
    'A-': (3.7, 3.85),
    'B+': (3.3, 3.7),
    'B': (3.0, 3.3),
    'B-': (2.7, 3.0),
    'C+': (2.3, 2.7),
    'C': (2.0, 2.3),
    'C-': (1.7, 2.0),
    'D': (1.0, 1.7),
    'F': (0.0, 1.0)
}


def gpa_to_grade_distribution(mean_gpa: float, std_gpa: float) -> Dict[str, float]:
    """
    Convert GPA mean/std to grade probability distribution.

    Assumes GPA ~ Normal(mean, std) clipped to [0, 4].
    Maps GPA intervals to letter grades using normal CDF.

    Args:
        mean_gpa: Predicted mean GPA
        std_gpa: Standard deviation of GPA prediction

    Returns:
        dict: Grade probabilities (e.g., {'A': 0.15, 'A-': 0.20, ...})
              Probabilities sum to 1.0

    Example:
        >>> dist = gpa_to_grade_distribution(3.5, 0.3)
        >>> dist['A']  # probability of getting an A
        0.095
    """
    # Ensure minimum uncertainty to avoid overconfidence
    std_gpa = max(std_gpa, 0.15)

    # Clip mean to valid range
    mean_gpa = np.clip(mean_gpa, 0.0, 4.0)

    # Create normal distribution
    dist = stats.norm(loc=mean_gpa, scale=std_gpa)

    # Calculate probability mass for each grade interval
    grade_probs = {}

    for grade, (lower, upper) in GRADE_BOUNDS.items():
        # P(lower <= GPA < upper)
        prob_lower = dist.cdf(lower)
        prob_upper = dist.cdf(upper)
        grade_probs[grade] = prob_upper - prob_lower

    # Normalize to ensure probabilities sum to 1.0
    # (due to clipping and numerical precision, may not be exactly 1.0)
    total_prob = sum(grade_probs.values())
    if total_prob > 0:
        grade_probs = {k: v / total_prob for k, v in grade_probs.items()}

    return grade_probs


def estimate_personalized_uncertainty(
    base_std: float,
    user_context_quality: float = 0.5
) -> float:
    """
    Estimate uncertainty for personalized predictions.

    Args:
        base_std: Base model uncertainty (from training residuals)
        user_context_quality: Quality of user context (0-1)
                            Lower = less complete data = more uncertainty

    Returns:
        float: Adjusted standard deviation
    """
    # With no user context (quality=0), use conservative high uncertainty
    # With complete context (quality=1), use base model uncertainty
    # Conservative: start with higher uncertainty
    max_std = max(base_std * 1.5, 0.25)  # At least 0.25 GPA points uncertainty
    min_std = max(base_std, 0.15)  # At least 0.15 even with full context

    # Linear interpolation between max and min based on context quality
    adjusted_std = max_std - (max_std - min_std) * user_context_quality

    return adjusted_std


def compute_user_context_features(user_context: Dict) -> Dict[str, float]:
    """
    Extract coarse-grained features from user context.

    PRIVACY: Only uses aggregates and coarse bins, no raw personal data.

    Args:
        user_context: UserContext dict with optional fields

    Returns:
        dict: Engineered features for model input
    """
    features = {}

    # GPA adjustment (coarse bins)
    avg_gpa = user_context.get('avg_gpa')
    if avg_gpa is not None:
        # Bin GPA into quartiles
        if avg_gpa >= 3.5:
            features['gpa_quartile'] = 4  # High GPA
        elif avg_gpa >= 3.0:
            features['gpa_quartile'] = 3  # Good GPA
        elif avg_gpa >= 2.5:
            features['gpa_quartile'] = 2  # Average GPA
        else:
            features['gpa_quartile'] = 1  # Lower GPA
    else:
        features['gpa_quartile'] = 2.5  # Default to middle

    # Workload indicator (coarse)
    units = user_context.get('units_this_semester')
    if units is not None:
        if units >= 18:
            features['workload'] = 1.0  # Heavy
        elif units >= 13:
            features['workload'] = 0.5  # Normal
        else:
            features['workload'] = 0.0  # Light
    else:
        features['workload'] = 0.5  # Default to normal

    # Time availability (coarse)
    hours = user_context.get('hours_per_week_available')
    if hours is not None:
        # More hours available = positive indicator
        features['time_available'] = min(hours / 40.0, 1.0)  # Normalize to [0, 1]
    else:
        features['time_available'] = 0.5  # Default

    # Comfort level (self-reported, coarse)
    comfort = user_context.get('comfort_level')
    if comfort is not None:
        features['comfort'] = (comfort - 1) / 4.0  # Normalize 1-5 to [0, 1]
    else:
        features['comfort'] = 0.5  # Default to middle

    # Prior courses indicator (coarse count)
    prior = user_context.get('prior_courses', [])
    # Handle None case explicitly
    if prior is None:
        prior = []

    if prior:
        # Just count, don't analyze specific courses (privacy)
        features['prior_courses_count'] = min(len(prior) / 10.0, 1.0)  # Normalize
    else:
        features['prior_courses_count'] = 0.0

    # Context completeness (for uncertainty adjustment)
    provided_fields = sum([
        avg_gpa is not None,
        units is not None,
        hours is not None,
        comfort is not None,
        prior is not None and len(prior) > 0
    ])
    features['context_quality'] = provided_fields / 5.0  # 0-1 scale

    return features


def adjust_prediction_with_context(
    base_gpa: float,
    base_std: float,
    user_context: Dict
) -> tuple[float, float]:
    """
    Adjust base GPA prediction using user context.

    This is a SIMPLE heuristic adjustment, not a trained model.
    Uses conservative adjustments to avoid overconfidence.

    Args:
        base_gpa: Base GPA prediction from course model
        base_std: Base uncertainty
        user_context: User context dict

    Returns:
        tuple: (adjusted_mean_gpa, adjusted_std_gpa)
    """
    context_features = compute_user_context_features(user_context)

    # Composite adjustment factor (-0.3 to +0.3 GPA points)
    # Based on user's academic standing and workload
    gpa_factor = (context_features['gpa_quartile'] - 2.5) / 10.0  # -0.15 to +0.15
    workload_factor = -context_features['workload'] * 0.1  # 0 to -0.1
    time_factor = (context_features['time_available'] - 0.5) * 0.1  # -0.05 to +0.05
    comfort_factor = (context_features['comfort'] - 0.5) * 0.1  # -0.05 to +0.05

    total_adjustment = gpa_factor + workload_factor + time_factor + comfort_factor

    # Conservative: limit adjustment range
    total_adjustment = np.clip(total_adjustment, -0.3, 0.3)

    # Apply adjustment
    adjusted_mean = np.clip(base_gpa + total_adjustment, 0.0, 4.0)

    # Adjust uncertainty based on context completeness
    context_quality = context_features['context_quality']
    adjusted_std = estimate_personalized_uncertainty(base_std, context_quality)

    return adjusted_mean, adjusted_std
