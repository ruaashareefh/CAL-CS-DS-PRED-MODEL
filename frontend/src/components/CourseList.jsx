import React from 'react';

const CourseList = ({ courses, onSelectCourse }) => {
  if (!courses || courses.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
        No courses found
      </div>
    );
  }

  return (
    <div className="course-list">
      {courses.map((course) => (
        <div
          key={course.course_id}
          className="course-item"
          onClick={() => onSelectCourse && onSelectCourse(course)}
        >
          <div className="course-name">{course.full_name}</div>
          <div className="course-stats">
            <span>
              <strong>Avg GPA:</strong> {course.avg_gpa?.toFixed(2) || 'N/A'}
            </span>
            <span>
              <strong>Students:</strong> {course.total_students?.toLocaleString() || 'N/A'}
            </span>
            {course.features && (
              <>
                <span>
                  <strong>Entropy:</strong> {course.features.grade_entropy?.toFixed(2) || 'N/A'}
                </span>
                <span>
                  <strong>% A-range:</strong> {course.features.pct_a_range?.toFixed(1) || 'N/A'}%
                </span>
              </>
            )}
            {course.has_grading_structure && (
              <span style={{ color: '#060', fontWeight: 600 }}>
                ✓ Has Grading Structure
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default CourseList;
