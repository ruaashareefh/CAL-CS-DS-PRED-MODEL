import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import CourseList from '../components/CourseList';
import { courseAPI, handleAPIError } from '../services/api';

const CoursesPage = () => {
  const navigate = useNavigate();
  const [subject, setSubject] = useState('');

  // Fetch courses
  const { data, isLoading, error } = useQuery({
    queryKey: ['courses', subject],
    queryFn: async () => {
      const params = subject ? { subject, limit: 100 } : { limit: 100 };
      const response = await courseAPI.getAllCourses(params);
      return response.data;
    },
  });

  const handleSelectCourse = (course) => {
    // Navigate to home page with selected course
    // You could also navigate to a detail page
    navigate('/', { state: { selectedCourse: course } });
  };

  return (
    <div className="main-content">
      <div className="card">
        <h2>Browse Courses</h2>
        <p style={{ marginBottom: '1.5rem', color: '#666' }}>
          Explore all {data?.total || 30} courses with grade distribution data from UC Berkeley.
          Click on a course to predict its difficulty.
        </p>

        <div className="form-group">
          <label htmlFor="subject-filter">Filter by Subject</label>
          <select
            id="subject-filter"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
          >
            <option value="">All Subjects</option>
            <option value="COMPSCI">Computer Science (COMPSCI)</option>
            <option value="DATA">Data Science (DATA)</option>
          </select>
        </div>

        {isLoading && (
          <div className="loading">
            <div className="spinner"></div>
          </div>
        )}

        {error && (
          <div className="error">
            Failed to load courses: {handleAPIError(error)}
          </div>
        )}

        {data && (
          <>
            <div style={{ marginBottom: '1rem', color: '#666', fontSize: '0.9rem' }}>
              Showing {data.courses.length} of {data.total} courses
            </div>
            <CourseList courses={data.courses} onSelectCourse={handleSelectCourse} />
          </>
        )}
      </div>
    </div>
  );
};

export default CoursesPage;
