import { api } from './client';

export interface AdminUser {
    id: string;
    email: string;
    full_name: string;
    role: string;
    subscription_plan: string;
    is_verified: boolean;
    created_at: string;
    last_login: string | null;
}

export interface UserListResponse {
    users: AdminUser[];
    total: number;
    skip: number;
    limit: number;
}

export interface AdminUserUpdate {
    role?: string;
    subscription_plan?: string;
    is_verified?: boolean;
}

export interface SystemStatistics {
    total_users: number;
    total_exams: number;
    total_topics: number;
    total_reviews: number;
    active_users_last_7_days: number;
    active_users_last_30_days: number;
    users_by_plan: Record<string, number>;
    users_by_role: Record<string, number>;
}

export interface AdminExam {
    id: string;
    user_id: string;
    user_email: string;
    title: string;
    subject: string;
    status: string;
    created_at: string;
    topic_count: number;
}

export interface ExamListResponse {
    exams: AdminExam[];
    total: number;
    skip: number;
    limit: number;
}

export const adminApi = {
    getUsers: async (skip: number = 0, limit: number = 50): Promise<UserListResponse> => {
        const response = await api.get<UserListResponse>(`/admin/users?skip=${skip}&limit=${limit}`);
        return response.data;
    },

    getUser: async (userId: string): Promise<AdminUser> => {
        const response = await api.get<AdminUser>(`/admin/users/${userId}`);
        return response.data;
    },

    updateUser: async (userId: string, data: AdminUserUpdate): Promise<AdminUser> => {
        const response = await api.patch<AdminUser>(`/admin/users/${userId}`, data);
        return response.data;
    },

    deleteUser: async (userId: string): Promise<void> => {
        await api.delete(`/admin/users/${userId}`);
    },

    getStatistics: async (): Promise<SystemStatistics> => {
        const response = await api.get<SystemStatistics>('/admin/statistics');
        return response.data;
    },

    getExams: async (skip: number = 0, limit: number = 50): Promise<ExamListResponse> => {
        const response = await api.get<ExamListResponse>(`/admin/exams?skip=${skip}&limit=${limit}`);
        return response.data;
    },
};
