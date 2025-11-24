import { api } from './client';
import { User } from './auth';

export interface UserUpdateRequest {
    full_name?: string;
    preferred_language?: string;
    timezone?: string;
    daily_study_goal_minutes?: number;
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
        await api.post('/users/change-password', data);
    },

    deleteAccount: async (): Promise<void> => {
        await api.delete('/users/me');
    },
};
