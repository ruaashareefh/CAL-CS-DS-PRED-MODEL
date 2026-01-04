"""
Prediction endpoints for GPA predictions
"""
from fastapi import APIRouter, HTTPException
from typing import List, Union
from ..models.schemas import (
    PredictRequest,
    PredictResponse,
    BatchPredictRequest,
    BatchPredictResponse,
    ModelsResponse,
    PredictionResult,
    ModelInfo,
    CourseInfo,
    ConfidenceInterval,
    PersonalizedPredictResponse,
    PersonalizedPredictionResult,
    GradeDistributionProbs,
    PrivacyInfo
)
from ..models.ml_models import model_cache
from ..models.grade_distribution import (
    gpa_to_grade_distribution
)
from ..models.kalman_filter import (
    apply_kalman_filter_to_prior_courses,
    adjust_prediction_with_kalman_filter
)
from ..database.connection import get_db
from ..database.queries import get_course_features, get_course_by_id, get_course_averages

router = APIRouter()


@router.post("/predict")
async def predict_gpa(request: PredictRequest) -> Union[PredictResponse, PersonalizedPredictResponse]:
    """
    Predict GPA for a specific course

    Supports three modes:
    - 'grade_distribution': Course-level prediction using grade features
    - 'full': Course-level prediction using all features
    - 'personalized': Individual-level prediction with user context

    PRIVACY for personalized mode:
    - User inputs are processed in-memory only
    - No personal data is stored or logged
    - Returns probability distribution, not deterministic outcome

    Args:
        request: PredictRequest with course_id, model_type, and optional user_context

    Returns:
        PredictResponse or PersonalizedPredictResponse depending on model_type

    Raises:
        HTTPException: 400 if course not found, 422 if validation fails
    """
    # Handle personalized predictions separately
    if request.model_type == 'personalized':
        return await predict_personalized(request)
    try:
        with get_db() as conn:
            # Get course features for prediction
            try:
                features = get_course_features(conn, request.course_id)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

            # Get course metadata
            course_data = get_course_by_id(conn, request.course_id)
            if not course_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Course ID {request.course_id} not found"
                )

            # Check if model can be used with this course
            if request.model_type == 'full' and features.get('pct_exams') is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Course {course_data['full_name']} does not have grading structure data. "
                        "Please use model_type='grade_distribution' instead."
                    )
                )

            # Make prediction
            try:
                predicted_gpa, metadata = model_cache.predict(
                    model_type=request.model_type,
                    features=features
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

            # Calculate error if actual GPA is available
            actual_gpa = course_data.get('avg_gpa')
            error = predicted_gpa - actual_gpa if actual_gpa is not None else None

            # Build response
            model_info_dict = metadata['model_info']
            model_info = ModelInfo(
                model_type=model_info_dict['model_type'],
                model_name=model_info_dict['model_name'],
                description=model_info_dict.get('description'),
                mae=model_info_dict.get('mae'),
                rmse=model_info_dict.get('rmse'),
                r2=model_info_dict.get('r2'),
                features_used=model_info_dict['features'],
                num_features=model_info_dict['num_features']
            )

            # Extract input features that were actually used
            input_features = {
                feature: features[feature]
                for feature in model_info_dict['features']
                if feature in features
            }

            response = PredictResponse(
                prediction=PredictionResult(
                    predicted_gpa=predicted_gpa,
                    actual_gpa=actual_gpa,
                    error=error,
                    confidence_interval=ConfidenceInterval(
                        lower=metadata['confidence_interval']['lower'],
                        upper=metadata['confidence_interval']['upper']
                    )
                ),
                model_info=model_info,
                input_features=input_features,
                course=CourseInfo(
                    course_id=course_data['course_id'],
                    subject=course_data['subject'],
                    number=course_data['number'],
                    full_name=course_data['full_name']
                )
            )

            return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


async def predict_personalized(request: PredictRequest) -> PersonalizedPredictResponse:
    """
    PRIVACY-PRESERVING personalized prediction.

    Returns grade distribution based on user context.
    NO personal data is stored or logged.

    Args:
        request: PredictRequest with user_context

    Returns:
        PersonalizedPredictResponse with grade distribution and privacy info
    """
    try:
        with get_db() as conn:
            # Get course data (aggregated, not personal)
            course_data = get_course_by_id(conn, request.course_id)
            if not course_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Course ID {request.course_id} not found"
                )

            # Get course features for base prediction
            features = get_course_features(conn, request.course_id)

            # Make base prediction using grade_distribution model
            base_gpa, metadata = model_cache.predict(
                model_type='grade_distribution',
                features=features
            )

            # Get base uncertainty from model
            base_std = metadata['model_info'].get('mae', 0.1) * 1.5  # Conservative estimate

            # Prepare user context
            user_context_dict = request.user_context.model_dump() if request.user_context else {}

            # Apply Kalman filter if prior courses with grades provided
            ability_offset = 0.0
            ability_uncertainty = 0.4
            kalman_history = []

            if request.user_context and request.user_context.prior_courses:
                # Extract course names for lookup
                prior_courses_list = [
                    {
                        'course_name': pc.course_name,
                        'grade_received': pc.grade_received
                    }
                    for pc in request.user_context.prior_courses
                ]
                course_names = [pc['course_name'] for pc in prior_courses_list]

                # Look up course averages
                course_averages = get_course_averages(conn, course_names)

                # Apply Kalman filter
                ability_offset, ability_uncertainty, kalman_history = apply_kalman_filter_to_prior_courses(
                    prior_courses=prior_courses_list,
                    course_averages=course_averages,
                    overall_gpa=user_context_dict.get('avg_gpa')
                )

            # Adjust prediction using Kalman filter + other context
            adjusted_mean, adjusted_std = adjust_prediction_with_kalman_filter(
                base_gpa=base_gpa,
                base_std=base_std,
                ability_offset=ability_offset,
                ability_uncertainty=ability_uncertainty,
                user_context=user_context_dict
            )

            # Convert to grade distribution
            grade_probs = gpa_to_grade_distribution(adjusted_mean, adjusted_std)

            # Build response
            response = PersonalizedPredictResponse(
                prediction=PersonalizedPredictionResult(
                    course_id=request.course_id,
                    predicted_gpa_mean=adjusted_mean,
                    predicted_gpa_std=adjusted_std,
                    grade_distribution=GradeDistributionProbs(
                        A=grade_probs['A'],
                        **{'A-': grade_probs['A-']},
                        **{'B+': grade_probs['B+']},
                        B=grade_probs['B'],
                        **{'B-': grade_probs['B-']},
                        **{'C+': grade_probs['C+']},
                        C=grade_probs['C'],
                        **{'C-': grade_probs['C-']},
                        D=grade_probs['D'],
                        F=grade_probs['F']
                    )
                ),
                privacy=PrivacyInfo(),
                course=CourseInfo(
                    course_id=course_data['course_id'],
                    subject=course_data['subject'],
                    number=course_data['number'],
                    full_name=course_data['full_name']
                )
            )

            return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Personalized prediction error: {str(e)}")


