import { api } from './client';
import { Exam } from './exams';

export interface Course {
    id: string;
    user_id: string;
    title: string;
    subject: string;
    description?: string;
    semester_start?: string;
    semester_end?: string;
    is_archived: boolean;
    created_at: string;
    updated_at: string;
    stats?: CourseStats;
}

export interface CourseStats {
    exam_count: number;
    topic_count: number;
    completed_topics: number;
    due_flashcards_count: number;
    total_actual_study_minutes: number;
    total_planned_study_minutes: number;
    average_difficulty: number;
    progress_percentage?: number;
}

export interface CourseCreateRequest {
    title: string;
    subject: string;
    description?: string;
    semester_start?: string;
    semester_end?: string;
}

export interface CourseUpdateRequest {
    title?: string;
    subject?: string;
    description?: string;
    semester_start?: string;
    semester_end?: string;
    is_archived?: boolean;
}

export interface CourseListResponse {
    items: Course[];
    total: number;
}

export const coursesApi = {
    list: async (params?: { limit?: number; offset?: number }): Promise<CourseListResponse> => {
        const response = await api.get('/courses/', { params });
        return response.data;
    },

    getById: async (id: string): Promise<Course> => {
        const response = await api.get(`/courses/${id}`);
        return response.data;
    },

    create: async (data: CourseCreateRequest): Promise<Course> => {
        const response = await api.post('/courses/', data);
        return response.data;
    },

    update: async (id: string, data: CourseUpdateRequest): Promise<Course> => {
        const response = await api.patch(`/courses/${id}`, data);
        return response.data;
    },

    delete: async (id: string): Promise<void> => {
        await api.delete(`/courses/${id}`);
    },

    listExams: async (courseId: string): Promise<Exam[]> => {
        const response = await api.get(`/courses/${courseId}/exams`);
        return response.data;
    },

    addExam: async (courseId: string, examId: string): Promise<void> => {
        await api.post(`/courses/${courseId}/exams/${examId}`);
    },

    removeExam: async (courseId: string, examId: string): Promise<void> => {
        await api.delete(`/courses/${courseId}/exams/${examId}`);
    },
};
