import axios from 'axios';

export interface TopicOutline {
    subject: string;
    total_topics: number;
    outline: Array<{
        topic: string;
        subtopics: string[];
    }>;
    message?: string;
}

// Create a separate axios instance for public endpoints (no auth required)
const getBaseUrl = () => {
    let url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    if (url.includes('railway.app') && url.startsWith('http://')) {
        url = url.replace('http://', 'https://');
    }
    return url;
};

const publicApi = axios.create({
    baseURL: getBaseUrl(),
    headers: {
        'Content-Type': 'application/json',
    },
});

export const analyzeApi = {
    analyzeContent: async (file: File, subject?: string): Promise<TopicOutline> => {
        const formData = new FormData();
        formData.append('file', file);
        if (subject) {
            formData.append('subject', subject);
        }

        const response = await publicApi.post('/analyze/content', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });

        return response.data;
    },
};
