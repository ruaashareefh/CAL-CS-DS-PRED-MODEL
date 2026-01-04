import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { courseAPI, handleAPIError } from '../services/api';

const AboutPage = () => {
  // Fetch prediction method information
  const { data: modelsData, isLoading, error } = useQuery({
    queryKey: ['models'],
    queryFn: async () => {
      const response = await courseAPI.getModels();
      return response.data;
    },
  });

  return (
    <div className="main-content">
      <div className="card">
        <h2>About This Tool</h2>
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
          📚 Predictions for CS, Data Science & EECS Courses
        </div>
        <p style={{ marginBottom: '1rem' }}>
          This tool predicts expected grades for UC Berkeley courses in Computer Science,
          Data Science, and EECS based on historical grade data from BerkleyTime.
        </p>
        <p>
          The predictions help you understand course difficulty before enrollment by analyzing
          patterns in past grade distributions, assignment structures, and student performance.
        </p>
      </div>

      <div className="card">
        <h2>Dataset</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div className="feature-item">
            <div className="feature-label">Total Courses</div>
            <div className="feature-value">36</div>
          </div>
          <div className="feature-item">
            <div className="feature-label">Subjects</div>
            <div className="feature-value">CS, DATA, EECS</div>
          </div>
          <div className="feature-item">
            <div className="feature-label">Courses with Assignment Weights</div>
            <div className="feature-value">8</div>
          </div>
          <div className="feature-item">
            <div className="feature-label">Data Source</div>
            <div className="feature-value">BerkleyTime</div>
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Prediction Methods</h2>

        {isLoading && (
          <div className="loading">
            <div className="spinner"></div>
          </div>
        )}

        {error && (
          <div className="error">
            Failed to load prediction information: {handleAPIError(error)}
          </div>
        )}

        {modelsData?.models && (
          <div style={{ display: 'grid', gap: '1.5rem' }}>
            {modelsData.models.map((model) => (
              <div
                key={model.model_type}
                style={{
                  padding: '1.5rem',
                  backgroundColor: '#f9f9f9',
                  borderRadius: '4px',
                  borderLeft: '4px solid #003262',
                }}
              >
                <h3>{model.model_name}</h3>
                <p style={{ color: '#666', marginBottom: '1rem' }}>
                  {model.description}
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                  <div>
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>Average Error</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 600, color: '#003262' }}>
                      ±{model.mae?.toFixed(3) || 'N/A'} GPA
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>Accuracy</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 600, color: '#003262' }}>
                      {model.r2 ? `${(model.r2 * 100).toFixed(1)}%` : 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>Data Points</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 600, color: '#003262' }}>
                      {model.num_features}
                    </div>
                  </div>
                </div>

                <details style={{ marginTop: '1rem' }}>
                  <summary style={{ cursor: 'pointer', fontWeight: 600, color: '#003262' }}>
                    What data is analyzed?
                  </summary>
                  <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                    {model.features_used.map((feature) => (
                      <li key={feature} style={{ color: '#666', marginBottom: '0.25rem' }}>
                        {feature.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                      </li>
                    ))}
                  </ul>
                </details>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h2>How It Works</h2>

        <div style={{ marginBottom: '2rem' }}>
          <h3>Standard Prediction</h3>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            Analyzes grade distribution patterns from historical data to predict expected GPA.
          </p>
          <ol style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#555' }}>
            <li>
              <strong>Data Collection:</strong> Collects grade distributions from BerkleyTime for 35 courses
              (18 CS + 12 DATA + 6 EECS courses with complete data)
            </li>
            <li>
              <strong>Pattern Analysis:</strong> Examines how grades are distributed (entropy, skewness, percentage of A-range grades)
            </li>
            <li>
              <strong>Prediction:</strong> Uses these patterns to estimate the expected GPA for any course
            </li>
            <li>
              <strong>Letter Grade:</strong> Converts the predicted GPA to the most probable letter grade
            </li>
          </ol>
        </div>

        <div style={{ marginBottom: '2rem', padding: '1.5rem', backgroundColor: '#f0f7ff', borderRadius: '8px', border: '2px solid #003262' }}>
          <h3 style={{ marginTop: 0, color: '#003262' }}>Personalized Prediction with Kalman Filter</h3>
          <p style={{ color: '#555', marginBottom: '1rem' }}>
            For personalized predictions, we use a <strong>Kalman filter</strong> - a mathematical technique
            that estimates your likely performance based on your past grades.
          </p>

          <h4 style={{ color: '#003262', fontSize: '1.05rem', marginTop: '1.5rem' }}>How the Kalman Filter Works:</h4>
          <ol style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#555' }}>
            <li>
              <strong>Initialization:</strong> Starts with your overall GPA compared to the typical average (3.3)
              as an initial estimate of your "ability offset"
            </li>
            <li>
              <strong>Sequential Processing:</strong> For each prior course you took:
              <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                <li>Converts your letter grade (A+, A, A-, B+, etc.) to GPA using Berkeley's standard scale</li>
                <li>Looks up the course's average GPA from our database</li>
                <li>Calculates how you performed relative to that average (e.g., +0.3 or -0.2)</li>
                <li>Updates the estimate of your typical performance using statistical methods</li>
                <li>Balances new evidence with previous estimate using optimal Kalman gain</li>
              </ul>
            </li>
            <li>
              <strong>Uncertainty Quantification:</strong> The filter tracks both your estimated ability
              and the uncertainty in that estimate, which decreases as more courses are processed
            </li>
            <li>
              <strong>Final Adjustment:</strong> The final ability estimate is applied to the target course's
              base difficulty to produce your personalized prediction
            </li>
          </ol>

          <h4 style={{ color: '#003262', fontSize: '1.05rem', marginTop: '1.5rem' }}>Why Use This Method?</h4>
          <ul style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#555' }}>
            <li>
              <strong>Proven Accuracy:</strong> Uses a well-established mathematical technique
              that's been proven to give the best possible estimates
            </li>
            <li>
              <strong>Learns from Each Course:</strong> Processes your grades one course at a time,
              getting better with more information
            </li>
            <li>
              <strong>Handles Uncertainty:</strong> Tracks how confident the prediction is and becomes
              more certain as more courses are included
            </li>
            <li>
              <strong>Accounts for Differences:</strong> Considers that different professors and courses
              have natural grade variations
            </li>
            <li>
              <strong>Easy to Understand:</strong> Each step has clear meaning: "Given this new grade,
              how should I update my estimate of your ability?"
            </li>
          </ul>

          <h4 style={{ color: '#003262', fontSize: '1.05rem', marginTop: '1.5rem' }}>Example:</h4>
          <div style={{ padding: '1rem', backgroundColor: 'white', borderRadius: '4px', marginTop: '0.75rem', fontFamily: 'monospace', fontSize: '0.9rem' }}>
            <strong>Prior Courses:</strong>
            <ul style={{ marginTop: '0.5rem', marginBottom: '0.5rem', lineHeight: 1.6 }}>
              <li>COMPSCI 61A: You got A- (3.7 GPA), average was 3.2 → +0.5 offset</li>
              <li>DATA C8: You got B+ (3.3 GPA), average was 3.3 → +0.0 offset</li>
              <li>COMPSCI 70: You got B+ (3.3 GPA), average was 3.2 → +0.1 offset</li>
            </ul>
            <strong>Kalman Filter Estimate:</strong> +0.22 ability offset (weighted average with optimal gains)<br/>
            <strong>Target Course (CS 170):</strong> Base difficulty 3.35<br/>
            <strong>Your Prediction:</strong> 3.35 + 0.22 = 3.57 GPA
          </div>
        </div>

        <div style={{ marginTop: '2rem', padding: '1.5rem', backgroundColor: '#fff3cd', borderRadius: '8px', border: '1px solid #ffc107' }}>
          <h3 style={{ marginTop: 0, color: '#856404' }}>Additional Context Analysis</h3>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            When you provide additional notes about your circumstances, the system analyzes this text
            to extract relevant factors that might affect your performance.
          </p>

          <h4 style={{ color: '#856404', fontSize: '1.05rem', marginTop: '1.5rem' }}>How Context Analysis Works:</h4>
          <ol style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#555' }}>
            <li>
              <strong>Text Processing:</strong> Your notes are sent to a third-party text analysis service (Groq)
            </li>
            <li>
              <strong>Context Extraction:</strong> The system identifies factors like:
              <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                <li>Health status (positive, negative, or neutral impact)</li>
                <li>External commitments (work hours, family obligations)</li>
                <li>Motivation level (high, moderate, or low)</li>
                <li>Prior experience in related topics</li>
                <li>Available support resources</li>
              </ul>
            </li>
            <li>
              <strong>Adjustment Calculation:</strong> Based on these factors, calculates a small
              confidence adjustment (-0.2 to +0.2 GPA)
            </li>
            <li>
              <strong>Conservative Application:</strong> The adjustment is intentionally small to avoid
              over-relying on subjective information
            </li>
            <li>
              <strong>Final Prediction:</strong> Combines the base prediction, Kalman filter adjustment,
              and context adjustment
            </li>
          </ol>

          <h4 style={{ color: '#856404', fontSize: '1.05rem', marginTop: '1.5rem' }}>Why Use Context Analysis?</h4>
          <ul style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#555' }}>
            <li>
              <strong>Holistic View:</strong> Grades alone don't capture your full situation (work, health, motivation)
            </li>
            <li>
              <strong>Free Service:</strong> Uses Groq's free API (14,400 requests/day, ultra-fast processing)
            </li>
            <li>
              <strong>Open Source:</strong> Powered by Meta's Llama 3.1 8B open-source language technology
            </li>
            <li>
              <strong>Privacy Aware:</strong> Notes are processed instantly and not stored by either our system or Groq
            </li>
            <li>
              <strong>Optional:</strong> You can skip this field entirely - predictions work without it
            </li>
          </ul>

          <div style={{
            marginTop: '1rem',
            padding: '0.75rem',
            backgroundColor: 'white',
            border: '1px solid #ffc107',
            borderRadius: '4px',
            fontSize: '0.9rem'
          }}>
            <strong>⚠️ Privacy Notice:</strong> Your notes are sent to Groq (a third-party service) for processing.
            While Groq doesn't store data long-term, avoid including highly sensitive or identifying information.
            This field is completely optional.
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Important Disclaimers</h2>
        <div style={{ padding: '1rem', backgroundColor: '#fff3cd', borderRadius: '4px', border: '1px solid #ffc107' }}>
          <ul style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#856404' }}>
            <li>
              <strong>Predictions Are Not Guarantees:</strong> These are statistical estimates based on historical data.
              Your actual grade will depend on your effort, teaching quality, and many other factors.
            </li>
            <li>
              <strong>Many Unmeasured Factors:</strong> Your actual performance depends on teaching quality, your effort,
              personal circumstances, and many other factors we cannot measure.
            </li>
            <li>
              <strong>Limited Training Data:</strong> Predictions are based on 35 courses (with complete grade distribution data). Results may be less
              accurate for edge cases or courses with unique characteristics.
            </li>
            <li>
              <strong>Simple Adjustments:</strong> Personalized predictions use simple statistical adjustments (±0.3 GPA),
              not comprehensive performance evaluation.
            </li>
            <li>
              <strong>Privacy Note:</strong> If you use the "Additional Context" field, your notes are sent to a
              third-party service (Groq) for analysis. No personal data is stored in our database.
            </li>
          </ul>
        </div>
      </div>

      <div className="card">
        <h2>About the Predictions</h2>
        <p style={{ color: '#666', marginBottom: '1rem' }}>
          This tool analyzes historical grade data from UC Berkeley courses to help you understand
          what grade you might expect. The predictions are based on:
        </p>
        <ul style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#555' }}>
          <li>Grade patterns from 35 courses (93% accuracy on average)</li>
          <li>Assignment weights for 8 courses with detailed breakdown</li>
          <li>Your past performance in related courses (for personalized predictions)</li>
          <li>Your personal circumstances and context (if you choose to share)</li>
        </ul>
        <p style={{ color: '#666', marginTop: '1rem' }}>
          All methods are transparent and based on established statistical techniques.
        </p>
      </div>
    </div>
  );
};

export default AboutPage;
