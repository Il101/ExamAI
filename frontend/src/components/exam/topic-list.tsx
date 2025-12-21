'use client';

import { ExamWithTopics } from '@/lib/api/exams';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Clock, Brain, CheckCircle2, BookOpen, ExternalLink, Calendar } from 'lucide-react';
import { format, isToday, isTomorrow, parseISO } from 'date-fns';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useState } from 'react';
import { toast } from 'sonner';

interface TopicListProps {
    exam: ExamWithTopics;
}

export function TopicList({ exam }: TopicListProps) {
    const router = useRouter();
    const [isRescheduling, setIsRescheduling] = useState(false);

    // Find first topic with incomplete quiz
    const firstIncomplete = exam.topics.find(
        topic => !topic.quiz_completed
    );

    // Check if any topics have been started
    const hasStartedTopics = exam.topics.some(
        topic => topic.is_viewed || topic.quiz_completed
    );

    // Get the index of the topic we'll navigate to
    const targetTopicIndex = firstIncomplete
        ? exam.topics.findIndex(t => t.id === firstIncomplete.id)
        : 0;

    const handleStartReview = () => {
        if (firstIncomplete) {
            router.push(`/dashboard/topics/${firstIncomplete.id}`);
        } else {
            // All topics completed, go to first topic
            router.push(`/dashboard/topics/${exam.topics[0]?.id}`);
        }
    };

    const handleReschedule = async () => {
        try {
            setIsRescheduling(true);
            const { examsApi } = await import('@/lib/api/exams');
            await examsApi.reschedule(exam.id);
            toast.success('Study plan updated based on your progress!');
            router.refresh();
        } catch (error) {
            console.error('Failed to reschedule:', error);
            toast.error('Failed to refresh schedule. Please try again.');
        } finally {
            setIsRescheduling(false);
        }
    };

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Your Study Topics</h2>
                    <div className="flex items-center gap-4 mt-1">
                        <p className="text-muted-foreground">
                            {exam.topics.length} topics generated from your summary
                        </p>
                        {exam.exam_date && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleReschedule}
                                disabled={isRescheduling}
                                className="h-7 px-2 text-xs font-medium text-primary hover:text-primary hover:bg-primary/10"
                            >
                                <Calendar className={`mr-2 h-3 w-3 ${isRescheduling ? 'animate-spin' : ''}`} />
                                {isRescheduling ? 'Refreshing...' : 'Refresh Schedule'}
                            </Button>
                        )}
                    </div>
                </div>
                <Button size="lg" onClick={handleStartReview} className="shadow-lg hover:shadow-xl transition-all">
                    <Play className="mr-2 h-5 w-5" />
                    {hasStartedTopics
                        ? `Continue → Topic ${targetTopicIndex + 1}`
                        : 'Start First Review'
                    }
                </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {exam.topics.map((topic, index) => (
                    <Link
                        key={topic.id}
                        href={`/dashboard/topics/${topic.id}`}
                        className="group"
                    >
                        <Card className="group-hover:border-primary/50 transition-colors cursor-pointer h-full">
                            <CardHeader className="pb-3">
                                <div className="flex justify-between items-start mb-2">
                                    <Badge variant="secondary" className="font-mono text-xs">
                                        Topic {index + 1}
                                    </Badge>
                                    {/* Difficulty Indicator (5 Dots) */}
                                    <div className="flex gap-0.5">
                                        {[1, 2, 3, 4, 5].map((i) => (
                                            <div
                                                key={i}
                                                className={`h-1.5 w-1.5 rounded-full transition-colors ${i <= (topic.difficulty_level || 3)
                                                    ? 'bg-primary shadow-[0_0_3px_rgba(var(--primary),0.4)]'
                                                    : 'bg-muted/40'
                                                    }`}
                                            />
                                        ))}
                                    </div>
                                </div>
                                <CardTitle className="text-lg leading-tight group-hover:text-primary transition-colors">
                                    {topic.topic_name}
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="flex flex-col gap-3 text-sm text-muted-foreground">
                                    <div className="flex items-center gap-2">
                                        <Brain className="h-4 w-4" />
                                        <span>{topic.content ? 'Content ready' : 'No content'}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Clock className="h-4 w-4" />
                                        <span>~{topic.estimated_study_minutes || 5} min</span>
                                    </div>
                                    <div className="mt-2 pt-2 border-t flex items-center justify-between text-xs">
                                        <div className="flex items-center gap-1">
                                            <Calendar className="h-3 w-3" />
                                            <span>Scheduled:</span>
                                        </div>
                                        <span className="font-medium text-foreground">
                                            {topic.scheduled_date ? (
                                                isToday(parseISO(topic.scheduled_date)) ? 'Today' :
                                                    isTomorrow(parseISO(topic.scheduled_date)) ? 'Tomorrow' :
                                                        format(parseISO(topic.scheduled_date), 'MMM d')
                                            ) : 'TBD'}
                                        </span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </Link>
                ))}
            </div>

            <Card className="bg-primary/5 border-primary/20">
                <CardContent className="flex items-center gap-4 p-6">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <CheckCircle2 className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-lg">Ready to start?</h3>
                        <p className="text-muted-foreground">
                            Your first session will take about {exam.topics.length * 2} minutes.
                            Reviewing now helps move these topics to long-term memory.
                        </p>
                    </div>
                    <Button onClick={handleStartReview} className="ml-auto" variant="outline">
                        {hasStartedTopics
                            ? `Continue → Topic ${targetTopicIndex + 1}`
                            : 'Start Now'
                        }
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}
