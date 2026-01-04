/**
 * API client for communicating with the FastAPI backend
 */
import axios from 'axios';

// Use environment variable or default to local development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Add request interceptor for logging (development only)
if (import.meta.env.DEV) {
  api.interceptors.request.use(
    (config) => {
      console.log(`[API Request] ${config.method.toUpperCase()} ${config.url}`, config.data);
      return config;
    },
    (error) => {
      console.error('[API Request Error]', error);
      return Promise.reject(error);
    }
  );

  api.interceptors.response.use(
    (response) => {
      console.log(`[API Response] ${response.config.method.toUpperCase()} ${response.config.url}`, response.data);
      return response;
    },
    (error) => {
      console.error('[API Response Error]', error.response?.data || error.message);
      return Promise.reject(error);
    }
  );
}

/**
 * Course API endpoints
 */
export const courseAPI = {
  /**
   * Get all courses with optional filtering
   * @param {Object} params - Query parameters
   * @param {string} params.subject - Filter by subject (optional)
   * @param {number} params.limit - Max results (default: 50)
   * @param {number} params.offset - Pagination offset (default: 0)
   */
  getAllCourses: (params = {}) => api.get('/courses', { params }),

  /**
   * Get detailed information about a specific course
   * @param {number} courseId - Course ID
   */
  getCourse: (courseId) => api.get(`/courses/${courseId}`),

  /**
   * Predict GPA for a course
   * @param {number} courseId - Course ID
   * @param {string} modelType - Model type ('grade_distribution', 'full', or 'personalized')
   * @param {Object} userContext - Optional user context for personalized predictions
   */
  predict: (courseId, modelType = 'grade_distribution', userContext = null) => {
    const payload = {
      course_id: courseId,
      model_type: modelType,
    };

    // Add user_context only if provided and modelType is personalized
    if (userContext && modelType === 'personalized') {
      payload.user_context = userContext;
    }

    return api.post('/predict', payload);
  },

  /**
   * Batch predict GPA for multiple courses
   * @param {number[]} courseIds - Array of course IDs
   * @param {string} modelType - Model type
   */
  batchPredict: (courseIds, modelType = 'grade_distribution') =>
    api.post('/predict/batch', {
      course_ids: courseIds,
      model_type: modelType,
    }),

  /**
   * Get information about available models
   */
  getModels: () => api.get('/models'),

  /**
   * Health check
   */
  getHealth: () => api.get('/health'),
};

/**
 * Error handling helper
 * @param {Error} error - Axios error object
 * @returns {string} User-friendly error message
 */
export const handleAPIError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;

    if (status === 404) {
      return data.detail || 'Resource not found';
    } else if (status === 400) {
      return data.detail || 'Invalid request';
    } else if (status === 422) {
      // Validation error
      const validationErrors = data.detail || [];
      if (Array.isArray(validationErrors)) {
        return validationErrors.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
      }
      return 'Validation error';
    } else if (status === 500) {
      return 'Server error. Please try again later.';
    }

    return data.detail || `Error: ${status}`;
  } else if (error.request) {
    // Request made but no response received
    return 'Cannot connect to server. Please check your connection.';
  } else {
    // Error in request setup
    return error.message || 'An unexpected error occurred';
  }
};

export default api;
