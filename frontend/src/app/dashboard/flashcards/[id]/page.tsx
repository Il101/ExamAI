'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useExamDetail } from '@/lib/hooks/use-exam-detail';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, ArrowLeft, Play, Brain, Layers } from 'lucide-react';
import Link from 'next/link';
import { studyApi } from '@/lib/api/study';

export default function ExamFlashcardsPage() {
    const params = useParams();
    const router = useRouter();
    const examId = params.id as string;

    const { exam, isLoading } = useExamDetail(examId);
    const [flashcardCounts, setFlashcardCounts] = useState<Record<string, number>>({});
    const [loadingCounts, setLoadingCounts] = useState(false);

    // Fetch flashcard counts for all topics
    useEffect(() => {
        const fetchFlashcardCounts = async () => {
            const topics = (exam as any)?.topics;
            if (!exam || !topics || topics.length === 0) {
                setLoadingCounts(false);
                return;
            }

            setLoadingCounts(true);
            const counts: Record<string, number> = {};

            try {
                // Fetch flashcard count for each topic
                await Promise.all(
                    topics.map(async (topic: any) => {
                        try {
                            const flashcards = await studyApi.getDueReviews(100, undefined, topic.id);
                            counts[topic.id] = Array.isArray(flashcards) ? flashcards.length : 0;
                        } catch (error) {
                            console.error(`Failed to fetch flashcards for topic ${topic.id}:`, error);
                            counts[topic.id] = 0;
                        }
                    })
                );

                setFlashcardCounts(counts);
            } catch (error) {
                console.error('Failed to fetch flashcard counts:', error);
            } finally {
                setLoadingCounts(false);
            }
        };

        fetchFlashcardCounts();
    }, [exam]);

    const handleStartReview = (topicId?: string) => {
        // Navigate directly to study session with flashcards
        const query = new URLSearchParams();
        query.set('examId', examId);
        if (topicId) {
            query.set('topicId', topicId);
        }
        router.push(`/dashboard/study/session?${query.toString()}`);
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!exam) return <div>Exam not found</div>;

    const topics = (exam as any).topics || [];

    return (
        <div className="container max-w-5xl py-8 space-y-8">
            {/* Header */}
            <div>
                <Link href="/dashboard/flashcards" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary mb-4 transition-colors">
                    <ArrowLeft className="h-4 w-4 mr-1" />
                    Back to Library
                </Link>
                <div className="flex items-start justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">{exam.title}</h1>
                        <p className="text-muted-foreground mt-1 flex items-center gap-2">
                            <Layers className="h-4 w-4" />
                            {topics.length} Topics
                            {!loadingCounts && (
                                <>
                                    <span className="text-gray-300">|</span>
                                    <Brain className="h-4 w-4" />
                                    {Object.values(flashcardCounts).reduce((sum, count) => sum + count, 0)} Total Cards
                                </>
                            )}
                            <span className="text-gray-300">|</span>
                            <Link href={`/dashboard/exams/${exam.id}`} className="hover:underline">
                                View Exam Details
                            </Link>
                        </p>
                    </div>
                    <Button
                        size="lg"
                        onClick={() => handleStartReview()}
                        disabled={loadingCounts || Object.values(flashcardCounts).reduce((sum, count) => sum + count, 0) === 0}
                        className="shadow-lg"
                    >
                        <Play className="mr-2 h-4 w-4" />
                        Study All Cards
                    </Button>
                </div>
            </div>

            {/* Topics List */}
            <div className="grid gap-4">
                {topics.map((topic: any, index: number) => (
                    <Card key={topic.id} className="hover:bg-muted/30 transition-colors">
                        <CardContent className="p-6 flex items-center justify-between">
                            <div className="flex items-start gap-4 flex-1">
                                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-1">
                                    <span className="font-bold text-primary">{index + 1}</span>
                                </div>
                                <div className="flex-1">
                                    <h3 className="font-semibold text-lg mb-2">{topic.topic_name}</h3>
                                    <div className="flex items-center gap-2">
                                        <Badge variant="outline" className="font-normal">
                                            {topic.status === 'ready' ? 'Ready' : 'Pending'}
                                        </Badge>
                                        {loadingCounts ? (
                                            <span className="flex items-center gap-1 text-sm text-muted-foreground">
                                                <Loader2 className="h-3 w-3 animate-spin" />
                                                Loading...
                                            </span>
                                        ) : (
                                            <Badge variant={flashcardCounts[topic.id] > 0 ? "default" : "secondary"}>
                                                <Brain className="h-3 w-3 mr-1" />
                                                {flashcardCounts[topic.id] || 0} cards
                                            </Badge>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <Button
                                variant="secondary"
                                size="lg"
                                onClick={() => handleStartReview(topic.id)}
                                disabled={loadingCounts || !flashcardCounts[topic.id] || flashcardCounts[topic.id] === 0}
                            >
                                <Brain className="mr-2 h-4 w-4" />
                                Study
                            </Button>
                        </CardContent>
                    </Card>
                ))}

                {topics.length === 0 && (
                    <div className="text-center py-12 border rounded-lg bg-muted/10">
                        <p className="text-muted-foreground">No topics found for this exam.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
