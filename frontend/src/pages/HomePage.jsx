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
    prior_courses: '',
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
      contextData = {
        avg_gpa: userContext.avg_gpa ? parseFloat(userContext.avg_gpa) : null,
        units_this_semester: userContext.units_this_semester ? parseInt(userContext.units_this_semester) : null,
        hours_per_week_available: userContext.hours_per_week_available ? parseInt(userContext.hours_per_week_available) : null,
        comfort_level: parseInt(userContext.comfort_level),
        prior_courses: userContext.prior_courses ? userContext.prior_courses.split(',').map(s => s.trim()).filter(s => s) : null,
      };

      // Remove null values
      contextData = Object.fromEntries(
        Object.entries(contextData).filter(([_, v]) => v !== null && (Array.isArray(v) ? v.length > 0 : true))
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
        <p style={{ marginBottom: '1.5rem', color: '#666' }}>
          Select a course and model to predict the average GPA. The prediction uses machine learning
          models trained on historical grade distribution data from UC Berkeley.
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
          <label htmlFor="model-type">Select Model</label>
          <select
            id="model-type"
            value={modelType}
            onChange={(e) => setModelType(e.target.value)}
          >
            <option value="grade_distribution">
              Grade Distribution Model (Works for all courses)
            </option>
            <option
              value="full"
              disabled={selectedCourse && !selectedCourse.has_grading_structure}
            >
              Full Features Model (Requires grading structure data)
            </option>
            <option value="personalized">
              Personalized Prediction (Optional - with your academic info)
            </option>
          </select>
          <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.5rem' }}>
            {modelType === 'grade_distribution' ? (
              '✓ Uses entropy, skewness, and grade distribution features (MAE: 0.041)'
            ) : modelType === 'full' ? (
              '✓ Uses grade distribution + grading structure features (MAE: 0.061)'
            ) : (
              '🔒 Privacy-preserving: Your data is processed in-memory only, never stored'
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
                <label htmlFor="avg-gpa">Your Average GPA (0.0 - 4.0)</label>
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
                <label htmlFor="prior-courses">Prior Related Courses (comma-separated)</label>
                <input
                  type="text"
                  id="prior-courses"
                  placeholder="e.g., COMPSCI 61A, MATH 54"
                  value={userContext.prior_courses}
                  onChange={(e) => setUserContext({ ...userContext, prior_courses: e.target.value })}
                />
                <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.25rem' }}>
                  List courses you've taken that relate to this course
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
