'use client';

import { useState } from 'react';
import { useAnalytics } from '@/lib/hooks/use-analytics';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { MemoryHealthScore } from '@/components/analytics/memory-health-score';
import { TodayInsight } from '@/components/analytics/today-insight';
import { QuickStats } from '@/components/analytics/quick-stats';
import { ActivityHeatmap } from '@/components/analytics/activity-heatmap';
import { RetentionChart } from '@/components/analytics/retention-chart';
import { DailyProgressChart } from '@/components/analytics/daily-progress';
import {
    ChevronDown,
    ChevronUp,
    BarChart3,
    Brain,
    Info,
    Settings2,
    TrendingUp
} from 'lucide-react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';

export default function AnalyticsPage() {
    const { stats, isLoading } = useAnalytics();
    const [showDetails, setShowDetails] = useState(false);

    if (isLoading) {
        return (
            <div className="space-y-8 animate-pulse">
                <div className="h-10 bg-muted rounded w-1/4" />
                <div className="grid gap-8 md:grid-cols-2">
                    <div className="h-64 bg-muted rounded-xl" />
                    <div className="h-64 bg-muted rounded-xl" />
                </div>
            </div>
        );
    }

    // Calculate a mock Memory Health score based on retention and streak
    // In a real app, this would come from the backend or a more complex FE logic
    const baseHealth = stats?.retention_curve?.[0]?.retention_rate
        ? Math.round(stats.retention_curve[0].retention_rate * 100)
        : 85;
    const healthScore = Math.min(100, baseHealth + (stats?.current_streak || 0));

    return (
        <div className="max-w-5xl mx-auto space-y-10 pb-20">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-black text-foreground tracking-tight">Your Progress</h1>
                    <p className="mt-2 text-muted-foreground font-medium">
                        Real-time visualization of your learning journey
                    </p>
                </div>
                <div className="flex items-center gap-6">
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button variant="outline" size="icon" className="rounded-full">
                                    <Settings2 className="h-4 w-4" />
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                                <p>Analytics Settings</p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                </div>
            </div>

            {/* Hero Section: Health & Insights */}
            <div className="grid gap-8 md:grid-cols-5 items-stretch">
                <Card className="md:col-span-2 flex flex-col items-center justify-center bg-card border-none shadow-sm pb-8">
                    <MemoryHealthScore score={healthScore} isLoading={isLoading} />
                </Card>

                <div className="md:col-span-3 flex flex-col gap-8">
                    <TodayInsight
                        streak={stats?.current_streak}
                        totalLearned={stats?.total_cards_learned}
                        isLoading={isLoading}
                    />
                    <QuickStats
                        streak={stats?.current_streak || 0}
                        totalLearned={stats?.total_cards_learned || 0}
                        isLoading={isLoading}
                    />
                </div>
            </div>

            {/* Activity Section */}
            <section className="space-y-4">
                <div className="flex items-center justify-between px-2">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <BarChart3 className="h-5 w-5 text-blue-500" />
                        Study Consistency
                    </h2>
                    <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest">
                        Last 12 Weeks
                    </span>
                </div>
                <Card className="p-8 border-none shadow-sm bg-card/50 overflow-hidden">
                    <ActivityHeatmap data={stats?.activity_heatmap || []} />
                </Card>
            </section>

            {/* Detailed Stats Toggle */}
            <div className="pt-4 flex flex-col items-center">
                <Button
                    variant="ghost"
                    onClick={() => setShowDetails(!showDetails)}
                    className="group text-muted-foreground hover:text-foreground transition-all rounded-full px-8 py-6 border border-border/50 hover:border-border"
                >
                    <div className="flex flex-col items-center gap-1">
                        <span className="text-sm font-semibold">
                            {showDetails ? "Hide Deep Analytics" : "Show Deep Analytics"}
                        </span>
                        {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4 group-hover:translate-y-1 transition-transform" />}
                    </div>
                </Button>

                {showDetails && (
                    <div className="w-full mt-10 space-y-10 animate-in fade-in slide-in-from-top-4 duration-500">
                        {/* Daily Progress */}
                        <Card className="p-8 border-none shadow-sm bg-card/30">
                            <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
                                <TrendingUp className="h-5 w-5 text-green-500" />
                                Memory Growth Rate
                            </h3>
                            <DailyProgressChart data={stats?.daily_progress || []} />
                        </Card>

                        {/* Retention Curve */}
                        <Card className="p-8 border-none shadow-sm bg-card/30">
                            <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                                <Brain className="h-5 w-5 text-purple-500" />
                                Retention Forecast
                            </h3>
                            <p className="text-sm text-muted-foreground mb-8">
                                Predicted probability of remembering information over the next 30 days.
                            </p>
                            <RetentionChart data={stats?.retention_curve || []} />
                        </Card>

                        {/* FSRS Info (Simplified) */}
                        <div className="bg-blue-500/5 border border-blue-500/10 rounded-2xl p-6 flex items-start gap-4">
                            <Info className="h-6 w-6 text-blue-500 mt-1 shrink-0" />
                            <div>
                                <h4 className="font-bold text-blue-700 dark:text-blue-400">Advanced Learning Model</h4>
                                <p className="text-sm text-blue-600/80 dark:text-blue-400/80 mt-1">
                                    Your learning is powered by the FSRS algorithm, which optimizes review intervals based on your unique memory performance.
                                </p>
                                <Button variant="link" asChild className="p-0 h-auto mt-2 text-blue-700 dark:text-blue-400 font-bold underline decoration-2 underline-offset-4">
                                    <a href="/dashboard/review-queue">View Technical Data →</a>
                                </Button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

