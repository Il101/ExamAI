import { api } from './client';

export interface Topic {
    id: string;
    exam_id: string;
    topic_name: string;
    content?: string;
    content_blocknote?: any;
    content_markdown_backup?: string;
    flashcard_count?: number;
    status: 'pending' | 'generating' | 'ready' | 'failed';
    order_index: number;
    difficulty_level?: number;
    estimated_study_minutes?: number;
    created_at: string;
    updated_at: string;
    is_viewed?: boolean;
    quiz_completed?: boolean;
    last_viewed_at?: string;
}

export interface QuizOption {
    id: number;
    text: string;
    is_correct: boolean;
}

export interface QuizQuestion {
    id: number;
    question: string;
    options: QuizOption[];
    explanation: string;
}

export interface QuizData {
    topic_id: string;
    topic_name: string;
    questions: QuizQuestion[];
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

    getQuiz: async (topicId: string, numQuestions: number = 5): Promise<QuizData> => {
        const response = await api.get(`/topics/${topicId}/quiz`, {
            params: { num_questions: numQuestions },
        });
        return response.data;
    },

    updateTopicContent: async (
        topicId: string,
        contentBlocknote: any,
        contentMarkdown: string
    ): Promise<Topic> => {
        const response = await api.put(`/topics/${topicId}/content`, {
            content_blocknote: contentBlocknote,
            content_markdown: contentMarkdown,
        });
        return response.data;
    },

    submitQuizResult: async (
        topicId: string,
        questionsCorrect: number,
        questionsTotal: number
    ): Promise<void> => {
        await api.post('/quiz-results/', {
            topic_id: topicId,
            questions_correct: questionsCorrect,
            questions_total: questionsTotal,
        });
    },

    markAsViewed: async (
        topicId: string,
        examId: string,
        quizCompleted: boolean = false
    ): Promise<void> => {
        await api.post(`/topics/${topicId}/view`, null, {
            params: {
                exam_id: examId,
                quiz_completed: quizCompleted,
            },
        });
    },
};
