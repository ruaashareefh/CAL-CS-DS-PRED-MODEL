"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict


# ============================================================================
# Request Schemas
# ============================================================================

class PriorCourse(BaseModel):
    """
    Prior course with student's grade for performance comparison.
    """
    course_name: str = Field(
        ...,
        description="Course name (e.g., 'COMPSCI 61A', 'DATA C8')"
    )
    grade_received: str = Field(
        ...,
        description="Letter grade received (A+, A, A-, B+, B, B-, C+, C, C-, D, F)"
    )

    @field_validator('grade_received')
    @classmethod
    def validate_grade(cls, v):
        """Validate letter grade"""
        valid_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
        if v not in valid_grades:
            raise ValueError(f'grade_received must be one of {valid_grades}')
        return v


class UserContext(BaseModel):
    """
    User academic context for personalized predictions.
    PRIVACY: These fields are NON-SENSITIVE and coarse-grained.
    NO demographics, disability status, or protected attributes.
    """
    prior_courses: Optional[List[PriorCourse]] = Field(
        None,
        description="List of prior courses with grades for Kalman filter analysis"
    )
    avg_gpa: Optional[float] = Field(
        None,
        ge=0.0,
        le=4.0,
        description="Current overall GPA (optional, clamped to [0.0, 4.0])"
    )
    units_this_semester: Optional[int] = Field(
        None,
        ge=0,
        le=35,
        description="Total units enrolled this semester (optional, clamped to [0, 35])"
    )
    hours_per_week_available: Optional[int] = Field(
        None,
        ge=0,
        le=80,
        description="Hours per week available for study (optional, clamped to [0, 80])"
    )
    comfort_level: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Self-reported comfort level with course material (1=low, 5=high)"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Free-form notes about circumstances, challenges, or context (processed by LLM)"
    )


class PredictRequest(BaseModel):
    """Request schema for GPA prediction"""
    course_id: int = Field(..., ge=1, description="Course ID from database")
    model_type: str = Field(
        "grade_distribution",
        description="Model type: 'grade_distribution', 'full', or 'personalized'"
    )
    user_context: Optional[UserContext] = Field(
        None,
        description="Optional user academic context for personalized predictions"
    )

    @field_validator('model_type')
    @classmethod
    def validate_model_type(cls, v):
        if v not in ['grade_distribution', 'full', 'personalized']:
            raise ValueError('model_type must be "grade_distribution", "full", or "personalized"')
        return v

    @field_validator('user_context')
    @classmethod
    def validate_user_context_required(cls, v, info):
        """Require user_context if model_type is personalized"""
        if info.data.get('model_type') == 'personalized' and v is None:
            raise ValueError('user_context is required when model_type is "personalized"')
        return v


class BatchPredictRequest(BaseModel):
    """Request schema for batch predictions"""
    course_ids: List[int] = Field(..., min_length=1, max_length=50)
    model_type: str = Field("grade_distribution")

    @field_validator('model_type')
    @classmethod
    def validate_model_type(cls, v):
        if v not in ['grade_distribution', 'full']:
            raise ValueError('model_type must be "grade_distribution" or "full"')
        return v


# ============================================================================
# Response Schemas
# ============================================================================

class ConfidenceInterval(BaseModel):
    """Confidence interval for prediction"""
    lower: float = Field(..., ge=0.0, le=4.0)
    upper: float = Field(..., ge=0.0, le=4.0)


class PredictionResult(BaseModel):
    """Prediction result with actual GPA for comparison"""
    predicted_gpa: float = Field(..., ge=0.0, le=4.0)
    actual_gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    error: Optional[float] = None
    confidence_interval: ConfidenceInterval


class ModelInfo(BaseModel):
    """Model metadata"""
    model_type: str
    model_name: str
    description: Optional[str] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    features_used: List[str]
    num_features: int


class CourseInfo(BaseModel):
    """Basic course information"""
    course_id: int
    subject: str
    number: str
    full_name: str


class PredictResponse(BaseModel):
    """Complete prediction response"""
    prediction: PredictionResult
    model_info: ModelInfo
    input_features: Dict[str, float]
    course: CourseInfo


