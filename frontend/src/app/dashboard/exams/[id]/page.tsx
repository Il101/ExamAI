'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useExamDetail } from '@/lib/hooks/use-exam-detail';
import { ExamHeader } from '@/components/exam/exam-header';
import { ExamSummary } from '@/components/exam/exam-summary';
import { TopicList } from '@/components/exam/topic-list';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, AlertCircle } from 'lucide-react';
import { ExamWithTopics } from '@/lib/api/exams';
import { useExams } from '@/lib/hooks/use-exams';
import { Button } from '@/components/ui/button';

export default function ExamDetailPage() {
    const params = useParams();
    const examId = params.id as string;

    const { exam, isLoading, isError, error } = useExamDetail(examId);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
                    <p className="text-muted-foreground">Loading exam...</p>
                </div>
            </div>
        );
    }

    if (isError) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Card className="max-w-md">
                    <CardContent className="pt-6">
                        <div className="text-center">
                            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
                            <h2 className="text-xl font-semibold mb-2">Error Loading Exam</h2>
                            <p className="text-muted-foreground">
                                {error instanceof Error ? error.message : 'Failed to load exam details'}
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (!exam) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Card className="max-w-md">
                    <CardContent className="pt-6">
                        <div className="text-center">
                            <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                            <h2 className="text-xl font-semibold mb-2">Exam Not Found</h2>
                            <p className="text-muted-foreground">
                                The exam you&apos;re looking for doesn&apos;t exist or you don&apos;t have access to it.
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    const { createPlan, startGeneration, isPlanning, isGenerating } = useExams();

    const renderReadyContent = () => (
        <Tabs defaultValue="summary" className="w-full">
            <TabsList className="grid w-full max-w-md grid-cols-3">
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="topics">Topics</TabsTrigger>
                <TabsTrigger value="progress">Progress</TabsTrigger>
            </TabsList>

            <TabsContent value="summary" className="mt-6">
                <ExamSummary exam={exam} onGenerateTopics={() => { }} />
            </TabsContent>

            <TabsContent value="topics" className="mt-6">
                <TopicList exam={exam as ExamWithTopics} />
            </TabsContent>

            <TabsContent value="progress" className="mt-6">
                <Card className="p-8 text-center">
                    <h3 className="text-lg font-semibold mb-2">Progress Tracking</h3>
                    <p className="text-muted-foreground">
                        Coming soon! Here you'll see your study timeline, completed topics, and review statistics.
                    </p>
                </Card>
            </TabsContent>
        </Tabs>
    );

    const renderContent = () => {
        if (exam.status === 'ready') {
            return renderReadyContent();
        }

        if (exam.status === 'generating') {
            const progress = exam.progress || 0;
            const currentStep = exam.current_step || 'Initializing...';
            const message = exam.message || 'AI is crafting your exam. This may take a few minutes.';
            const progressPercent = Math.round(progress * 100);

            return (
                <div className="text-center py-12">
                    <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
                    <h3 className="text-lg font-semibold mb-2">Generating Exam Content</h3>
                    <p className="text-muted-foreground mb-2">
                        {message}
                    </p>
                    <p className="text-sm text-muted-foreground mb-4">
                        {currentStep}
                    </p>
                    <div className="max-w-xs mx-auto">
                        <div className="bg-muted rounded-full h-2 overflow-hidden mb-2">
                            <div
                                className="bg-primary h-full transition-all duration-500 ease-out"
                                style={{ width: `${progressPercent}%` }}
                            ></div>
                        </div>
                        <p className="text-xs text-muted-foreground">{progressPercent}%</p>
                    </div>
                </div>
            );
        }

        if (exam.status === 'failed') {
            return (
                <div className="text-center py-12">
                    <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">Generation Failed</h3>
                    <p className="text-muted-foreground">
                        There was an error generating your exam. Please try again.
                    </p>
                </div>
            );
        }

        if (exam.status === 'draft') {
            return (
                <div className="text-center py-12">
                    <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-2">Exam Draft Created</h3>
                        <p className="text-muted-foreground max-w-md mx-auto">
                            Your exam setup is ready. Next, we'll generate a study plan with topics based on your materials.
                        </p>
                    </div>
                    <Button
                        onClick={() => createPlan(exam.id)}
                        disabled={isPlanning}
                        size="lg"
                    >
                        {isPlanning ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Planning...
                            </>
                        ) : (
                            'Generate Study Plan'
                        )}
                    </Button>
                </div>
            );
        }

        if (exam.status === 'planned') {
            return (
                <div className="space-y-8">
                    <div className="text-center py-8 border-b">
                        <h3 className="text-lg font-semibold mb-2">Study Plan Ready</h3>
                        <p className="text-muted-foreground mb-6">
                            Review the topics below. When you're ready, start generating the full content.
                        </p>
                        <Button
                            onClick={() => startGeneration(exam.id)}
                            disabled={isGenerating}
                            size="lg"
                        >
                            {isGenerating ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Starting...
                                </>
                            ) : (
                                'Start Generation'
                            )}
                        </Button>
                    </div>

                    {/* Show topics preview if available */}
                    <div className="opacity-70 pointer-events-none">
                        <TopicList exam={{
                            ...exam,
                            topics: (exam as ExamWithTopics).topics?.length > 0
                                ? (exam as ExamWithTopics).topics
                                : (exam.plan_data?.blocks.flatMap((block, bIdx) =>
                                    block.topics.map((topic, tIdx) => ({
                                        id: topic.id,
                                        topic_name: topic.title,
                                        content: topic.description,
                                        order_index: bIdx * 10 + tIdx,
                                        difficulty_level: 1,
                                        estimated_study_minutes: topic.estimated_paragraphs * 3
                                    }))
                                ) || [])
                        } as ExamWithTopics} />
                    </div>
                </div>
            );
        }

        return null;
    };

    return (
        <div className="container max-w-5xl py-8">
            <div className="mb-8">
                <ExamHeader
                    examId={exam.id}
                    title={exam.title}
                    subject={exam.subject}
                    status={exam.status}
                    topicCount={exam.topic_count}
                    createdAt={exam.created_at}
                    updatedAt={exam.updated_at}
                />
            </div>

            {renderContent()}
        </div>
    );
}
