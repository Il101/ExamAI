'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useReviews } from '@/lib/hooks/use-reviews';
import { useStudySession } from '@/lib/hooks/use-study-session';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Flashcard } from '@/components/study/flashcard';
import { Brain, CheckCircle } from 'lucide-react';
import Link from 'next/link';

import { useEffect } from 'react';
import { usePomodoroStore } from '@/lib/hooks/use-pomodoro';
import { PomodoroTimer } from '@/components/study/pomodoro-timer';

export default function StudyPage() {
    const searchParams = useSearchParams();
    const examId = searchParams.get('exam');

    const { dueReviews, submitReview } = useReviews(20);
    const { startSession, endSession, isStarting, isEnding } = useStudySession();

    // Pomodoro Store
    const { start, pause, reset, isBreak, isRunning } = usePomodoroStore();

    const [currentIndex, setCurrentIndex] = useState(0);
    const [sessionActive, setSessionActive] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [reviewedCount, setReviewedCount] = useState(0);

    const currentReview = dueReviews?.[currentIndex];
    const totalReviews = dueReviews?.length || 0;
    const progress = totalReviews > 0 ? ((currentIndex + 1) / totalReviews) * 100 : 0;

    // Start timer when session starts
    useEffect(() => {
        if (sessionActive && !isRunning && !isBreak) {
            start();
        }
        return () => {
            // Optional: pause on unmount or session end?
            // pause(); 
        };
    }, [sessionActive, start, isRunning, isBreak]);

    const handleStartSession = () => {
        if (examId) {
            startSession({ examId, duration: 25 }, {
                onSuccess: (session) => {
                    setSessionActive(true);
                    setSessionId(session.id);
                    reset(); // Reset timer for new session
                    start();
                },
            });
        } else {
            setSessionActive(true);
            reset();
            start();
        }
    };

    const handleEndSession = () => {
        if (sessionId) {
            endSession(sessionId);
        }
        setSessionActive(false);
        pause();
    };

    const handleReview = (quality: number) => {
        if (!currentReview) return;

        submitReview(
            { reviewId: currentReview.id, quality },
            {
                onSuccess: () => {
                    setReviewedCount(prev => prev + 1);
                    if (currentIndex < totalReviews - 1) {
                        setCurrentIndex(prev => prev + 1);
                    }
                },
            }
        );
    };

    const isCompleted = currentIndex >= totalReviews - 1 && reviewedCount > 0;

    if (!sessionActive) {
        return (
            <div className="max-w-2xl mx-auto">
                <Card className="p-12 text-center">
                    <Brain className="h-16 w-16 text-blue-600 mx-auto mb-6" />
                    <h1 className="text-3xl font-bold mb-4">Ready to Study?</h1>
                    <p className="text-gray-600 mb-8">
                        {totalReviews > 0
                            ? `You have ${totalReviews} reviews due. Let's get started!`
                            : 'No reviews due right now. Great job staying on top of your studies!'}
                    </p>

                    {totalReviews > 0 ? (
                        <div className="space-y-4">
                            <Button
                                size="lg"
                                onClick={handleStartSession}
                                disabled={isStarting}
                            >
                                {isStarting ? 'Starting...' : 'Start Study Session'}
                            </Button>
                            <p className="text-sm text-gray-500">
                                Recommended session: 25 minutes (Pomodoro)
                            </p>
                        </div>
                    ) : (
                        <Link href="/dashboard/exams">
                            <Button variant="outline">Back to Exams</Button>
                        </Link>
                    )}
                </Card>
            </div>
        );
    }

    if (isCompleted) {
        return (
            <div className="max-w-2xl mx-auto">
                <Card className="p-12 text-center">
                    <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-6" />
                    <h1 className="text-3xl font-bold mb-4">Session Complete!</h1>
                    <p className="text-gray-600 mb-8">
                        Great work! You reviewed {reviewedCount} cards.
                    </p>

                    <div className="grid gap-4 md:grid-cols-2 mb-8">
                        <Card className="p-4">
                            <p className="text-sm text-gray-600">Cards Reviewed</p>
                            <p className="text-3xl font-bold">{reviewedCount}</p>
                        </Card>
                        <Card className="p-4">
                            <p className="text-sm text-gray-600">Accuracy</p>
                            <p className="text-3xl font-bold">
                                {Math.round((reviewedCount / totalReviews) * 100)}%
                            </p>
                        </Card>
                    </div>

                    <div className="space-x-4">
                        <Button onClick={handleEndSession} disabled={isEnding}>
                            {isEnding ? 'Ending...' : 'End Session'}
                        </Button>
                        <Link href="/dashboard/analytics">
                            <Button variant="outline">View Analytics</Button>
                        </Link>
                    </div>
                </Card>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6 relative">
            {/* Pomodoro Timer Widget */}
            <PomodoroTimer />

            {/* Break Overlay */}
            {isBreak && (
                <div className="absolute inset-0 z-40 bg-background/80 backdrop-blur-sm flex items-center justify-center rounded-xl border-2 border-green-100 dark:border-green-900">
                    <div className="text-center p-8 bg-card rounded-xl shadow-2xl border animate-in fade-in zoom-in duration-300">
                        <div className="text-6xl mb-4">☕</div>
                        <h2 className="text-2xl font-bold mb-2">Time for a Break!</h2>
                        <p className="text-muted-foreground mb-6">
                            Take a breather. Stretch, hydrate, or just relax.
                        </p>
                        <p className="text-sm font-medium text-green-600 dark:text-green-400">
                            Cards are paused until the break ends.
                        </p>
                    </div>
                </div>
            )}

            {/* Progress Header */}
            <div className="space-y-2">
                <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>Progress</span>
                    <span>{currentIndex + 1} / {totalReviews}</span>
                </div>
                <Progress value={progress} className="h-2" />
            </div>

            {/* Flashcard */}
            {currentReview && (
                <Flashcard
                    key={currentReview.id}
                    item={currentReview}
                    onResult={handleReview}
                    disabled={isBreak}
                    className={isBreak ? "opacity-50 blur-sm transition-all duration-500" : "transition-all duration-500"}
                />
            )}

            {/* Session Info */}
            <Card className="p-4">
                <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                        <Brain className="h-4 w-4 text-blue-600" />
                        <span className="text-gray-600">Study Session Active</span>
                    </div>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleEndSession}
                        disabled={isEnding}
                    >
                        {isEnding ? 'Ending...' : 'End Session'}
                    </Button>
                </div>
            </Card>
        </div>
    );
}
