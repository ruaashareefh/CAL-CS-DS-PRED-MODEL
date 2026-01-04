import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import CourseSearch from '../components/CourseSearch';
import PredictionCard from '../components/PredictionCard';
import { courseAPI, handleAPIError } from '../services/api';

const HomePage = () => {
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [modelType, setModelType] = useState('grade_distribution');
  const [prediction, setPrediction] = useState(null);

  // User context for personalized predictions
  const [userContext, setUserContext] = useState({
    avg_gpa: '',
    units_this_semester: '',
    hours_per_week_available: '',
    comfort_level: 3,
    prior_courses: [{ course_name: '', grade_received: '' }],
    notes: '',
  });

  // Prediction mutation
  const predictionMutation = useMutation({
    mutationFn: ({ courseId, modelType, userContext }) =>
      courseAPI.predict(courseId, modelType, userContext),
    onSuccess: (response) => {
      setPrediction(response.data);
    },
    onError: (error) => {
      alert(`Prediction failed: ${handleAPIError(error)}`);
    },
  });

  const handleSelectCourse = (course) => {
    setSelectedCourse(course);
    setPrediction(null);
  };

  const handlePredict = () => {
    if (!selectedCourse) {
      alert('Please select a course first');
      return;
    }

    // Prepare user context for personalized predictions
    let contextData = null;
    if (modelType === 'personalized') {
      // Filter out empty prior courses
      const validPriorCourses = userContext.prior_courses
        .filter(pc => pc.course_name.trim() && pc.grade_received)
        .map(pc => ({
          course_name: pc.course_name.trim(),
          grade_received: pc.grade_received  // Letter grade (A+, A, A-, etc.)
        }));

      contextData = {
        avg_gpa: userContext.avg_gpa ? parseFloat(userContext.avg_gpa) : null,
        units_this_semester: userContext.units_this_semester ? parseInt(userContext.units_this_semester) : null,
        hours_per_week_available: userContext.hours_per_week_available ? parseInt(userContext.hours_per_week_available) : null,
        comfort_level: parseInt(userContext.comfort_level),
        prior_courses: validPriorCourses.length > 0 ? validPriorCourses : null,
        notes: userContext.notes.trim() || null,
      };

      // Remove null values
      contextData = Object.fromEntries(
        Object.entries(contextData).filter(([_, v]) => v !== null)
      );

      // Require at least one field for personalized prediction
      if (Object.keys(contextData).length === 0) {
        alert('Please provide at least one piece of information for personalized prediction');
        return;
      }
    }

    predictionMutation.mutate({
      courseId: selectedCourse.course_id,
      modelType,
      userContext: contextData,
    });
  };

  return (
    <div className="main-content">
      <div className="card">
        <h2>Predict Course Difficulty</h2>
        <div style={{
          padding: '0.75rem 1rem',
          backgroundColor: '#003262',
          color: 'white',
          borderRadius: '4px',
          marginBottom: '1rem',
          fontWeight: 600,
          fontSize: '0.95rem',
          textAlign: 'center'
        }}>
          📚 CS, Data Science & EECS Courses Only
        </div>
        <p style={{ marginBottom: '1.5rem', color: '#666' }}>
          Select a course to predict the expected GPA. Predictions are based on historical grade data
          from UC Berkeley Computer Science, Data Science, and EECS courses.
        </p>

        <CourseSearch onSelectCourse={handleSelectCourse} />

        {selectedCourse && (
          <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#003262', marginBottom: '0.5rem' }}>
              Selected: {selectedCourse.full_name}
            </div>
            <div style={{ fontSize: '0.9rem', color: '#666' }}>
              Current Avg GPA: {selectedCourse.avg_gpa?.toFixed(2) || 'N/A'} |
              {' '}{selectedCourse.total_students?.toLocaleString() || 0} students enrolled
              {selectedCourse.has_grading_structure && (
                <span style={{ color: '#060', fontWeight: 600 }}> | ✓ Has Grading Structure</span>
              )}
            </div>
          </div>
        )}

        <div className="form-group" style={{ marginTop: '1.5rem' }}>
          <label htmlFor="model-type">Prediction Type</label>
          <select
            id="model-type"
            value={modelType}
            onChange={(e) => setModelType(e.target.value)}
          >
            <option value="grade_distribution">
              Standard Prediction (Recommended - Works for all courses)
            </option>
            <option
              value="full"
              disabled={selectedCourse && !selectedCourse.has_grading_structure}
            >
              Detailed Prediction (Includes assignment weights - Limited availability)
            </option>
            <option value="personalized">
              Personalized Prediction (Add your academic background)
            </option>
          </select>
          <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.5rem' }}>
            {modelType === 'grade_distribution' ? (
              '✓ Based on grade patterns from 35 courses (Average error: ±0.035 GPA)'
            ) : modelType === 'full' ? (
              '✓ Includes exam/project weights (Average error: ±0.061 GPA)'
            ) : (
              '🔒 Privacy-focused: Your information is processed instantly and never stored'
            )}
          </div>
        </div>

        {/* Personalized Prediction Form */}
        {modelType === 'personalized' && (
          <div style={{
            marginTop: '1.5rem',
            padding: '1.5rem',
            backgroundColor: '#f0f7ff',
            border: '2px solid #003262',
            borderRadius: '8px'
          }}>
            <h3 style={{ marginTop: 0, color: '#003262', fontSize: '1.1rem' }}>
              Optional: Your Academic Context
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#555', marginBottom: '1rem' }}>
              🔒 <strong>Privacy Notice:</strong> All information is processed in-memory only and never stored.
              Fill in as much or as little as you want - all fields are optional.
            </p>

            <div style={{ display: 'grid', gap: '1rem' }}>
              <div className="form-group">
                <label htmlFor="avg-gpa">Your Overall GPA (0.0 - 4.0)</label>
                <input
                  type="number"
                  id="avg-gpa"
                  min="0"
                  max="4"
                  step="0.01"
                  placeholder="e.g., 3.5"
                  value={userContext.avg_gpa}
                  onChange={(e) => setUserContext({ ...userContext, avg_gpa: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label htmlFor="units">Units This Semester (0 - 35)</label>
                <input
                  type="number"
                  id="units"
                  min="0"
                  max="35"
                  placeholder="e.g., 16"
                  value={userContext.units_this_semester}
                  onChange={(e) => setUserContext({ ...userContext, units_this_semester: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label htmlFor="hours">Hours Per Week Available for Study (0 - 80)</label>
                <input
                  type="number"
                  id="hours"
                  min="0"
                  max="80"
                  placeholder="e.g., 20"
                  value={userContext.hours_per_week_available}
                  onChange={(e) => setUserContext({ ...userContext, hours_per_week_available: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label htmlFor="comfort">Comfort Level with Course Material (1 = Low, 5 = High)</label>
                <select
                  id="comfort"
                  value={userContext.comfort_level}
                  onChange={(e) => setUserContext({ ...userContext, comfort_level: e.target.value })}
                >
                  <option value="1">1 - Not familiar at all</option>
                  <option value="2">2 - Slightly familiar</option>
                  <option value="3">3 - Moderately familiar</option>
                  <option value="4">4 - Very familiar</option>
                  <option value="5">5 - Expert level</option>
                </select>
              </div>

              <div className="form-group">
                <label>Prior Related Courses with Grades</label>
                <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.75rem' }}>
                  Enter courses you've taken and your grades. Used by Kalman filter to estimate your performance.
                </div>

                {userContext.prior_courses.map((course, index) => (
                  <div key={index} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', alignItems: 'flex-start' }}>
                    <div style={{ flex: 2 }}>
                      <input
                        type="text"
                        placeholder="e.g., COMPSCI 61A"
                        value={course.course_name}
                        onChange={(e) => {
                          const newCourses = [...userContext.prior_courses];
                          newCourses[index].course_name = e.target.value;
                          setUserContext({ ...userContext, prior_courses: newCourses });
                        }}
                        style={{ width: '100%' }}
                      />
                    </div>
                    <div style={{ flex: 1 }}>
                      <select
                        value={course.grade_received}
                        onChange={(e) => {
                          const newCourses = [...userContext.prior_courses];
                          newCourses[index].grade_received = e.target.value;
                          setUserContext({ ...userContext, prior_courses: newCourses });
                        }}
                        style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                      >
                        <option value="">Select Grade</option>
                        <option value="A+">A+ (4.0)</option>
                        <option value="A">A (4.0)</option>
                        <option value="A-">A- (3.7)</option>
                        <option value="B+">B+ (3.3)</option>
                        <option value="B">B (3.0)</option>
                        <option value="B-">B- (2.7)</option>
                        <option value="C+">C+ (2.3)</option>
                        <option value="C">C (2.0)</option>
                        <option value="C-">C- (1.7)</option>
                        <option value="D">D (1.0)</option>
                        <option value="F">F (0.0)</option>
                      </select>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        const newCourses = userContext.prior_courses.filter((_, i) => i !== index);
                        setUserContext({ ...userContext, prior_courses: newCourses.length > 0 ? newCourses : [{ course_name: '', grade_received: '' }] });
                      }}
                      style={{
                        padding: '0.5rem 0.75rem',
                        backgroundColor: '#dc3545',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.9rem'
                      }}
                    >
                      Remove
                    </button>
                  </div>
                ))}

                <button
                  type="button"
                  onClick={() => {
                    setUserContext({
                      ...userContext,
                      prior_courses: [...userContext.prior_courses, { course_name: '', grade_received: '' }]
                    });
                  }}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: '#003262',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    marginTop: '0.5rem'
                  }}
                >
                  + Add Another Course
                </button>
              </div>

              <div className="form-group" style={{ marginTop: '1.5rem' }}>
                <label htmlFor="notes">Additional Context (Optional)</label>
                <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.5rem' }}>
                  Add any relevant circumstances (work schedule, prior experience, health, motivation, etc.)
                </div>
                <textarea
                  id="notes"
                  rows="4"
                  placeholder="e.g., Working 20 hours/week, strong interest in the subject, previous programming experience..."
                  value={userContext.notes}
                  onChange={(e) => setUserContext({ ...userContext, notes: e.target.value })}
                  maxLength="1000"
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontFamily: 'inherit',
                    fontSize: '1rem',
                    resize: 'vertical'
                  }}
                />
                <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.25rem' }}>
                  {userContext.notes.length}/1000 characters
                </div>
                <div style={{
                  marginTop: '0.75rem',
                  padding: '0.75rem',
                  backgroundColor: '#e8f4f8',
                  border: '1px solid #17a2b8',
                  borderRadius: '4px',
                  fontSize: '0.85rem'
                }}>
                  <strong>ℹ️ Note:</strong> Your additional context is processed to provide a small adjustment to your prediction.
                  This information is never stored in our database.
                </div>
              </div>
            </div>

            <div style={{
              marginTop: '1rem',
              padding: '0.75rem',
              backgroundColor: '#fff3cd',
              border: '1px solid #ffc107',
              borderRadius: '4px',
              fontSize: '0.85rem'
            }}>
              <strong>⚠️ Uncertainty Notice:</strong> This prediction shows probabilities, not guarantees.
              Individual outcomes vary based on many factors beyond what we can measure.
            </div>
          </div>
        )}

        <button
          className="btn btn-primary"
          onClick={handlePredict}
          disabled={!selectedCourse || predictionMutation.isPending}
          style={{ marginTop: '1rem', width: '100%' }}
        >
          {predictionMutation.isPending ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
              <div style={{ width: '20px', height: '20px' }} className="spinner"></div>
              Predicting...
            </span>
          ) : (
            'Predict GPA'
          )}
        </button>
      </div>

      {predictionMutation.isError && (
        <div className="error">
          {handleAPIError(predictionMutation.error)}
        </div>
      )}

      {prediction && <PredictionCard prediction={prediction} />}
    </div>
  );
};

export default HomePage;
