import React from 'react';

// Convert GPA to most likely letter grade using midpoint thresholds
// Berkeley scale: A+=4.0, A=4.0, A-=3.7, B+=3.3, B=3.0, B-=2.7, C+=2.3, C=2.0, C-=1.7, D=1.0, F=0.0
const gpaToLetterGrade = (gpa) => {
  if (gpa >= 3.85) return 'A+';  // Midpoint between A (4.0) and A- (3.7)
  if (gpa >= 3.50) return 'A-';  // Midpoint between A- (3.7) and B+ (3.3)
  if (gpa >= 3.15) return 'B+';  // Midpoint between B+ (3.3) and B (3.0)
  if (gpa >= 2.85) return 'B';   // Midpoint between B (3.0) and B- (2.7)
  if (gpa >= 2.50) return 'B-';  // Midpoint between B- (2.7) and C+ (2.3)
  if (gpa >= 2.15) return 'C+';  // Midpoint between C+ (2.3) and C (2.0)
  if (gpa >= 1.85) return 'C';   // Midpoint between C (2.0) and C- (1.7)
  if (gpa >= 1.35) return 'C-';  // Midpoint between C- (1.7) and D (1.0)
  if (gpa >= 0.50) return 'D';   // Midpoint between D (1.0) and F (0.0)
  return 'F';
};

