import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    // Check if we are in the browser
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      console.log('Interceptor: token from localStorage:', token ? 'EXISTS' : 'NULL');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log('Interceptor: Authorization header set');
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle network errors (backend not running)
    if (!error.response) {
      const networkError = new Error(
        'Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен на порту 8000.'
      );
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (networkError as any).isNetworkError = true;
      return Promise.reject(networkError);
    }

    // Handle 401 Unauthorized (token expired)
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Here we would handle token refresh logic
      // For now, just redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);
