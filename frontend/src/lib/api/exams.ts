import { api } from './client';

export interface CreateExamRequest {
  title: string;
  subject: string;
  exam_type: 'oral' | 'written' | 'test';
  level: 'school' | 'bachelor' | 'master' | 'phd';
  original_content: string;
}

export interface Exam {
  id: string;
  title: string;
  description: string;
  subject?: string;
  exam_type?: 'oral' | 'written' | 'test';
  level?: 'school' | 'bachelor' | 'master' | 'phd';
  status: 'draft' | 'planned' | 'generating' | 'ready' | 'failed';
  topic_count: number;
  created_at: string;
  updated_at: string;
  user_id: string;
  ai_summary?: string;
  plan_data?: {
    blocks: Array<{
      block_title: string;
      topics: Array<{
        id: string;
        title: string;
        description: string;
        estimated_paragraphs: number;
      }>;
    }>;
    total_blocks: number;
    total_topics: number;
  };
}

export interface ExamWithTopics extends Exam {
  topics: Array<{
    id: string;
    topic_name: string;
    content: string;
    status: 'pending' | 'generating' | 'ready' | 'failed';
    order_index: number;
    difficulty_level: number;
    estimated_study_minutes: number;
  }>;
  // Progress tracking (from status endpoint)
  progress?: number;
  message?: string;
  current_step?: string;
}


export interface ExamListResponse {
  exams: Exam[];
  total: number;
  limit: number;
  offset: number;
}

export const examsApi = {
  create: async (data: FormData) => {
    // Increase timeout to 120s for AI plan generation
    const response = await api.post('/exams/v3', data, {
      timeout: 120000,
    });
    return response.data;
  },

  list: async (params?: { skip?: number; limit?: number }): Promise<ExamListResponse> => {
    const response = await api.get('/exams/', { params });
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

  createPlan: async (examId: string) => {
    const response = await api.post(`/exams/${examId}/plan`);
    return response.data;
  },

  getTaskStatus: async (taskId: string) => {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },

  getGenerationStatus: async (examId: string) => {
    const response = await api.get(`/exams/${examId}/status`);
    return response.data;
  },
};

export interface GenerationStatusResponse {
  status: string;
  progress: number;
  message: string;
  current_step: string;
  steps_completed: number;
  total_steps: number;
}
