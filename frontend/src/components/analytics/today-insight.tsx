'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Zap, ArrowRight, Sparkles } from 'lucide-react';
import Link from 'next/link';

interface TodayInsightProps {
    cardsDue?: number;
    streak?: number;
    totalLearned?: number;
    isLoading?: boolean;
}

export function TodayInsight({ cardsDue = 0, streak = 0, totalLearned = 0, isLoading }: TodayInsightProps) {
    if (isLoading) {
        return (
            <Card className="p-6 animate-pulse bg-muted/50 border-none h-40" />
        );
    }

    const getRecommendation = () => {
        if (totalLearned === 0) {
            return {
                title: "Welcome aboard!",
                message: "Ready to build your long-term memory? Start by learning your first set of cards.",
                cta: "Learn First Cards",
                href: "/dashboard"
            };
        }
        if (cardsDue > 0) {
            return {
                title: "Peak Learning Moment",
                message: `You have ${cardsDue} cards due for review. Study them now to maximize retention!`,
                cta: "Start Review",
                href: "/dashboard/review-queue"
            };
        }
        if (streak > 0) {
            return {
                title: "Keep the Momentum!",
                message: `You're on a ${streak}-day streak. Even 5 minutes today will keep your memory sharp.`,
                cta: "Browse Exams",
                href: "/dashboard"
            };
        }
        return {
            title: "Great Job!",
            message: "All caught up! Why not explore some new topics to expand your knowledge?",
            cta: "Discover More",
            href: "/dashboard"
        };
    };

    const { title, message, cta, href } = getRecommendation();

    return (
        <Card className="p-6 border-blue-500/20 bg-gradient-to-br from-blue-500/10 to-purple-500/10 hover:shadow-lg transition-all duration-300">
            <div className="flex items-start gap-4">
                <div className="p-3 bg-blue-500 rounded-2xl shadow-lg shadow-blue-500/20">
                    <Sparkles className="h-6 w-6 text-white" />
                </div>
                <div className="flex-1">
                    <h3 className="text-xl font-bold text-foreground flex items-center gap-2">
                        {title}
                    </h3>
                    <p className="text-muted-foreground mt-2 leading-relaxed">
                        {message}
                    </p>
                    <div className="mt-6">
                        <Button asChild className="rounded-full px-6 bg-blue-600 hover:bg-blue-700 text-white group shadow-md hover:shadow-lg transition-all">
                            <Link href={href} className="flex items-center gap-2">
                                {cta}
                                <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                            </Link>
                        </Button>
                    </div>
                </div>
            </div>
        </Card>
    );
}
