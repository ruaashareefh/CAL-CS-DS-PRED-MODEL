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
      <h2>Prediction for {course.full_name}</h2>

      {/* Most Probable Grade - Big and Prominent */}
      <div style={{
        textAlign: 'center',
        padding: '2rem',
        backgroundColor: '#f0f7ff',
        borderRadius: '8px',
        marginBottom: '2rem',
        border: '3px solid #003262'
      }}>
        <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem', fontWeight: 600 }}>
          MOST PROBABLE GRADE
        </div>
        <div style={{
          fontSize: '4rem',
          fontWeight: 'bold',
          color: '#003262',
          lineHeight: 1,
          marginBottom: '0.5rem'
        }}>
          {letterGrade}
        </div>
        <div style={{ fontSize: '1.5rem', color: '#FDB515', fontWeight: 600 }}>
          GPA: {predicted_gpa.toFixed(2)}
        </div>
      </div>

      {/* GPA Visualization */}
      <div className="gpa-meter">
        <h3>GPA Breakdown</h3>
        <div className="gpa-meter-bar">
          <div
            className="gpa-marker"
            style={{ left: `${markerPosition}%` }}
            title={`Predicted: ${predicted_gpa.toFixed(2)}`}
          >
            {predicted_gpa.toFixed(2)}
          </div>
        </div>
        <div className="gpa-labels">
          <span>0.0</span>
          <span>1.0</span>
          <span>2.0</span>
          <span>3.0</span>
          <span>4.0</span>
        </div>

        <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: '#666' }}>Predicted GPA</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#003262' }}>
                {predicted_gpa.toFixed(2)}
              </div>
            </div>

            {actual_gpa !== null && (
              <div>
                <div style={{ fontSize: '0.85rem', color: '#666' }}>Actual GPA</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#555' }}>
                  {actual_gpa.toFixed(2)}
                </div>
              </div>
            )}

            {error !== null && (
              <div>
                <div style={{ fontSize: '0.85rem', color: '#666' }}>Prediction Error</div>
                <div
                  style={{
                    fontSize: '1.5rem',
                    fontWeight: 600,
                    color: Math.abs(error) < 0.1 ? '#060' : '#c00',
                  }}
                >
                  {error > 0 ? '+' : ''}{error.toFixed(3)}
                </div>
              </div>
            )}

            <div>
              <div style={{ fontSize: '0.85rem', color: '#666' }}>95% Confidence Interval</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#555' }}>
                [{confidence_interval.lower.toFixed(2)}, {confidence_interval.upper.toFixed(2)}]
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Input Features */}
      <div style={{ marginTop: '2rem' }}>
        <h3>Input Features Used</h3>
        <div className="feature-grid">
          {Object.entries(input_features).map(([key, value]) => (
            <div key={key} className="feature-item">
              <div className="feature-label">{formatFeatureName(key)}</div>
              <div className="feature-value">
                {typeof value === 'number' ? value.toFixed(3) : value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Prediction Accuracy Info */}
      <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f0f7ff', borderRadius: '4px' }}>
        <h3>Prediction Details</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '0.75rem' }}>
          <div>
            <div style={{ fontSize: '0.85rem', color: '#666' }}>Prediction Type</div>
            <div style={{ fontWeight: 600 }}>{model_info.model_name}</div>
          </div>
          {model_info.mae && (
            <div>
              <div style={{ fontSize: '0.85rem', color: '#666' }}>Average Error</div>
              <div style={{ fontWeight: 600 }}>±{model_info.mae.toFixed(3)} GPA</div>
            </div>
          )}
          {model_info.r2 && (
            <div>
              <div style={{ fontSize: '0.85rem', color: '#666' }}>Accuracy Score</div>
              <div style={{ fontWeight: 600 }}>{(model_info.r2 * 100).toFixed(1)}%</div>
            </div>
          )}
          <div>
            <div style={{ fontSize: '0.85rem', color: '#666' }}>Data Points Analyzed</div>
            <div style={{ fontWeight: 600 }}>{model_info.num_features}</div>
          </div>
        </div>
        {model_info.description && (
          <div style={{ marginTop: '0.75rem', fontSize: '0.9rem', color: '#555' }}>
            {model_info.description}
          </div>
        )}
      </div>
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
