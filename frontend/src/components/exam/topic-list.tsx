'use client';

import { ExamWithTopics } from '@/lib/api/exams';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Clock, Brain, CheckCircle2, BookOpen, ExternalLink } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface TopicListProps {
    exam: ExamWithTopics;
}

export function TopicList({ exam }: TopicListProps) {
    const router = useRouter();

    const handleStartReview = () => {
        router.push(`/dashboard/study/session?examId=${exam.id}`);
    };

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Your Study Topics</h2>
                    <p className="text-muted-foreground">
                        {exam.topics.length} topics generated from your summary
                    </p>
                </div>
                <Button size="lg" onClick={handleStartReview} className="shadow-lg hover:shadow-xl transition-all">
                    <Play className="mr-2 h-5 w-5" />
                    Start First Review
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
                                    {/* Difficulty Indicator Mockup */}
                                    <div className="flex gap-0.5">
                                        {[1, 2, 3].map((i) => (
                                            <div
                                                key={i}
                                                className={`h-2 w-2 rounded-full ${i <= (topic.difficulty_level || 2) // Default to medium if not set
                                                    ? 'bg-primary'
                                                    : 'bg-muted'
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
                                        <span>Next review:</span>
                                        <span className="font-medium text-foreground">Tomorrow</span>
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
                        Start Now
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}
