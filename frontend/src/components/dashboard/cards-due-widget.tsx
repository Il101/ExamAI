'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { studyApi, ReviewItem } from '@/lib/api/study';
import { Bell, Play, Calendar, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export function CardsDueWidget() {
    const [dueCards, setDueCards] = useState<ReviewItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchDueCards = async () => {
            try {
                const cards = await studyApi.getDueReviews(100);
                setDueCards(cards);
            } catch (error) {
                console.error('Failed to fetch due cards:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchDueCards();
    }, []);

    const dueCount = dueCards.length;

    // Urgency color based on count
    const getUrgencyColor = () => {
        if (dueCount === 0) return 'text-green-400';
        if (dueCount <= 10) return 'text-yellow-400';
        if (dueCount <= 25) return 'text-orange-400';
        return 'text-red-400';
    };

    const getUrgencyBg = () => {
        if (dueCount === 0) return 'bg-green-500/20';
        if (dueCount <= 10) return 'bg-yellow-500/20';
        if (dueCount <= 25) return 'bg-orange-500/20';
        return 'bg-red-500/20';
    };

    if (isLoading) {
        return (
            <Card className="p-6 border-border bg-card/50 backdrop-blur-xl">
                <div className="flex items-center justify-center py-4">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
            </Card>
        );
    }

    return (
        <Card className={cn(
            "p-6 border-border bg-card/50 backdrop-blur-xl relative overflow-hiddengroup hover:shadow-lg transition-all duration-300",
            dueCount > 0 && "border-primary/30 hover:border-primary/50"
        )}>
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                        <Calendar className="h-4 w-4" />
                        Cards Due Today
                    </p>
                    <p className={cn("text-3xl font-bold mt-1", getUrgencyColor())}>
                        {dueCount}
                    </p>
                    {dueCount > 0 && (
                        <p className="text-xs text-muted-foreground mt-1">
                            {dueCount === 1 ? 'card needs' : 'cards need'} review
                        </p>
                    )}
                </div>
                <div className={cn("h-12 w-12 rounded-full flex items-center justify-center", getUrgencyBg())}>
                    <Bell className={cn("h-6 w-6", getUrgencyColor())} />
                </div>
            </div>

            {dueCount > 0 && (
                <div className="mt-4 flex gap-2">
                    <Link href="/dashboard/review-queue" className="flex-1">
                        <Button variant="outline" size="sm" className="w-full">
                            View Queue
                        </Button>
                    </Link>
                    <Link href="/dashboard/flashcards">
                        <Button size="sm" className="gap-1">
                            <Play className="h-3 w-3" />
                            Review
                        </Button>
                    </Link>
                </div>
            )}

            {dueCount === 0 && (
                <p className="text-xs text-green-500 mt-3 flex items-center gap-1">
                    ✓ You're all caught up!
                </p>
            )}
        </Card>
    );
}
