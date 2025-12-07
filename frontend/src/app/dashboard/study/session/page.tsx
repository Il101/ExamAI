'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { studyApi, ReviewItem } from '@/lib/api/study';
import { Flashcard } from '@/components/study/flashcard';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Card } from '@/components/ui/card';
import { Loader2, Trophy, ArrowRight, X } from 'lucide-react';
import { toast } from 'sonner';

export default function StudySessionPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const examId = searchParams.get('examId');
    const topicId = searchParams.get('topicId');

    const [isLoading, setIsLoading] = useState(true);
    const [items, setItems] = useState<ReviewItem[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [results, setResults] = useState<number[]>([]);
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
        const loadSession = async () => {
            try {
                // In a real app, we might start a session on the backend here
                // For now, we just fetch due reviews
                const dueItems = await studyApi.getDueReviews(
                    20,
                    examId || undefined,
                    topicId || undefined
                );
                setItems(dueItems);
            } catch (error) {
                console.error('Failed to load reviews:', error);
                toast.error('Failed to load review items. Please try again.');
            } finally {
                setIsLoading(false);
            }
        };

        loadSession();
    }, [examId, topicId]);

    const handleReviewResult = async (quality: number) => {
        const currentItem = items[currentIndex];

        try {
            // Submit review to backend
            await studyApi.submitReview(currentItem.id, quality);

            setResults([...results, quality]);

            if (currentIndex < items.length - 1) {
                setCurrentIndex(currentIndex + 1);
            } else {
                setIsComplete(true);
            }
        } catch (error) {
            console.error('Failed to submit review:', error);
            toast.error('Failed to save your progress. Please try again.');
        }
    };

    const handleFinish = () => {
        router.push('/dashboard');
    };

    if (isLoading) {
        return (
            <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (items.length === 0) {
        return (
            <div className="container max-w-2xl py-12">
                <Card className="text-center p-12">
                    <div className="flex justify-center mb-6">
                        <Trophy className="h-16 w-16 text-yellow-500" />
                    </div>
                    <h2 className="text-2xl font-bold mb-4">All Caught Up!</h2>
                    <p className="text-muted-foreground mb-8">
                        You have no reviews due right now. Great job keeping up with your studies!
                    </p>
                    <Button onClick={handleFinish}>Back to Dashboard</Button>
                </Card>
            </div>
        );
    }

    if (isComplete) {
        const correctCount = results.filter(r => r >= 3).length;
        const accuracy = Math.round((correctCount / results.length) * 100);

        return (
            <div className="container max-w-2xl py-12">
                <Card className="text-center p-12 animate-in fade-in zoom-in duration-500">
                    <div className="flex justify-center mb-6">
                        <div className="h-20 w-20 rounded-full bg-green-100 flex items-center justify-center">
                            <Trophy className="h-10 w-10 text-green-600" />
                        </div>
                    </div>
                    <h2 className="text-3xl font-bold mb-2">Session Complete!</h2>
                    <p className="text-muted-foreground mb-8">
                        You reviewed {items.length} items in this session.
                    </p>

                    <div className="grid grid-cols-3 gap-4 mb-8">
                        <div className="p-4 bg-muted rounded-lg">
                            <div className="text-2xl font-bold">{items.length}</div>
                            <div className="text-xs text-muted-foreground uppercase">Cards</div>
                        </div>
                        <div className="p-4 bg-muted rounded-lg">
                            <div className="text-2xl font-bold text-green-600">{accuracy}%</div>
                            <div className="text-xs text-muted-foreground uppercase">Accuracy</div>
                        </div>
                        <div className="p-4 bg-muted rounded-lg">
                            <div className="text-2xl font-bold text-blue-600">1</div>
                            <div className="text-xs text-muted-foreground uppercase">Day Streak</div>
                        </div>
                    </div>

                    <Button size="lg" onClick={handleFinish} className="w-full">
                        Back to Dashboard
                        <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                </Card>
            </div>
        );
    }

    const progress = ((currentIndex) / items.length) * 100;
    const currentItem = items[currentIndex];

    return (
        <div className="container max-w-4xl py-8 min-h-[calc(100vh-4rem)] flex flex-col">
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={handleFinish}>
                        <X className="h-5 w-5" />
                    </Button>
                    <div className="space-y-1">
                        <h2 className="font-semibold">Review Session</h2>
                        <p className="text-xs text-muted-foreground">
                            Card {currentIndex + 1} of {items.length}
                        </p>
                    </div>
                </div>
                <div className="w-32 md:w-48">
                    <Progress value={progress} className="h-2" />
                </div>
            </div>

            <div className="max-w-2xl mx-auto">
                <Flashcard
                    key={currentItem.id}
                    item={currentItem}
                    onResult={handleReviewResult}
                />
            </div>
        </div>
    );
}
