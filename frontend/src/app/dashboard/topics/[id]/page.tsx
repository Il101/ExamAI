'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { topicsApi, Topic } from '@/lib/api/topics';
import { examsApi, ExamWithTopics } from '@/lib/api/exams';
import { useSidebar } from '@/lib/contexts/sidebar-context';
import { Breadcrumbs, BreadcrumbItem } from '@/components/ui/breadcrumbs';
import { TopicSidebar } from '@/components/exam/topic-sidebar';
import { TopicNavigation } from '@/components/exam/topic-navigation';
import { AiTutorChat } from '@/components/exam/ai-tutor-chat';
import { CheckYourself } from '@/components/exam/check-yourself';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Clock, BarChart3, AlertCircle, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';

export default function TopicDetailPage() {
    const params = useParams();
    const topicId = params.id as string;
    const { setIsCollapsed } = useSidebar();

    const [topic, setTopic] = useState<Topic | null>(null);
    const [exam, setExam] = useState<ExamWithTopics | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [quizCompleted, setQuizCompleted] = useState(false);
    const [quizScore, setQuizScore] = useState<{ score: number; total: number } | null>(null);

    // Collapse sidebar when topic page loads, expand when leaving
    useEffect(() => {
        setIsCollapsed(true);
        return () => {
            setIsCollapsed(false);
        };
    }, [setIsCollapsed]);

    useEffect(() => {
        loadTopicData();
    }, [topicId]);

    const loadTopicData = async () => {
        try {
            setIsLoading(true);
            setError(null);

            // Load topic
            const topicData = await topicsApi.getById(topicId);
            setTopic(topicData);

            // Load exam with topics for sidebar
            const examData = await examsApi.getById(topicData.exam_id);
            setExam(examData);

            // Mark topic as viewed
            try {
                await fetch(`/api/topics/${topicId}/view?exam_id=${topicData.exam_id}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    },
                });
            } catch (err) {
                console.error('Failed to mark topic as viewed:', err);
            }
        } catch (err) {
            console.error('Failed to load topic:', err);
            setError('Failed to load topic. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleQuizComplete = async (score: number, total: number) => {
        setQuizCompleted(true);
        setQuizScore({ score, total });

        // Mark quiz as completed
        if (topic) {
            try {
                await fetch(`/api/topics/${topicId}/view?exam_id=${topic.exam_id}&quiz_completed=true`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    },
                });
            } catch (err) {
                console.error('Failed to mark quiz as completed:', err);
            }
        }
    };

    const handleQuizSkip = () => {
        setQuizCompleted(true);
    };

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error || !topic || !exam) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Card className="p-12 text-center max-w-md">
                    <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
                    <h2 className="text-xl font-semibold mb-2">Error Loading Topic</h2>
                    <p className="text-muted-foreground">
                        {error || 'Topic not found.'}
                    </p>
                </Card>
            </div>
        );
    }

    // Find current topic index and navigation
    const topics = exam.topics || [];
    const currentIndex = topics.findIndex(t => t.id === topicId);
    const prevTopicId = currentIndex > 0 ? topics[currentIndex - 1].id : null;
    const nextTopicId = currentIndex < topics.length - 1 ? topics[currentIndex + 1].id : null;

    const breadcrumbItems: BreadcrumbItem[] = [
        { label: 'Exams', href: '/dashboard/exams', icon: 'exam' },
        { label: exam.title, href: `/dashboard/exams/${exam.id}`, icon: 'exam' },
        { label: topic.topic_name, icon: 'topic' },
    ];

    return (
        <div className="flex h-[calc(100vh-4rem)] overflow-hidden bg-background">
            {/* Left Sidebar - Topic Navigation */}
            <TopicSidebar
                exam={exam}
                currentTopicId={topicId}
                className="hidden lg:flex"
            />

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto w-full">
                <div className="container max-w-5xl py-8 px-8 mx-auto">
                    {/* Minimal Breadcrumbs */}
                    <div className="mb-6 flex items-center text-sm text-muted-foreground/60">
                        <Breadcrumbs items={breadcrumbItems} className="mb-0 text-xs uppercase tracking-wider font-medium" />
                    </div>

                    {/* Topic Header - Strict Style */}
                    <div className="mb-10 border-b border-border/40 pb-6">
                        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight mb-4 text-foreground">
                            {topic.topic_name}
                        </h1>

                        <div className="flex items-center gap-6 text-sm text-muted-foreground">
                            <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4 opacity-70" />
                                <span>~{topic.estimated_study_minutes || 5} min read</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <BarChart3 className="h-4 w-4 opacity-70" />
                                <span>Level {topic.difficulty_level}/3</span>
                            </div>
                            <div className="ml-auto text-xs font-mono opacity-50">
                                TOPIC {currentIndex + 1} / {topics.length}
                            </div>
                        </div>
                    </div>

                    {/* Topic Content - Modern Typography */}
                    <article className="prose prose-zinc dark:prose-invert max-w-none 
                        prose-headings:font-semibold prose-headings:tracking-tight 
                        prose-p:leading-relaxed prose-p:text-muted-foreground/90
                        prose-li:text-muted-foreground/90
                        prose-strong:text-foreground prose-strong:font-semibold
                        prose-code:text-primary prose-code:bg-primary/5 prose-code:px-1 prose-code:rounded
                        prose-pre:bg-muted/50 prose-pre:border
                        mb-12">
                        {topic.content ? (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {topic.content}
                            </ReactMarkdown>
                        ) : (
                            <div className="p-12 text-center border border-dashed rounded-lg bg-muted/20">
                                <p className="text-muted-foreground">
                                    No content available for this topic yet.
                                </p>
                            </div>
                        )}
                    </article>

                    {/* Check Yourself Quiz */}
                    {topic.content && (
                        <div className="mb-12 pt-8 border-t border-border/40">
                            <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                <CheckYourself
                                    topicId={topic.id}
                                    onComplete={handleQuizComplete}
                                    onSkip={handleQuizSkip}
                                />
                            </h3>
                        </div>
                    )}

                    {/* Navigation */}
                    <div className="pb-12">
                        <TopicNavigation
                            currentIndex={currentIndex}
                            totalTopics={topics.length}
                            prevTopicId={prevTopicId}
                            nextTopicId={quizCompleted ? nextTopicId : null}
                        />
                    </div>
                </div>
            </div>

            {/* Right Sidebar - AI Tutor (Desktop Only) */}
            <aside className="hidden xl:flex w-96 border-l bg-background/50 flex-col">
                <div className="p-4 border-b h-14 flex items-center justify-between bg-muted/10">
                    <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                        <h3 className="font-medium text-sm">AI Tutor</h3>
                    </div>
                    <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-medium">Always Active</span>
                </div>
                <div className="flex-1 overflow-hidden bg-background">
                    <AiTutorChat topicId={topicId} />
                </div>
            </aside>
        </div>
    );
}
