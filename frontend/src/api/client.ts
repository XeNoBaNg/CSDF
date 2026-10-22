/**
 * Axios API client configuration with error interceptor and timeout defaults.
 */

import axios, { AxiosError } from 'axios';
import type { ApiErrorResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Response interceptor for consistent error extraction
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorResponse>) => {
    if (error.response?.data?.error) {
      console.warn(
        `[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}:`,
        error.response.data.error.message
      );
    } else {
      console.error(
        `[Network Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}:`,
        error.message
      );
    }
    return Promise.reject(error);
  }
);
