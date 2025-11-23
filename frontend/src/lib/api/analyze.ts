import { api } from './client';

export interface TopicOutline {
    subject: string;
    total_topics: number;
    outline: Array<{
        topic: string;
        subtopics: string[];
    }>;
    message?: string;
}

export const analyzeApi = {
    analyzeContent: async (file: File, subject?: string): Promise<TopicOutline> => {
        const formData = new FormData();
        formData.append('file', file);
        if (subject) {
            formData.append('subject', subject);
        }

        const response = await api.post('/analyze/content', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });

        return response.data;
    },
};
