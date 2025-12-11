'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { studyApi, ReviewItem, StudySession as SessionModel } from '@/lib/api/study';
import { Flashcard } from './flashcard';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

interface StudySessionProps {
    examId: string;
}

export function StudySession({ examId }: StudySessionProps) {
    const router = useRouter();
    const [session, setSession] = useState<SessionModel | null>(null);
    const [queue, setQueue] = useState<ReviewItem[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isComplete, setIsComplete] = useState(false);

    // Initialize session
    useEffect(() => {
        const initSession = async () => {
            try {
                // 1. Start session
                const newSession = await studyApi.startSession(examId);
                setSession(newSession);

                // 2. Fetch reviews
                const reviews = await studyApi.getDueReviews(20);

                if (reviews.length === 0) {
                    setIsComplete(true);
                } else {
                    setQueue(reviews);
                }
            } catch (error) {
                console.error('Failed to start session:', error);
                toast.error('Failed to start study session');
            } finally {
                setIsLoading(false);
            }
        };

        initSession();
    }, [examId]);

    const handleRate = async (quality: number) => {
        if (!session || isSubmitting) return;

        const currentItem = queue[currentIndex];
        setIsSubmitting(true);

        try {
            await studyApi.submitReview(currentItem.id, quality);

            // Move to next card
            if (currentIndex < queue.length - 1) {
                setCurrentIndex(prev => prev + 1);
            } else {
                // Session complete
                await studyApi.endSession(session.id);
                setIsComplete(true);
            }
        } catch (error) {
            console.error('Failed to submit review:', error);
            toast.error('Failed to save progress');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
                <p className="text-muted-foreground">Preparing your study session...</p>
            </div>
        );
    }

    if (isComplete) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
                <div className="bg-green-100 dark:bg-green-900/30 p-6 rounded-full mb-6">
                    <CheckCircle2 className="h-16 w-16 text-green-600 dark:text-green-400" />
                </div>
                <h2 className="text-3xl font-bold mb-2">Session Complete!</h2>
                <p className="text-muted-foreground mb-8 max-w-md">
                    You&apos;ve reviewed all scheduled cards for now. Great job keeping up with your spaced repetition!
                </p>
                <div className="flex gap-4">
                    <Button onClick={() => router.back()}>
                        Back
                    </Button>
                    <Button variant="outline" onClick={() => router.back()}>
                        Back
                    </Button>
                </div>
            </div>
        );
    }

    if (queue.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
                <AlertCircle className="h-16 w-16 text-muted-foreground mb-4" />
                <h2 className="text-2xl font-bold mb-2">No Reviews Due</h2>
                <p className="text-muted-foreground mb-8">
                    You&apos;re all caught up! Check back later for more reviews.
                </p>
                <Button onClick={() => router.back()}>
                    Back
                </Button>
            </div>
        );
    }

    const currentItem = queue[currentIndex];
    const progress = ((currentIndex) / queue.length) * 100;

    return (
        <div className="flex flex-col items-center max-w-5xl mx-auto py-8 px-4">
            <Flashcard
                key={currentItem.id}
                item={currentItem}
                onResult={handleRate}
            />
        </div>
    );
}
