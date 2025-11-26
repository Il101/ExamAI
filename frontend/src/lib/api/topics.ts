import { api } from './client';

export interface Topic {
    id: string;
    exam_id: string;
    topic_name: string;
    content: string;
    order_index: number;
    difficulty_level: number;
    estimated_study_minutes: number;
    created_at: string;
    updated_at: string;
}

export const topicsApi = {
    getByExamId: async (examId: string): Promise<Topic[]> => {
        const response = await api.get(`/topics`, {
            params: { exam_id: examId },
        });
        return response.data;
    },

    getById: async (topicId: string): Promise<Topic> => {
        const response = await api.get(`/topics/${topicId}`);
        return response.data;
    },
};
