import { api } from './client';

export interface DailyProgress {
    date: string;
    cards_reviewed: number;
    cards_learned: number;
    minutes_studied: number;
}

export interface RetentionPoint {
    days_since_review: number;
    retention_rate: number;
}

export interface HeatmapPoint {
    date: string;
    count: number;
    level: number;
}

export interface AnalyticsResponse {
    daily_progress: DailyProgress[];
    retention_curve: RetentionPoint[];
    activity_heatmap: HeatmapPoint[];
    total_cards_learned: number;
    total_minutes_studied: number;
    current_streak: number;
    longest_streak: number;
}

export const analyticsApi = {
    getDashboardStats: async () => {
        const response = await api.get<AnalyticsResponse>('/analytics/dashboard');
        return response.data;
    },
};
