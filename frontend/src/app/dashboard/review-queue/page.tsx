'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { studyApi, ReviewItem } from '@/lib/api/study';
import {
    Loader2,
    Calendar,
    BarChart3,
    Brain,
    ArrowRight,
    Filter,
    Clock
} from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { formatDistanceToNow, parseISO, isPast, isToday } from 'date-fns';
import {
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
} from '@/components/ui/tabs';

const STATE_COLORS: Record<string, string> = {
    new: 'bg-blue-500/20 text-blue-400',
    learning: 'bg-yellow-500/20 text-yellow-400',
    review: 'bg-green-500/20 text-green-400',
    relearning: 'bg-orange-500/20 text-orange-400',
};

const STATE_LABELS: Record<string, string> = {
    new: 'New',
    learning: 'Learning',
    review: 'Review',
    relearning: 'Relearning',
};

export default function ReviewQueuePage() {
    const [allCards, setAllCards] = useState<ReviewItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [filter, setFilter] = useState<'due' | 'all'>('due');

    useEffect(() => {
        const fetchCards = async () => {
            try {
                const cards = await studyApi.getDueReviews(1000);
                setAllCards(cards);
            } catch (error) {
                console.error('Failed to fetch cards:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchCards();
    }, []);

    const dueCards = allCards.filter(card => {
        const nextReview = parseISO(card.next_review_date);
        return isPast(nextReview) || isToday(nextReview);
    });

    const displayCards = filter === 'due' ? dueCards : allCards;

    // Statistics
    const stateCounts = allCards.reduce((acc, card) => {
        acc[card.state] = (acc[card.state] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const avgStability = allCards.length > 0
        ? (allCards.reduce((sum, c) => sum + c.stability, 0) / allCards.length).toFixed(1)
        : '0';

    const avgDifficulty = allCards.length > 0
        ? (allCards.reduce((sum, c) => sum + c.difficulty, 0) / allCards.length).toFixed(1)
        : '0';

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Review Queue</h1>
                    <p className="text-muted-foreground mt-2">
                        All your flashcards with FSRS scheduling data
                    </p>
                </div>
                {dueCards.length > 0 && (
                    <Link href="/dashboard/flashcards">
                        <Button className="gap-2">
                            Start Review
                            <ArrowRight className="h-4 w-4" />
                        </Button>
                    </Link>
                )}
            </div>

            {/* Stats Row */}
            <div className="grid gap-4 md:grid-cols-5">
                <Card className="p-4">
                    <p className="text-xs text-muted-foreground mb-1">Due Today</p>
                    <p className="text-2xl font-bold text-orange-400">{dueCards.length}</p>
                </Card>
                <Card className="p-4">
                    <p className="text-xs text-muted-foreground mb-1">Total Cards</p>
                    <p className="text-2xl font-bold">{allCards.length}</p>
                </Card>
                <Card className="p-4">
                    <p className="text-xs text-muted-foreground mb-1">Avg. Stability</p>
                    <p className="text-2xl font-bold text-blue-400">{avgStability} days</p>
                </Card>
                <Card className="p-4">
                    <p className="text-xs text-muted-foreground mb-1">Avg. Difficulty</p>
                    <p className="text-2xl font-bold text-purple-400">{avgDifficulty}/10</p>
                </Card>
                <Card className="p-4">
                    <p className="text-xs text-muted-foreground mb-1">Total Lapses</p>
                    <p className="text-2xl font-bold text-red-400">
                        {allCards.reduce((sum, c) => sum + c.lapses, 0)}
                    </p>
                </Card>
            </div>

            {/* State Distribution */}
            <Card className="p-6">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Card State Distribution
                </h3>
                <div className="flex gap-4 flex-wrap">
                    {Object.entries(STATE_LABELS).map(([state, label]) => (
                        <div key={state} className="flex items-center gap-2">
                            <Badge className={cn('px-3 py-1', STATE_COLORS[state])}>
                                {label}
                            </Badge>
                            <span className="text-sm font-medium">{stateCounts[state] || 0}</span>
                        </div>
                    ))}
                </div>
            </Card>

            {/* Cards Table */}
            <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold flex items-center gap-2">
                        <Brain className="h-4 w-4" />
                        Cards ({displayCards.length})
                    </h3>
                    <Tabs value={filter} onValueChange={(v) => setFilter(v as 'due' | 'all')}>
                        <TabsList>
                            <TabsTrigger value="due" className="text-xs">
                                <Clock className="h-3 w-3 mr-1" />
                                Due ({dueCards.length})
                            </TabsTrigger>
                            <TabsTrigger value="all" className="text-xs">
                                <Filter className="h-3 w-3 mr-1" />
                                All ({allCards.length})
                            </TabsTrigger>
                        </TabsList>
                    </Tabs>
                </div>

                {displayCards.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                        <Brain className="h-12 w-12 mx-auto mb-4 opacity-30" />
                        <p>No cards {filter === 'due' ? 'due today' : 'found'}.</p>
                        {filter === 'due' && (
                            <p className="text-sm mt-2">You're all caught up! 🎉</p>
                        )}
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b text-left text-muted-foreground">
                                    <th className="pb-3 font-medium">Question</th>
                                    <th className="pb-3 font-medium">State</th>
                                    <th className="pb-3 font-medium">Next Review</th>
                                    <th className="pb-3 font-medium">Interval</th>
                                    <th className="pb-3 font-medium">Stability</th>
                                    <th className="pb-3 font-medium">Difficulty</th>
                                    <th className="pb-3 font-medium">Reps</th>
                                    <th className="pb-3 font-medium">Lapses</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {displayCards.map((card) => {
                                    const nextReview = parseISO(card.next_review_date);
                                    const isDue = isPast(nextReview) || isToday(nextReview);

                                    return (
                                        <tr key={card.id} className="hover:bg-muted/30">
                                            <td className="py-3 max-w-xs truncate pr-4">
                                                {card.question}
                                            </td>
                                            <td className="py-3">
                                                <Badge className={cn('text-xs', STATE_COLORS[card.state])}>
                                                    {STATE_LABELS[card.state]}
                                                </Badge>
                                            </td>
                                            <td className={cn("py-3", isDue && "text-orange-400 font-medium")}>
                                                {isDue ? 'Due!' : formatDistanceToNow(nextReview, { addSuffix: true })}
                                            </td>
                                            <td className="py-3 text-muted-foreground">
                                                {card.scheduled_days} days
                                            </td>
                                            <td className="py-3">
                                                <span className="text-blue-400">{card.stability.toFixed(1)}</span>
                                            </td>
                                            <td className="py-3">
                                                <span className="text-purple-400">{card.difficulty.toFixed(1)}</span>
                                            </td>
                                            <td className="py-3 text-muted-foreground">{card.reps}</td>
                                            <td className="py-3">
                                                <span className={cn(card.lapses > 0 && "text-red-400")}>
                                                    {card.lapses}
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </Card>
        </div>
    );
}
