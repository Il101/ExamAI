'use client';

import { useParams, useRouter } from 'next/navigation';
import { useExamDetail } from '@/lib/hooks/use-exam-detail';
import { useStudySession } from '@/lib/hooks/use-study-session';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, ArrowLeft, Play, Brain, Layers, Clock } from 'lucide-react';
import Link from 'next/link';
import { toast } from 'sonner';

export default function ExamFlashcardsPage() {
    const params = useParams();
    const router = useRouter();
    const examId = params.id as string;

    const { exam, isLoading } = useExamDetail(examId);
    const { startSession, isStarting } = useStudySession();

    const handleStartSession = (options: { examId: string; topicId?: string }) => {
        startSession({ examId: options.examId, duration: 25 }, {
            onSuccess: (session) => {
                // Here we need to make sure the session page knows what to load.
                // Currently /dashboard/study/session loads by examId.
                // We should probably update that page to check for topicId as well if we passed it?
                // For now, let's stick to the URL params the session page expects.
                const query = new URLSearchParams();
                query.set('examId', session.exam_id);
                if (options.topicId) {
                    query.set('topicId', options.topicId);
                }
                router.push(`/dashboard/study/session?${query.toString()}`);
            },
            onError: () => {
                toast.error('Failed to start session');
            }
        });
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
                            <span className="text-gray-300">|</span>
                            <Link href={`/dashboard/exams/${exam.id}`} className="hover:underline">
                                View Exam Details
                            </Link>
                        </p>
                    </div>
                    <Button
                        size="lg"
                        onClick={() => handleStartSession({ examId: exam.id })}
                        disabled={isStarting}
                        className="shadow-lg"
                    >
                        {isStarting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                        Study All Cards
                    </Button>
                </div>
            </div>

            {/* Topics List */}
            <div className="grid gap-4">
                {topics.map((topic: any, index: number) => (
                    <Card key={topic.id} className="hover:bg-muted/30 transition-colors">
                        <CardContent className="p-6 flex items-center justify-between">
                            <div className="flex items-start gap-4">
                                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-1">
                                    <span className="font-bold text-primary">{index + 1}</span>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-lg">{topic.topic_name}</h3>
                                    <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                                        <Badge variant="outline" className="font-normal">
                                            {topic.status === 'ready' ? 'Ready' : topic.status}
                                        </Badge>
                                        {topic.estimated_study_minutes && (
                                            <span className="flex items-center gap-1">
                                                <Clock className="h-3 w-3" />
                                                {topic.estimated_study_minutes} min
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <Button
                                variant="secondary"
                                onClick={() => handleStartSession({ examId: exam.id, topicId: topic.id })}
                                disabled={isStarting || topic.status !== 'ready'}
                            >
                                <Brain className="mr-2 h-4 w-4" />
                                Study Topic
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