const PredictionCard = ({ prediction }) => {
  if (!prediction) return null;

  // Check if this is a personalized prediction
  const isPersonalized = prediction.privacy !== undefined;

  if (isPersonalized) {
    return <PersonalizedPredictionCard prediction={prediction} />;
  }

  const { prediction: pred, model_info, input_features, course } = prediction;
  const { predicted_gpa, actual_gpa, error, confidence_interval } = pred;

  // Calculate position for GPA marker (0-4 scale)
  const markerPosition = (predicted_gpa / 4) * 100;

  // Get letter grade
  const letterGrade = gpaToLetterGrade(predicted_gpa);

  return (
    <div className="card">
      <h2>{course.full_name}</h2>

      {/* Most Probable Grade - Big and Prominent */}
      <div style={{
        textAlign: 'center',
        padding: '2rem',
        backgroundColor: '#f0f7ff',
        borderRadius: '8px',
        marginBottom: '2rem',
        border: '3px solid #003262'
      }}>
        <div style={{ fontSize: '1rem', color: '#666', marginBottom: '0.5rem', fontWeight: 600 }}>
          YOUR EXPECTED GRADE IN THIS CLASS
        </div>
        <div style={{
          fontSize: '4.5rem',
          fontWeight: 'bold',
          color: '#003262',
          lineHeight: 1,
          marginBottom: '0.75rem'
        }}>
          {letterGrade}
        </div>
        <div style={{ fontSize: '1.3rem', color: '#555', fontWeight: 500, marginBottom: '0.5rem' }}>
          Expected GPA: <span style={{ color: '#FDB515', fontWeight: 700, fontSize: '1.5rem' }}>{predicted_gpa.toFixed(2)}</span>
        </div>
        <div style={{ fontSize: '0.95rem', color: '#666', marginTop: '0.75rem', borderTop: '1px solid #ddd', paddingTop: '0.75rem' }}>
          Class Average: <span style={{ fontWeight: 600, color: '#003262' }}>{actual_gpa?.toFixed(2) || 'N/A'}</span>
        </div>
      </div>

      {/* Comparison Section */}
      {actual_gpa !== null && (
        <div style={{ marginBottom: '2rem', padding: '1.25rem', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
          <h3 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1.1rem' }}>How You Compare</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#e3f2fd', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.5rem' }}>Your Expected GPA</div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: '#003262' }}>
                {predicted_gpa.toFixed(2)}
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#fff3e0', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.5rem' }}>Class Average GPA</div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: '#FDB515' }}>
                {actual_gpa.toFixed(2)}
              </div>
            </div>
          </div>
          <div style={{ marginTop: '1rem', textAlign: 'center', fontSize: '0.9rem', color: '#555' }}>
            {error !== null && (
              <span>
                Your prediction is <strong style={{ color: Math.abs(error) < 0.1 ? '#060' : '#666' }}>
                  {Math.abs(error).toFixed(3)} GPA points
                </strong> {error > 0 ? 'above' : 'below'} the class average
              </span>
            )}
          </div>
        </div>
      )}

      {/* Confidence Interval */}
      <div style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#e8f5e9', borderRadius: '8px', border: '1px solid #4caf50' }}>
        <div style={{ fontSize: '0.9rem', color: '#2e7d32', marginBottom: '0.5rem', fontWeight: 600 }}>
          ✓ Prediction Confidence
        </div>
        <div style={{ fontSize: '0.95rem', color: '#555' }}>
          We're 95% confident your GPA in this class will be between{' '}
          <strong style={{ color: '#2e7d32' }}>{confidence_interval.lower.toFixed(2)}</strong> and{' '}
          <strong style={{ color: '#2e7d32' }}>{confidence_interval.upper.toFixed(2)}</strong>
        </div>
      </div>

      {/* Technical Details - Collapsible */}
      <details style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f5f5f5', borderRadius: '8px', cursor: 'pointer' }}>
        <summary style={{ fontWeight: 600, color: '#003262', fontSize: '1rem', cursor: 'pointer' }}>
          📊 Show Technical Details
        </summary>

        <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid #ddd' }}>
          <h4 style={{ marginTop: 0, fontSize: '0.95rem', color: '#555' }}>Prediction Method: {model_info.model_name}</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginTop: '0.75rem', marginBottom: '1.5rem' }}>
            {model_info.mae && (
              <div>
                <div style={{ fontSize: '0.8rem', color: '#666' }}>Average Error</div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>±{model_info.mae.toFixed(3)} GPA</div>
              </div>
            )}
            {model_info.r2 && (
              <div>
                <div style={{ fontSize: '0.8rem', color: '#666' }}>Accuracy</div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{(model_info.r2 * 100).toFixed(1)}%</div>
              </div>
            )}
          </div>

          <h4 style={{ marginTop: '1rem', fontSize: '0.95rem', color: '#555' }}>Data Used for Prediction</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem', marginTop: '0.5rem' }}>
            {Object.entries(input_features).map(([key, value]) => (
              <div key={key} style={{ fontSize: '0.85rem', color: '#666', padding: '0.5rem', backgroundColor: 'white', borderRadius: '4px' }}>
                <div style={{ fontWeight: 500 }}>{formatFeatureName(key)}</div>
                <div style={{ color: '#003262', fontWeight: 600 }}>
                  {typeof value === 'number' ? value.toFixed(3) : value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </details>
    </div>
  );
};

// Helper function to format feature names
const formatFeatureName = (name) => {
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Personalized Prediction Card Component
const PersonalizedPredictionCard = ({ prediction }) => {
  const { prediction: pred, privacy, course } = prediction;
  const { predicted_gpa_mean, predicted_gpa_std, grade_distribution, confidence_note } = pred;

  // Convert grade distribution to array for easier rendering
  const grades = [
    { grade: 'A+', prob: grade_distribution['A+'] || 0 },
    { grade: 'A', prob: grade_distribution['A'] },
    { grade: 'A-', prob: grade_distribution['A-'] },
    { grade: 'B+', prob: grade_distribution['B+'] },
    { grade: 'B', prob: grade_distribution.B },
    { grade: 'B-', prob: grade_distribution['B-'] },
    { grade: 'C+', prob: grade_distribution['C+'] },
    { grade: 'C', prob: grade_distribution.C },
    { grade: 'C-', prob: grade_distribution['C-'] },
    { grade: 'D', prob: grade_distribution.D },
    { grade: 'F', prob: grade_distribution.F },
  ];

  // Find highest probability grade
  const maxProb = Math.max(...grades.map(g => g.prob));
  const mostLikelyGrade = grades.find(g => g.prob === maxProb);

  return (
    <div className="card">
      <h2>Your Personalized Prediction for {course.full_name}</h2>

      {/* Most Likely Grade - Big and Prominent */}
      <div style={{
        textAlign: 'center',
        padding: '2rem',
        backgroundColor: '#f0f7ff',
        borderRadius: '8px',
        marginBottom: '2rem',
        border: '3px solid #003262'
      }}>
        <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem', fontWeight: 600 }}>
          MOST LIKELY GRADE FOR YOU
        </div>
        <div style={{
          fontSize: '4rem',
          fontWeight: 'bold',
          color: '#003262',
          lineHeight: 1,
          marginBottom: '0.5rem'
        }}>
          {mostLikelyGrade.grade}
        </div>
        <div style={{ fontSize: '1.5rem', color: '#FDB515', fontWeight: 600 }}>
          {(mostLikelyGrade.prob * 100).toFixed(1)}% probability
        </div>
        <div style={{ fontSize: '1.1rem', color: '#666', marginTop: '0.5rem' }}>
          Expected GPA: {predicted_gpa_mean.toFixed(2)} ± {predicted_gpa_std.toFixed(2)}
        </div>
      </div>

      {/* Privacy Notice */}
      <div style={{
        padding: '1rem',
        backgroundColor: '#d4edda',
        border: '1px solid #28a745',
        borderRadius: '4px',
        marginBottom: '1.5rem'
      }}>
        <div style={{ fontWeight: 600, color: '#155724', marginBottom: '0.5rem' }}>
          🔒 Privacy Confirmed
        </div>
        <div style={{ fontSize: '0.9rem', color: '#155724' }}>
          {privacy.note}
        </div>
      </div>

      {/* GPA Statistics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem',
        marginBottom: '2rem',
        padding: '1rem',
        backgroundColor: '#f9f9f9',
        borderRadius: '4px'
      }}>
        <div>
          <div style={{ fontSize: '0.85rem', color: '#666' }}>Predicted Mean GPA</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#003262' }}>
            {predicted_gpa_mean.toFixed(2)}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.85rem', color: '#666' }}>Uncertainty (Std Dev)</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#555' }}>
            ±{predicted_gpa_std.toFixed(2)}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.85rem', color: '#666' }}>Expected Range (±1 std)</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 600, color: '#555' }}>
            {Math.max(0, predicted_gpa_mean - predicted_gpa_std).toFixed(2)} - {Math.min(4, predicted_gpa_mean + predicted_gpa_std).toFixed(2)}
          </div>
        </div>
      </div>

      {/* Grade Distribution Bar Chart */}
      <div style={{ marginBottom: '2rem' }}>
        <h3>Grade Probability Distribution</h3>
        <div style={{ marginTop: '1rem' }}>
          {grades.map(({ grade, prob }) => (
            <div key={grade} style={{ marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ width: '40px', fontWeight: 600, fontSize: '0.95rem', color: '#003262' }}>
                  {grade}
                </div>
                <div style={{ flex: 1, position: 'relative' }}>
                  <div style={{
                    width: '100%',
                    height: '30px',
                    backgroundColor: '#e0e0e0',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${prob * 100}%`,
                      height: '100%',
                      backgroundColor: prob === maxProb ? '#FDB515' : '#003262',
                      transition: 'width 0.3s ease',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      paddingRight: '0.5rem',
                      color: 'white',
                      fontSize: '0.85rem',
                      fontWeight: 600
                    }}>
                      {prob > 0.05 && `${(prob * 100).toFixed(1)}%`}
                    </div>
                  </div>
                </div>
                <div style={{ width: '60px', textAlign: 'right', fontSize: '0.9rem', color: '#666' }}>
                  {(prob * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <div style={{
        padding: '1rem',
        backgroundColor: '#fff3cd',
        border: '1px solid #ffc107',
        borderRadius: '4px',
        fontSize: '0.9rem'
      }}>
        <div style={{ fontWeight: 600, color: '#856404', marginBottom: '0.5rem' }}>
          ⚠️ Important Disclaimer
        </div>
        <div style={{ color: '#856404' }}>
          {confidence_note}
        </div>
      </div>
    </div>
  );
};

export default PredictionCard;
