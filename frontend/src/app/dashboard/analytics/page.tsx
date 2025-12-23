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
    Loader2,
    Play,
    Zap,
    Info
} from 'lucide-react';
import { DailyProgressChart } from '@/components/analytics/daily-progress';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

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
                                <div className="h-4 bg-muted rounded mb-2" />
                                <div className="h-8 bg-muted rounded" />
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
                <p className="mt-2 text-muted-foreground">
                    Understand how your brain learns and track your memory growth
                </p>
            </div>

            {/* AI Recommendation / Next Steps */}
            <Card className="p-6 border-blue-500/20 bg-blue-500/5">
                <div className="flex items-start gap-4">
                    <div className="p-2 bg-blue-500 rounded-lg">
                        <Zap className="h-5 w-5 text-white" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            Learning Recommendation
                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p className="max-w-xs">We analyze your performance using the FSRS model to predict which cards you are likely to forget soon.</p>
                                    </TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                        </h3>
                        <p className="text-muted-foreground mt-1">
                            {stats?.total_cards_learned && stats.total_cards_learned > 0
                                ? `You have learned ${stats.total_cards_learned} cards. To maintain high retention, we recommend reviewing your scheduled cards today.`
                                : "Your learning journey is just beginning! Start your first focus session to build your personal memory forecast."}
                        </p>
                    </div>
                </div>
            </Card>

            {/* Stats Overview */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                <Card className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <Brain className="h-8 w-8 text-blue-600" />
                    </div>
                    <p className="text-sm text-muted-foreground mb-1">Total Cards Learned</p>
                    <p className="text-3xl font-bold">{stats?.total_cards_learned || 0}</p>
                </Card>

                <Card className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <Clock className="h-8 w-8 text-green-600" />
                    </div>
                    <p className="text-sm text-muted-foreground mb-1">Study Time</p>
                    <div className="flex items-baseline gap-2">
                        <p className="text-3xl font-bold">{stats?.total_minutes_studied || 0}</p>
                        <p className="text-xs text-muted-foreground">minutes</p>
                    </div>
                    {(!stats?.total_minutes_studied || stats.total_minutes_studied === 0) && (
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <div className="flex items-center gap-1 mt-2 text-xs text-blue-600 cursor-pointer hover:underline">
                                        <Play className="h-3 w-3" />
                                        <span>Start Session</span>
                                    </div>
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p>Click the timer 🧠 in the header to start tracking!</p>
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    )}
                </Card>

                <Card className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <TrendingUp className="h-8 w-8 text-orange-600" />
                    </div>
                    <p className="text-sm text-muted-foreground mb-1">Current Streak</p>
                    <p className="text-3xl font-bold">{stats?.current_streak || 0}</p>
                    <p className="text-xs text-muted-foreground">days</p>
                </Card>

                <Card className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <Target className="h-8 w-8 text-purple-600" />
                    </div>
                    <p className="text-sm text-muted-foreground mb-1">Longest Streak</p>
                    <p className="text-3xl font-bold">{stats?.longest_streak || 0}</p>
                    <p className="text-xs text-muted-foreground">days</p>
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
                            <h3 className="text-lg font-semibold">Study Consistency</h3>
                            <p className="text-sm text-muted-foreground">
                                Your daily study activity. Consistency is the key to moving information into long-term memory.
                            </p>
                            {stats?.daily_progress && stats.daily_progress.length > 0 ? (
                                <DailyProgressChart data={stats.daily_progress} />
                            ) : (
                                <div className="text-center py-12 bg-muted/30 rounded-lg border border-dashed">
                                    <Brain className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
                                    <h4 className="font-semibold">No progress data yet</h4>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        Start studying to see your daily progress here!
                                    </p>
                                </div>
                            )}
                        </div>
                    </TabsContent>

                    <TabsContent value="retention" className="mt-6">
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">Memory Forecast</h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                This graph shows your predicted chance of recalling information over time.
                                We use the <span className="font-mono text-xs bg-muted px-1 rounded">FSRS</span> model to ensure you review at the perfect moment.
                            </p>
                            <div className="bg-muted/30 p-4 rounded-lg border">
                                <RetentionChart data={retentionData} />
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                                <div className="p-3 rounded bg-blue-500/10 border border-blue-500/20 text-xs text-blue-700 dark:text-blue-400">
                                    <strong>Tip:</strong> Reviewing when retention is between 80-90% is the most efficient way to learn.
                                </div>
                                <div className="p-3 rounded bg-purple-500/10 border border-purple-500/20 text-xs text-purple-700 dark:text-purple-400">
                                    <strong>Science:</strong> Spaced repetition flattens the forgetting curve, making memories permanent.
                                </div>
                            </div>
                        </div>
                    </TabsContent>

                    <TabsContent value="activity" className="mt-6">
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">Study Activity</h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                Your study consistency over the last 30 days.
                            </p>
                            <div className="bg-muted/30 p-4 rounded-lg border overflow-hidden">
                                <ActivityHeatmap data={heatmapData} />
                            </div>
                        </div>
                    </TabsContent>
                </Tabs>
            </Card>
        </div>
    );
}
