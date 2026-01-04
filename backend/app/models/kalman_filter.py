"""
Kalman Filter for Sequential Grade Prediction

Uses a 1D Kalman filter to estimate student's "true ability" by sequentially
processing their performance in prior courses relative to course averages.

State:
    x = Student's ability offset (how much better/worse than average)

Observations:
    z = (student_grade - course_average) for each prior course

Process:
    - Initialize with prior estimate (overall GPA vs typical average)
    - Update sequentially with each prior course observation
    - Final estimate used to adjust target course prediction

PRIVACY: Only uses grade differentials, not raw grades. Data processed in-memory only.
"""
import numpy as np
from typing import List, Tuple, Dict


class StudentAbilityKalmanFilter:
    """
    1D Kalman filter for estimating student's ability relative to course averages.

    State: x = ability offset (student's typical performance vs average)
    Measurement: z = (grade_received - course_average)
    """

    def __init__(
        self,
        initial_estimate: float = 0.0,
        initial_uncertainty: float = 0.3,
        process_noise: float = 0.05,
        measurement_noise: float = 0.15
    ):
        """
        Initialize Kalman filter.

        Args:
            initial_estimate: Initial belief about student's ability offset
            initial_uncertainty: Initial uncertainty in estimate
            process_noise: How much ability can change between courses (low = stable)
            measurement_noise: Noise in grade measurements (professor variance, etc.)
        """
        self.x = initial_estimate  # State: ability offset
        self.P = initial_uncertainty ** 2  # State covariance (uncertainty)
        self.Q = process_noise ** 2  # Process noise covariance
        self.R = measurement_noise ** 2  # Measurement noise covariance

        # Track history for debugging/explainability
        self.history = []

    def predict(self):
        """
        Prediction step: Ability stays roughly the same between courses.
        (But uncertainty increases slightly due to process noise)
        """
        # State prediction: x = x (ability doesn't change)
        # Covariance prediction: P = P + Q (uncertainty increases)
        self.P = self.P + self.Q

    def update(self, measurement: float, measurement_weight: float = 1.0):
        """
        Update step: Incorporate new grade observation.

        Args:
            measurement: Observed (grade_received - course_average)
            measurement_weight: Weight for this measurement (0-1)
                              Lower weight = less trust in this observation
        """
        # Kalman gain: How much to trust new measurement vs current estimate
        # K = P / (P + R)
        K = self.P / (self.P + self.R / measurement_weight)

        # Update state: x = x + K * (z - x)
        # (Move estimate toward measurement, weighted by Kalman gain)
        innovation = measurement - self.x
        self.x = self.x + K * innovation

        # Update covariance: P = (1 - K) * P
        # (Uncertainty decreases after incorporating measurement)
        self.P = (1 - K) * self.P

        # Record for explainability
        self.history.append({
            'measurement': measurement,
            'kalman_gain': K,
            'innovation': innovation,
            'state_after': self.x,
            'uncertainty_after': np.sqrt(self.P)
        })

    def get_estimate(self) -> Tuple[float, float]:
        """
        Get current ability estimate and uncertainty.

        Returns:
            (ability_offset, std_dev)
        """
        return self.x, np.sqrt(self.P)

    def get_history(self) -> List[Dict]:
        """Get filter update history for explainability."""
        return self.history


def apply_kalman_filter_to_prior_courses(
    prior_courses: List[Dict],
    course_averages: Dict[str, float],
    overall_gpa: float = None
) -> Tuple[float, float, List[Dict]]:
    """
    Apply Kalman filter to sequence of prior course grades.

    Args:
        prior_courses: List of {'course_name': str, 'grade_received': float}
        course_averages: Dict mapping course names to average GPAs
        overall_gpa: Student's overall GPA (used for initialization)

    Returns:
        (ability_offset, uncertainty, filter_history)

        ability_offset: Estimated how much student performs above/below average
        uncertainty: Standard deviation of estimate
        filter_history: Step-by-step filter updates for explainability
    """
    # Initialize filter
    if overall_gpa is not None:
        # Use overall GPA vs typical average (3.3) as initial estimate
        initial_estimate = overall_gpa - 3.3
        initial_uncertainty = 0.25  # More confident with overall GPA
    else:
        initial_estimate = 0.0  # No prior info, assume average
        initial_uncertainty = 0.4  # Less confident without overall GPA

    kf = StudentAbilityKalmanFilter(
        initial_estimate=initial_estimate,
        initial_uncertainty=initial_uncertainty,
        process_noise=0.05,  # Ability is fairly stable
        measurement_noise=0.15  # Grade noise from professor variance, etc.
    )

    # Process each prior course sequentially
    valid_observations = 0
    for course in prior_courses:
        course_name = course['course_name']
        grade_received = course['grade_received']

        # Look up course average
        course_avg = course_averages.get(course_name)

        if course_avg is None:
            # Course not in database, skip
            continue

        # Predict step
        kf.predict()

        # Measurement: How much better/worse than course average
        measurement = grade_received - course_avg

        # Weight measurement based on how typical the course is
        # (Give less weight to outlier courses with very high/low averages)
        typicality = 1.0 - abs(course_avg - 3.3) / 1.0  # 0-1 scale
        measurement_weight = 0.5 + 0.5 * typicality  # 0.5-1.0 range

        # Update step
        kf.update(measurement, measurement_weight)
        valid_observations += 1

    # Get final estimate
    ability_offset, uncertainty = kf.get_estimate()

    # If no valid observations, increase uncertainty
    if valid_observations == 0:
        uncertainty = 0.4

    return ability_offset, uncertainty, kf.get_history()


def adjust_prediction_with_kalman_filter(
    base_gpa: float,
    base_std: float,
    ability_offset: float,
    ability_uncertainty: float,
    user_context: Dict
) -> Tuple[float, float]:
    """
    Adjust base prediction using Kalman filter estimate + other context.

    Args:
        base_gpa: Base course difficulty prediction
        base_std: Base prediction uncertainty
        ability_offset: Kalman filter ability estimate
        ability_uncertainty: Kalman filter uncertainty
        user_context: Other user context (workload, comfort, etc.)

    Returns:
        (adjusted_gpa, adjusted_std)
    """
    # Start with base prediction
    adjusted_gpa = base_gpa

    # Add Kalman filter ability offset (main adjustment)
    adjusted_gpa += ability_offset

    # Add smaller adjustments from other context factors
    # (These are less important than Kalman filter estimate)

    # Workload factor (minor adjustment)
    units = user_context.get('units_this_semester')
    hours = user_context.get('hours_per_week_available')
    if units is not None and hours is not None:
        # Heavy load + low hours = negative adjustment
        workload_ratio = units / max(hours, 1)
        if workload_ratio > 1.0:  # More than 1 unit per hour
            adjusted_gpa -= 0.05
        elif workload_ratio < 0.6:  # Less than 0.6 units per hour
            adjusted_gpa += 0.05

    # Comfort level factor (minor adjustment)
    comfort = user_context.get('comfort_level')
    if comfort is not None:
        # Scale 1-5 to -0.05 to +0.05
        comfort_adjustment = (comfort - 3) * 0.025
        adjusted_gpa += comfort_adjustment

    # Clip to valid GPA range
    adjusted_gpa = np.clip(adjusted_gpa, 0.0, 4.0)

    # Combine uncertainties
    # Use variance addition (independent uncertainties)
    combined_variance = base_std**2 + ability_uncertainty**2
    adjusted_std = np.sqrt(combined_variance)

    # Ensure minimum uncertainty
    adjusted_std = max(adjusted_std, 0.12)

    return adjusted_gpa, adjusted_std
