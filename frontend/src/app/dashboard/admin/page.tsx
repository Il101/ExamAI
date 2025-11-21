'use client';

import { useEffect, useState } from 'react';
import { adminApi, SystemStatistics } from '@/lib/api/admin';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Users, FileText, BookOpen, Activity } from 'lucide-react';
import { toast } from 'sonner';

export default function AdminDashboardPage() {
    const [stats, setStats] = useState<SystemStatistics | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await adminApi.getStatistics();
                setStats(data);
            } catch (err: unknown) {
                console.error('Failed to fetch statistics:', err);
                const status = err instanceof Error && 'response' in err
                    ? (err as { response?: { status?: number } }).response?.status
                    : undefined;

                if (status === 403) {
                    toast.error('Admin access required');
                } else {
                    toast.error('Failed to load statistics');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, []);

    if (loading) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (!stats) {
        return (
            <div className="container max-w-7xl py-8">
                <Card>
                    <CardHeader>
                        <CardTitle>Access Denied</CardTitle>
                        <CardDescription>You don&apos;t have permission to access this page.</CardDescription>
                    </CardHeader>
                </Card>
            </div>
        );
    }

    return (
        <div className="container max-w-7xl py-8 space-y-8">
            <div>
                <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
                <p className="text-muted-foreground">System overview and statistics</p>
            </div>

            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Users</CardTitle>
                        <Users className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.total_users}</div>
                        <p className="text-xs text-muted-foreground">
                            {stats.active_users_last_7_days} active (7d)
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Exams</CardTitle>
                        <FileText className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.total_exams}</div>
                        <p className="text-xs text-muted-foreground">{stats.total_topics} topics</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Reviews</CardTitle>
                        <BookOpen className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.total_reviews}</div>
                        <p className="text-xs text-muted-foreground">Study sessions</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.active_users_last_30_days}</div>
                        <p className="text-xs text-muted-foreground">Last 30 days</p>
                    </CardContent>
                </Card>
            </div>

            {/* Users by Plan */}
            <Card>
                <CardHeader>
                    <CardTitle>Users by Subscription Plan</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        {Object.entries(stats.users_by_plan).map(([plan, count]) => (
                            <div key={plan} className="flex items-center justify-between">
                                <span className="capitalize">{plan}</span>
                                <span className="font-semibold">{count}</span>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Users by Role */}
            <Card>
                <CardHeader>
                    <CardTitle>Users by Role</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        {Object.entries(stats.users_by_role).map(([role, count]) => (
                            <div key={role} className="flex items-center justify-between">
                                <span className="capitalize">{role}</span>
                                <span className="font-semibold">{count}</span>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
