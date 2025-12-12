'use client';

import { useAnalytics } from '@/lib/hooks/use-analytics';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RetentionChart } from '@/components/analytics/retention-chart';
import { ActivityHeatmap } from '@/components/analytics/activity-heatmap';
import {
    TrendingUp,
    Calendar,
    Brain,
    Clock,
    Target,
    Loader2
} from 'lucide-react';

export default function AnalyticsPage() {
    const { stats, isLoading } = useAnalytics();

    if (isLoading) {
        return (
            <div className="space-y-6">
                <div className="animate-pulse">
                    <div className="h-8 bg-muted rounded w-1/3 mb-4" />
                    <div className="grid gap-6 md:grid-cols-4">
                        {[1, 2, 3, 4].map((i) => (
                            <Card key={i} className="p-6">
                                <div className="h-4 bg-gray-200 rounded mb-2" />
                                <div className="h-8 bg-gray-200 rounded" />
                            </Card>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    // Transform data for retention chart if empty (fallback for MVP)
    const retentionData = stats?.retention_curve || [
        { days_since_review: 1, retention_rate: 1.0 },
        { days_since_review: 3, retention_rate: 0.9 },
        { days_since_review: 7, retention_rate: 0.75 },
        { days_since_review: 14, retention_rate: 0.6 },
        { days_since_review: 30, retention_rate: 0.45 },
    ];

    // Transform data for heatmap if empty (fallback for MVP)
    const heatmapData = stats?.activity_heatmap || [];

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-foreground">Analytics</h1>
                <p className="mt-2 text-muted">
                    Track your learning progress and performance
                </p>
            </div>

            {/* Stats Overview */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                <Card className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <Brain className="h-8 w-8 text-blue-600" />
                    </div>
                    <p className="text-sm text-gray-600 mb-1">Total Cards Learned</p>
                    <p className="text-3xl font-bold">{stats?.total_cards_learned || 0}</p>
                </Card>

                <Card className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <Clock className="h-8 w-8 text-green-600" />
                    </div>
                    <p className="text-sm text-gray-600 mb-1">Study Time</p>
                    <p className="text-3xl font-bold">{stats?.total_minutes_studied || 0}</p>
                    <p className="text-xs text-gray-500">minutes</p>
                </Card>

                <Card className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <TrendingUp className="h-8 w-8 text-orange-600" />
                    </div>
                    <p className="text-sm text-gray-600 mb-1">Current Streak</p>
                    <p className="text-3xl font-bold">{stats?.current_streak || 0}</p>
                    <p className="text-xs text-gray-500">days</p>
                </Card>

                <Card className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <Target className="h-8 w-8 text-purple-600" />
                    </div>
                    <p className="text-sm text-gray-600 mb-1">Longest Streak</p>
                    <p className="text-3xl font-bold">{stats?.longest_streak || 0}</p>
                    <p className="text-xs text-gray-500">days</p>
                </Card>
            </div>

            {/* Detailed Analytics */}
            <Card className="p-6">
                <Tabs defaultValue="progress" className="w-full">
                    <TabsList>
                        <TabsTrigger value="progress">Daily Progress</TabsTrigger>
                        <TabsTrigger value="retention">Retention</TabsTrigger>
                        <TabsTrigger value="activity">Activity</TabsTrigger>
                    </TabsList>

                    <TabsContent value="progress" className="mt-6">
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">Daily Progress</h3>
                            {stats?.daily_progress && stats.daily_progress.length > 0 ? (
                                <div className="space-y-2">
                                    {stats.daily_progress.slice(0, 7).map((day, index) => (
                                        <div key={index} className="flex items-center justify-between p-3 bg-muted rounded">
                                            <div className="flex items-center gap-3">
                                                <Calendar className="h-4 w-4 text-muted-foreground" />
                                                <span className="text-sm font-medium">
                                                    {new Date(day.date).toLocaleDateString()}
                                                </span>
                                            </div>
                                            <div className="flex gap-6 text-sm">
                                                <span className="text-muted">
                                                    {day.cards_reviewed} cards
                                                </span>
                                                <span className="text-muted">
                                                    {day.minutes_studied} min
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-gray-500 text-center py-8">
                                    No progress data available yet. Start studying to see your progress!
                                </p>
                            )}
                        </div>
                    </TabsContent>

                    <TabsContent value="retention" className="mt-6">
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">Forgetting Curve</h3>
                            <p className="text-sm text-gray-500 mb-4">
                                Shows how your memory retention decays over time without review (based on FSRS model).
                            </p>
                            <div className="bg-white dark:bg-gray-900 p-4 rounded-lg border">
                                <RetentionChart data={retentionData} />
                            </div>
                        </div>
                    </TabsContent>

                    <TabsContent value="activity" className="mt-6">
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">Study Activity</h3>
                            <p className="text-sm text-gray-500 mb-4">
                                Your study consistency over the last 30 days.
                            </p>
                            <div className="bg-white dark:bg-gray-900 p-4 rounded-lg border overflow-hidden">
                                <ActivityHeatmap data={heatmapData} />
                            </div>
                        </div>
                    </TabsContent>
                </Tabs>
            </Card>
        </div>
    );
}
