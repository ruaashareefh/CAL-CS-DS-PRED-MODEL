"""
Course endpoints for browsing and retrieving course data
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..models.schemas import CoursesResponse, CourseDetail, Course, CourseFeatures, GradeDistribution, GradingStructure
from ..database.connection import get_db
from ..database.queries import get_all_courses, get_course_by_id, get_total_courses

router = APIRouter()


@router.get("/courses", response_model=CoursesResponse)
async def list_courses(
    subject: Optional[str] = Query(None, description="Filter by subject (e.g., 'COMPSCI', 'DATA')"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    List all courses with their features

    Supports filtering by subject and pagination.

    Args:
        subject: Optional filter by course subject
        limit: Maximum number of results (default: 50, max: 100)
        offset: Pagination offset (default: 0)

    Returns:
        CoursesResponse: List of courses with pagination info
    """
    try:
        with get_db() as conn:
            # Get courses
            courses_data = get_all_courses(conn, subject=subject, limit=limit, offset=offset)

            # Get total count for pagination
            total = get_total_courses(conn, subject=subject)

            # Convert to Course schema
            courses = []
            for course_data in courses_data:
                course = Course(
                    course_id=course_data['course_id'],
                    subject=course_data['subject'],
                    number=course_data['number'],
                    full_name=course_data['full_name'],
                    avg_gpa=course_data['avg_gpa'],
                    total_students=course_data['total_students'],
                    features=CourseFeatures(
                        grade_entropy=course_data['grade_entropy'],
                        grade_skewness=course_data['grade_skewness'],
                        pct_a_range=course_data['pct_a_range'],
                        pct_passing=course_data['pct_passing']
                    ),
                    has_grading_structure=bool(course_data['has_grading_structure'])
                )
                courses.append(course)

            return CoursesResponse(
                courses=courses,
                total=total,
                limit=limit,
                offset=offset
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/courses/{course_id}", response_model=CourseDetail)
async def get_course(course_id: int):
    """
    Get detailed information about a specific course

    Includes:
    - Course metadata (subject, number, GPA)
    - Grade distribution (percentage of each letter grade)
    - Grading structure (if available)

    Args:
        course_id: Course ID

    Returns:
        CourseDetail: Detailed course information

    Raises:
        HTTPException: 404 if course not found
    """
    try:
        with get_db() as conn:
            course_data = get_course_by_id(conn, course_id)

            if not course_data:
                raise HTTPException(status_code=404, detail=f"Course ID {course_id} not found")

            # Convert grade distribution
            grade_dist = [
                GradeDistribution(
                    letter_grade=g['letter_grade'],
                    percentage=g['percentage']
                )
                for g in course_data['grade_distribution']
            ]

            # Convert grading structure (if available)
            grading_structure = None
            if course_data['grading_structure']:
                gs = course_data['grading_structure']
                grading_structure = GradingStructure(
                    pct_exams=gs['pct_exams'],
                    pct_projects=gs['pct_projects'],
                    pct_homework=gs['pct_homework'],
                    pct_participation=gs['pct_participation'],
                    pct_other=gs['pct_other'],
                    num_exams=gs['num_exams'],
                    num_projects=gs['num_projects'],
                    num_homeworks=gs['num_homeworks'],
                    has_final_exam=bool(gs['has_final_exam']) if gs['has_final_exam'] is not None else None,
                    notes=gs['notes'],
                    source_url=gs['source_url']
                )

            return CourseDetail(
                course_id=course_data['course_id'],
                subject=course_data['subject'],
                number=course_data['number'],
                full_name=course_data['full_name'],
                avg_gpa=course_data['avg_gpa'],
                total_students=course_data['total_students'],
                grade_entropy=course_data['grade_entropy'],
                grade_skewness=course_data['grade_skewness'],
                pct_a_range=course_data['pct_a_range'],
                pct_passing=course_data['pct_passing'],
                grade_distribution=grade_dist,
                grading_structure=grading_structure
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
