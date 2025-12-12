import { api } from './client';

export interface StudySession {
    id: string;
    user_id: string;
    exam_id: string;
    started_at: string;
    ended_at?: string;
    pomodoro_duration_minutes: number;
    pomodoros_completed: number;
    is_active: boolean;
}

export interface ReviewItem {
    id: string;
    topic_id: string;
    question: string;
    answer: string;
    review_type: 'flashcard' | 'question';
    difficulty: number;
    stability: number;
    state: 'new' | 'learning' | 'review' | 'relearning';
}

export interface ReviewStats {
    total_reviews: number;
    reviews_due: number;
    success_rate: number;
    streak_days: number;
}

export interface IntervalsPreview {
    again: number;
    hard: number;
    good: number;
    easy: number;
}

export const studyApi = {
    startSession: async (examId: string, durationMinutes: number = 25) => {
        const response = await api.post<StudySession>('/sessions/', {
            exam_id: examId,
            duration_minutes: durationMinutes,
        });
        return response.data;
    },

    endSession: async (sessionId: string) => {
        const response = await api.post<StudySession>(`/sessions/${sessionId}/end`);
        return response.data;
    },

    completePomodoro: async (sessionId: string) => {
        const response = await api.post<StudySession>(`/sessions/${sessionId}/pomodoro`);
        return response.data;
    },

    getDueReviews: async (limit: number = 20, examId?: string, topicId?: string) => {
        const response = await api.get<ReviewItem[]>('/reviews/due', {
            params: {
                limit,
                exam_id: examId,
                topic_id: topicId
            },
        });
        return response.data;
    },

    submitReview: async (reviewId: string, quality: number) => {
        const response = await api.post(`/reviews/${reviewId}/submit`, {
            quality,
        });
        return response.data;
    },

    getIntervalsPreview: async (reviewId: string) => {
        const response = await api.get<IntervalsPreview>(`/reviews/${reviewId}/intervals`);
        return response.data;
    },

    getStats: async () => {
        const response = await api.get<ReviewStats>('/reviews/stats');
        return response.data;
    },
};
