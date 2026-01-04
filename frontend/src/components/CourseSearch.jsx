import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { courseAPI } from '../services/api';

const CourseSearch = ({ onSelectCourse }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);

  // Fetch all courses
  const { data, isLoading, error } = useQuery({
    queryKey: ['courses'],
    queryFn: async () => {
      const response = await courseAPI.getAllCourses({ limit: 100 });
      return response.data;
    },
  });

  // Filter courses based on search term
  const filteredCourses = React.useMemo(() => {
    if (!data?.courses) return [];
    if (!searchTerm) return data.courses;

    const term = searchTerm.toLowerCase();
    return data.courses.filter((course) =>
      course.full_name.toLowerCase().includes(term) ||
      course.subject.toLowerCase().includes(term) ||
      course.number.toLowerCase().includes(term)
    );
  }, [data?.courses, searchTerm]);

  const handleSelectCourse = (course) => {
    setSearchTerm(course.full_name);
    setShowDropdown(false);
    onSelectCourse(course);
  };

  return (
    <div className="form-group">
      <label htmlFor="course-search">Search for a Course</label>
      <div style={{ position: 'relative' }}>
        <input
          id="course-search"
          type="text"
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setShowDropdown(true);
          }}
          onFocus={() => setShowDropdown(true)}
          placeholder="e.g., COMPSCI 61A, DATA C8"
          disabled={isLoading}
        />

        {error && (
          <div className="error" style={{ marginTop: '0.5rem' }}>
            Failed to load courses: {error.message}
          </div>
        )}

        {showDropdown && searchTerm && filteredCourses.length > 0 && (
          <div
            style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              backgroundColor: 'white',
              border: '1px solid #ddd',
              borderRadius: '4px',
              maxHeight: '300px',
              overflowY: 'auto',
              zIndex: 1000,
              marginTop: '4px',
              boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
            }}
          >
            {filteredCourses.slice(0, 20).map((course) => (
              <div
                key={course.course_id}
                onClick={() => handleSelectCourse(course)}
                style={{
                  padding: '0.75rem',
                  cursor: 'pointer',
                  borderBottom: '1px solid #f0f0f0',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => (e.target.style.backgroundColor = '#f5f5f5')}
                onMouseLeave={(e) => (e.target.style.backgroundColor = 'white')}
              >
                <div style={{ fontWeight: 600, color: '#003262' }}>
                  {course.full_name}
                </div>
                <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.25rem' }}>
                  Avg GPA: {course.avg_gpa?.toFixed(2) || 'N/A'} |
                  {' '}{course.total_students?.toLocaleString() || 0} students
                </div>
              </div>
            ))}
          </div>
        )}

        {showDropdown && searchTerm && filteredCourses.length === 0 && !isLoading && (
          <div
            style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              backgroundColor: 'white',
              border: '1px solid #ddd',
              borderRadius: '4px',
              padding: '1rem',
              marginTop: '4px',
              color: '#666',
            }}
          >
            No courses found matching "{searchTerm}"
          </div>
        )}
      </div>

      {isLoading && (
        <div style={{ marginTop: '0.5rem', color: '#666', fontSize: '0.9rem' }}>
          Loading courses...
        </div>
      )}
    </div>
  );
};

export default CourseSearch;
