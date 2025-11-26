'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { topicsApi, Topic } from '@/lib/api/topics';
import { examsApi, ExamWithTopics } from '@/lib/api/exams';
import { Breadcrumbs, BreadcrumbItem } from '@/components/ui/breadcrumbs';
import { TopicSidebar } from '@/components/exam/topic-sidebar';
import { TopicNavigation } from '@/components/exam/topic-navigation';
import { AiTutorChat } from '@/components/exam/ai-tutor-chat';
import { CheckYourself } from '@/components/exam/check-yourself';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Clock, BarChart3, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function TopicDetailPage() {
    const params = useParams();
    const topicId = params.id as string;

    const [topic, setTopic] = useState<Topic | null>(null);
    const [exam, setExam] = useState<ExamWithTopics | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [quizCompleted, setQuizCompleted] = useState(false);
    const [quizScore, setQuizScore] = useState<{ score: number; total: number } | null>(null);

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
        { label: 'Dashboard', href: '/dashboard', icon: 'home' },
        { label: 'Exams', href: '/dashboard/exams', icon: 'exam' },
        { label: exam.title, href: `/dashboard/exams/${exam.id}`, icon: 'exam' },
        { label: topic.topic_name, icon: 'topic' },
    ];

    return (
        <div className="flex h-screen overflow-hidden">
            {/* Left Sidebar - Topic Navigation */}
            <TopicSidebar
                exam={exam}
                currentTopicId={topicId}
                className="hidden lg:flex"
            />

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto">
                <div className="container max-w-4xl py-8 px-6">
                    {/* Breadcrumbs */}
                    <Breadcrumbs items={breadcrumbItems} className="mb-6" />

                    {/* Topic Header */}
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold mb-4">{topic.topic_name}</h1>
                        <div className="flex flex-wrap gap-2">
                            <Badge variant="secondary" className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                ~{topic.estimated_study_minutes || 5} min
                            </Badge>
                            <Badge variant="outline" className="flex items-center gap-1">
                                <BarChart3 className="h-3 w-3" />
                                Difficulty: {topic.difficulty_level}/3
                            </Badge>
                            <Badge variant="outline">
                                Topic {currentIndex + 1} of {topics.length}
                            </Badge>
                        </div>
                    </div>

                    {/* Topic Content */}
                    <div className="prose prose-slate dark:prose-invert max-w-none mb-8">
                        {topic.content ? (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {topic.content}
                            </ReactMarkdown>
                        ) : (
                            <Card className="p-8 text-center">
                                <p className="text-muted-foreground">
                                    No content available for this topic yet.
                                </p>
                            </Card>
                        )}
                    </div>

                    {/* Check Yourself Quiz */}
                    {topic.content && (
                        <div className="mb-8">
                            <CheckYourself
                                topicId={topic.id}
                                onComplete={handleQuizComplete}
                                onSkip={handleQuizSkip}
                            />
                        </div>
                    )}

                    {/* Navigation */}
                    <TopicNavigation
                        currentIndex={currentIndex}
                        totalTopics={topics.length}
                        prevTopicId={prevTopicId}
                        nextTopicId={quizCompleted ? nextTopicId : null}
                    />
                </div>
            </div>

            {/* Right Sidebar - AI Tutor (Desktop Only) */}
            <aside className="hidden xl:flex w-80 border-l bg-muted/30 flex-col">
                <div className="p-4 border-b">
                    <h3 className="font-semibold text-sm">💬 AI Tutor</h3>
                    <p className="text-xs text-muted-foreground mt-1">
                        Ask questions about this topic
                    </p>
                </div>
                <div className="flex-1 overflow-hidden">
                    <AiTutorChat topicId={topicId} />
                </div>
            </aside>
        </div>
    );
}
