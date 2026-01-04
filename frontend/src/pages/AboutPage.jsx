import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { courseAPI, handleAPIError } from '../services/api';

const AboutPage = () => {
  // Fetch model information
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
        <h2>About This Project</h2>
        <p style={{ marginBottom: '1rem' }}>
          This application predicts UC Berkeley course difficulty using machine learning models
          trained on historical grade distribution data from BerkleyTime.
        </p>
        <p>
          The predictions help students understand course difficulty before enrollment by analyzing
          patterns in grade distributions, grading structures, and other features.
        </p>
      </div>

      <div className="card">
        <h2>Dataset</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div className="feature-item">
            <div className="feature-label">Total Courses</div>
            <div className="feature-value">30</div>
          </div>
          <div className="feature-item">
            <div className="feature-label">Subjects Covered</div>
            <div className="feature-value">2</div>
          </div>
          <div className="feature-item">
            <div className="feature-label">Courses with Grading Data</div>
            <div className="feature-value">8</div>
          </div>
          <div className="feature-item">
            <div className="feature-label">Data Source</div>
            <div className="feature-value">BerkleyTime</div>
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Machine Learning Models</h2>

        {isLoading && (
          <div className="loading">
            <div className="spinner"></div>
          </div>
        )}

        {error && (
          <div className="error">
            Failed to load model information: {handleAPIError(error)}
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
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>Mean Absolute Error</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 600, color: '#003262' }}>
                      {model.mae?.toFixed(3) || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>R² Score</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 600, color: '#003262' }}>
                      {model.r2?.toFixed(3) || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>Features Used</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 600, color: '#003262' }}>
                      {model.num_features}
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '1rem' }}>
                  <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.5rem' }}>
                    Features:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {model.features_used.map((feature) => (
                      <span
                        key={feature}
                        style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: '#e8f4ff',
                          borderRadius: '12px',
                          fontSize: '0.85rem',
                          color: '#003262',
                        }}
                      >
                        {feature.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h2>How It Works</h2>
        <ol style={{ paddingLeft: '1.5rem', lineHeight: '1.8' }}>
          <li>
            <strong>Data Collection:</strong> Grade distributions and grading structures are collected
            from BerkleyTime API and course syllabi
          </li>
          <li>
            <strong>Feature Engineering:</strong> Features like grade entropy, skewness, percentage of
            A-range grades, and grading structure percentages are calculated
          </li>
          <li>
            <strong>Model Training:</strong> Ridge Regression and Random Forest models are trained
            using Leave-One-Out Cross-Validation
          </li>
          <li>
            <strong>Prediction:</strong> The trained models predict average GPA based on course features,
            with confidence intervals calculated using the model's MAE
          </li>
        </ol>
      </div>

      <div className="card">
        <h2>Privacy & Ethics</h2>
        <p style={{ marginBottom: '1.5rem', color: '#555' }}>
          We take privacy and ethical ML seriously. Here's how we protect your data and ensure responsible use:
        </p>

        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ color: '#003262', fontSize: '1.1rem', marginBottom: '0.75rem' }}>
            🔒 Privacy Safeguards for Personalized Predictions
          </h3>
          <div style={{
            padding: '1rem',
            backgroundColor: '#d4edda',
            border: '1px solid #28a745',
            borderRadius: '4px',
            marginBottom: '1rem'
          }}>
            <ul style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#155724', margin: 0 }}>
              <li><strong>No Data Storage:</strong> Your personal information (GPA, units, study hours) is NEVER stored in our database</li>
              <li><strong>No Logging:</strong> Request bodies containing personal data are not logged by the server</li>
              <li><strong>In-Memory Only:</strong> All processing happens in-memory and data is discarded after prediction</li>
              <li><strong>No Tracking:</strong> We don't use cookies, analytics, or tracking for personalized predictions</li>
              <li><strong>Read-Only Database:</strong> Our database only contains aggregated course data, never individual user information</li>
            </ul>
          </div>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ color: '#003262', fontSize: '1.1rem', marginBottom: '0.75rem' }}>
            ⚖️ Ethical Considerations
          </h3>
          <ul style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#555' }}>
            <li>
              <strong>Non-Deterministic Predictions:</strong> We provide probability distributions, not deterministic outcomes.
              No one can predict your exact grade with certainty.
            </li>
            <li>
              <strong>Coarse-Grained Features:</strong> We only use high-level academic indicators (GPA quartiles, workload bins)
              to avoid over-personalizing or creating false precision.
            </li>
            <li>
              <strong>No Protected Attributes:</strong> We do NOT collect or use demographics, disability status, race, gender,
              or other protected characteristics.
            </li>
            <li>
              <strong>Conservative Uncertainty:</strong> Our predictions include wide confidence intervals to acknowledge
              the many factors we can't measure (teaching quality, personal circumstances, etc.).
            </li>
            <li>
              <strong>Non-Gatekeeping Language:</strong> We avoid phrases like "you probably can't handle this course."
              Instead, we present probabilities and let you make informed decisions.
            </li>
          </ul>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ color: '#003262', fontSize: '1.1rem', marginBottom: '0.75rem' }}>
            ⚠️ Limitations & Disclaimers
          </h3>
          <div style={{
            padding: '1rem',
            backgroundColor: '#fff3cd',
            border: '1px solid #ffc107',
            borderRadius: '4px'
          }}>
            <ul style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#856404', margin: 0 }}>
              <li>
                <strong>Not a Guarantee:</strong> These predictions are statistical estimates based on historical patterns,
                not guarantees of individual outcomes.
              </li>
              <li>
                <strong>Many Unmeasured Factors:</strong> Your actual performance depends on teaching quality, your effort,
                personal circumstances, and many other factors we cannot measure.
              </li>
              <li>
                <strong>Limited Training Data:</strong> Models are trained on only 30 courses. Predictions may be less
                accurate for edge cases or courses with unique characteristics.
              </li>
              <li>
                <strong>Heuristic Adjustments:</strong> Personalized predictions use simple heuristic adjustments (±0.3 GPA),
                not a trained individual-level model.
              </li>
              <li>
                <strong>Use as One Input:</strong> Consider this alongside advisor recommendations, course reviews,
                and your own goals and interests.
              </li>
            </ul>
          </div>
        </div>

        <div>
          <h3 style={{ color: '#003262', fontSize: '1.1rem', marginBottom: '0.75rem' }}>
            ✅ Responsible Use Guidelines
          </h3>
          <ul style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#555' }}>
            <li>Use predictions as <strong>one data point</strong>, not the sole decision-making factor</li>
            <li>Don't let predictions discourage you from challenging courses you're interested in</li>
            <li>Remember that grade difficulty varies by instructor, semester, and your preparation</li>
            <li>Consult with academic advisors and peers before making enrollment decisions</li>
            <li>Focus on learning and growth, not just GPA optimization</li>
          </ul>
        </div>
      </div>

      <div className="card">
        <h2>Tech Stack</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Backend</h3>
            <ul style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#666' }}>
              <li>FastAPI</li>
              <li>scikit-learn</li>
              <li>SQLite</li>
              <li>Pydantic</li>
            </ul>
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Frontend</h3>
            <ul style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#666' }}>
              <li>React</li>
              <li>Vite</li>
              <li>React Query</li>
              <li>Axios</li>
            </ul>
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Deployment</h3>
            <ul style={{ paddingLeft: '1.5rem', lineHeight: '1.8', color: '#666' }}>
              <li>Docker</li>
              <li>Render.com</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;
