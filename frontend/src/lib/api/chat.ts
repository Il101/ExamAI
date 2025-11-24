import { api } from './client';

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    created_at: string;
}

export const chatApi = {
    /**
     * Send a message to the AI tutor
     */
    sendMessage: async (topicId: string, message: string): Promise<ChatMessage> => {
        const response = await api.post(`/chat/topics/${topicId}/messages`, {
            message,
        });
        return response.data;
    },

    /**
     * Get chat history for a topic
     */
    getHistory: async (topicId: string, limit: number = 50): Promise<ChatMessage[]> => {
        const response = await api.get(`/chat/topics/${topicId}/messages`, {
            params: { limit },
        });
        return response.data;
    },

    /**
     * Clear chat history for a topic
     */
    clearHistory: async (topicId: string): Promise<void> => {
        await api.delete(`/chat/topics/${topicId}/messages`);
    },
};

