import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api/analytics';

export function useAnalytics() {
    const { data: dashboardData, isLoading } = useQuery({
        queryKey: ['analytics', 'dashboard'],
        queryFn: analyticsApi.getDashboardStats,
    });

    return {
        stats: dashboardData,
        isLoading,
    };
}
