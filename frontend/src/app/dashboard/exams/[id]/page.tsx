'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useExamDetail } from '@/lib/hooks/use-exam-detail';
import { ExamHeader } from '@/components/exam/exam-header';
import { ExamSummary } from '@/components/exam/exam-summary';
import { TopicList } from '@/components/exam/topic-list';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, AlertCircle, Eye, CheckCircle2 } from 'lucide-react';
import { ExamWithTopics, examsApi } from '@/lib/api/exams';
import { Button } from '@/components/ui/button';

export default function ExamDetailPage() {
    const params = useParams();
    const router = useRouter();
    const examId = params.id as string;

    const { exam, isLoading, isError, error, refetch } = useExamDetail(examId);

    // State for generation button (used in 'planned' status)
    const [isGenerating, setIsGenerating] = useState(false);

    const handleStartReview = () => {
        if (!exam) return;

        // Find first topic with incomplete quiz
        const firstIncomplete = exam.topics.find(
            topic => !topic.quiz_completed
        );

        if (firstIncomplete) {
            router.push(`/dashboard/topics/${firstIncomplete.id}`);
        } else if (exam.topics.length > 0) {
            // All topics completed, go to first topic
            router.push(`/dashboard/topics/${exam.topics[0].id}`);
        }
    };

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
                            <p className="text-muted-foreground mb-4">
                                {error instanceof Error ? error.message : 'Failed to load exam details'}
                            </p>
                            <Button onClick={() => refetch()} variant="outline">
                                Try Again
                            </Button>
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



    const renderReadyContent = () => (
        <Tabs defaultValue="summary" className="w-full">
            <TabsList className="grid w-full max-w-md grid-cols-3">
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="topics">Topics</TabsTrigger>
                <TabsTrigger value="progress">Progress</TabsTrigger>
            </TabsList>

            <TabsContent value="summary" className="mt-6">
                <ExamSummary exam={exam} />
            </TabsContent>

            <TabsContent value="topics" className="mt-6">
                <TopicList exam={exam as ExamWithTopics} />
            </TabsContent>

            <TabsContent value="progress" className="mt-6">
                <div className="space-y-4">
                    <Card className="p-6">
                        <h3 className="text-lg font-semibold mb-4">Topic Progress</h3>
                        <div className="space-y-3">
                            {exam.topics?.map((topic, index) => (
                                <div key={topic.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <span className="text-sm font-medium w-6 text-muted-foreground">
                                            {index + 1}.
                                        </span>
                                        <span className="text-sm">{topic.topic_name}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {topic.is_viewed && (
                                            <Badge variant="outline" className="text-xs">
                                                <Eye className="h-3 w-3 mr-1" />
                                                Viewed
                                            </Badge>
                                        )}
                                        {topic.quiz_completed && (
                                            <Badge variant="default" className="text-xs bg-green-600">
                                                <CheckCircle2 className="h-3 w-3 mr-1" />
                                                Quiz Done
                                            </Badge>
                                        )}
                                        {!topic.is_viewed && !topic.quiz_completed && (
                                            <Badge variant="secondary" className="text-xs">
                                                Not started
                                            </Badge>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </Card>
                </div>
            </TabsContent>
        </Tabs>
    );

    const renderContent = () => {
        if (exam.status === 'ready') {
            return renderReadyContent();
        }

        if (exam.status === 'planned') {
            const handleStartGeneration = async () => {
                setIsGenerating(true);
                try {
                    await examsApi.startGeneration(exam.id);
                    // Refetch to get updated status
                    await refetch();
                } catch (error) {
                    console.error('Failed to start generation:', error);
                    alert('Failed to start generation. Please try again.');
                } finally {
                    setIsGenerating(false);
                }
            };

            // Extract topics from plan_data
            const topics = exam.topics?.length > 0
                ? exam.topics
                : (exam.plan_data?.blocks?.flatMap((block: any, bIdx: number) =>
                    block.topics.map((topic: any, tIdx: number) => ({
                        id: topic.id,
                        topic_name: topic.title,
                        content: topic.description,
                        order_index: bIdx * 10 + tIdx,
                        difficulty_level: 1,
                        estimated_study_minutes: topic.estimated_paragraphs * 3
                    }))
                ) || []);

            return (
                <div className="space-y-8">
                    <div className="text-center py-8 border-b">
                        <h3 className="text-lg font-semibold mb-2">Study Plan Ready</h3>
                        <p className="text-muted-foreground mb-6">
                            Review the topics below. When you're ready, start generating the full content.
                        </p>
                        <Button
                            onClick={handleStartGeneration}
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

                    {/* Show topics preview */}
                    <div className="opacity-70 pointer-events-none">
                        <TopicList exam={{
                            ...exam,
                            topics: topics
                        } as ExamWithTopics} />
                    </div>
                </div>
            );
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

        return null;
    };

    return (
        <div className="space-y-8">
            <div className="mb-8">
                <ExamHeader
                    examId={exam.id}
                    title={exam.title}
                    subject={exam.subject}
                    status={exam.status}
                    topicCount={exam.topic_count}
                    createdAt={exam.created_at}
                    updatedAt={exam.updated_at}
                    onStudyClick={handleStartReview}
                />
            </div>

            {renderContent()}
        </div>
    );
}
