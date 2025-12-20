import { api } from './client';
import { User } from './auth';

export interface UserUpdateRequest {
    full_name?: string;
    preferred_language?: string;
    timezone?: string;
    daily_study_goal_minutes?: number;
    notification_exam_ready?: boolean;
    notification_study_reminders?: boolean;
    notification_product_updates?: boolean;
}

export interface ChangePasswordRequest {
    current_password: string;
    new_password: string;
}

export const usersApi = {
    updateProfile: async (data: UserUpdateRequest): Promise<User> => {
        const response = await api.patch<User>('/users/me', data);
        return response.data;
    },

    changePassword: async (data: ChangePasswordRequest): Promise<void> => {
        // Backend change password endpoint lives under /auth
        await api.post('/auth/change-password', data);
    },

    deleteAccount: async (): Promise<void> => {
        await api.delete('/users/me');
    },

    sendTestNotification: async (): Promise<{ message: string; subscription_count: number }> => {
        const response = await api.post<{ message: string; subscription_count: number }>('/push/test');
        return response.data;
    },
};
