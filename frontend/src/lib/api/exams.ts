import { api } from './client';

export interface CreateExamRequest {
  title: string;
  subject?: string;
  exam_type?: 'oral' | 'written' | 'test';
  level?: 'school' | 'bachelor' | 'master' | 'phd';
  original_content?: string;
  description?: string;
  file_path?: string; // For file uploads
}

export interface Exam {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  user_id: string;
}

export const examsApi = {
  create: async (data: CreateExamRequest) => {
    const response = await api.post('/exams', data);
    return response.data;
  },

  list: async (params?: { skip?: number; limit?: number }) => {
    const response = await api.get('/exams', { params });
    return response.data;
  },

  getById: async (examId: string) => {
    const response = await api.get(`/exams/${examId}`);
    return response.data;
  },

  delete: async (examId: string) => {
    await api.delete(`/exams/${examId}`);
  },

  startGeneration: async (examId: string) => {
    const response = await api.post(`/exams/${examId}/generate`);
    return response.data;
  },

  getTaskStatus: async (taskId: string) => {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },
};