@router.post("/predict/batch", response_model=BatchPredictResponse)
async def batch_predict_gpa(request: BatchPredictRequest):
    """
    Predict GPA for multiple courses in a single request

    Args:
        request: BatchPredictRequest with list of course_ids and model_type

    Returns:
        BatchPredictResponse: List of predictions with summary statistics

    Raises:
        HTTPException: 400 if any course not found
    """
    predictions: List[PredictResponse] = []

    # Make prediction for each course
    for course_id in request.course_ids:
        try:
            pred_request = PredictRequest(
                course_id=course_id,
                model_type=request.model_type
            )
            prediction = await predict_gpa(pred_request)
            predictions.append(prediction)
        except HTTPException as e:
            # Skip courses that can't be predicted
            if e.status_code == 400:
                continue
            raise

    if not predictions:
        raise HTTPException(
            status_code=400,
            detail="No valid predictions could be made for the given courses"
        )

    # Calculate summary statistics
    predicted_gpas = [p.prediction.predicted_gpa for p in predictions]
    actual_gpas = [p.prediction.actual_gpa for p in predictions if p.prediction.actual_gpa is not None]

    summary = {
        'total_courses': len(predictions),
        'mean_predicted_gpa': sum(predicted_gpas) / len(predicted_gpas),
        'min_predicted_gpa': min(predicted_gpas),
        'max_predicted_gpa': max(predicted_gpas)
    }

    if actual_gpas:
        summary['mean_actual_gpa'] = sum(actual_gpas) / len(actual_gpas)

    return BatchPredictResponse(
        predictions=predictions,
        summary=summary
    )


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """
    Get information about all available ML models

    Returns model metadata including:
    - Model type and name
    - Features used
    - Performance metrics (MAE, RMSE, R²)
    - Description

    Returns:
        ModelsResponse: List of model information
    """
    try:
        models_info = model_cache.get_all_models_info()

        # Convert to ModelInfo schema
        models = [
            ModelInfo(
                model_type=info['model_type'],
                model_name=info['model_name'],
                description=info.get('description'),
                mae=info.get('mae'),
                rmse=info.get('rmse'),
                r2=info.get('r2'),
                features_used=info['features'],
                num_features=info['num_features']
            )
            for info in models_info
        ]

        return ModelsResponse(models=models)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving models: {str(e)}")