class GradeDistributionProbs(BaseModel):
    """Grade probability distribution for personalized predictions"""
    A: float = Field(..., ge=0.0, le=1.0)
    A_minus: float = Field(..., ge=0.0, le=1.0, alias="A-")
    B_plus: float = Field(..., ge=0.0, le=1.0, alias="B+")
    B: float = Field(..., ge=0.0, le=1.0)
    B_minus: float = Field(..., ge=0.0, le=1.0, alias="B-")
    C_plus: float = Field(..., ge=0.0, le=1.0, alias="C+")
    C: float = Field(..., ge=0.0, le=1.0)
    C_minus: float = Field(..., ge=0.0, le=1.0, alias="C-")
    D: float = Field(..., ge=0.0, le=1.0)
    F: float = Field(..., ge=0.0, le=1.0)

    class Config:
        populate_by_name = True


class PersonalizedPredictionResult(BaseModel):
    """Personalized prediction with grade distribution and uncertainty"""
    course_id: int
    model_type: str = "personalized"
    predicted_gpa_mean: float = Field(..., ge=0.0, le=4.0)
    predicted_gpa_std: float = Field(..., ge=0.0)
    grade_distribution: GradeDistributionProbs
    confidence_note: str = Field(
        default="This is a statistical estimate based on historical patterns, not an individual outcome.",
        description="Disclaimer about prediction nature"
    )


class PrivacyInfo(BaseModel):
    """Privacy information for user data handling"""
    stored: bool = Field(default=False, description="Whether personal data is stored")
    logged: bool = Field(default=False, description="Whether personal data is logged")
    note: str = Field(
        default="Personal inputs are processed in-memory only and are not retained.",
        description="Privacy policy note"
    )


class PersonalizedPredictResponse(BaseModel):
    """Response for personalized predictions"""
    prediction: PersonalizedPredictionResult
    privacy: PrivacyInfo
    course: CourseInfo


class BatchPredictResponse(BaseModel):
    """Batch prediction response"""
    predictions: List[PredictResponse]
    summary: Dict[str, float]


# ============================================================================
# Course Schemas
# ============================================================================

class GradeDistribution(BaseModel):
    """Grade distribution entry"""
    letter_grade: str
    percentage: float


class CourseFeatures(BaseModel):
    """Course features for ML model"""
    grade_entropy: Optional[float] = None
    grade_skewness: Optional[float] = None
    pct_a_range: Optional[float] = None
    pct_passing: Optional[float] = None


class GradingStructure(BaseModel):
    """Grading structure details"""
    pct_exams: Optional[float] = None
    pct_projects: Optional[float] = None
    pct_homework: Optional[float] = None
    pct_participation: Optional[float] = None
    pct_other: Optional[float] = None
    num_exams: Optional[int] = None
    num_projects: Optional[int] = None
    num_homeworks: Optional[int] = None
    has_final_exam: Optional[bool] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None


class Course(BaseModel):
    """Course with basic features"""
    course_id: int
    subject: str
    number: str
    full_name: str
    avg_gpa: Optional[float] = None
    total_students: Optional[int] = None
    features: CourseFeatures
    has_grading_structure: bool


class CourseDetail(BaseModel):
    """Detailed course information including grade distribution"""
    course_id: int
    subject: str
    number: str
    full_name: str
    avg_gpa: Optional[float] = None
    total_students: Optional[int] = None
    grade_entropy: Optional[float] = None
    grade_skewness: Optional[float] = None
    pct_a_range: Optional[float] = None
    pct_passing: Optional[float] = None
    grade_distribution: List[GradeDistribution]
    grading_structure: Optional[GradingStructure] = None


class CoursesResponse(BaseModel):
    """List of courses with pagination"""
    courses: List[Course]
    total: int
    limit: int
    offset: int


# ============================================================================
# Health & Utility Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database_connected: bool
    models_loaded: bool
    model_count: int


class ModelsResponse(BaseModel):
    """List of available models"""
    models: List[ModelInfo]


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    error_type: Optional[str] = None
