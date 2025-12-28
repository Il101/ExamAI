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
import { MobileAiTutor } from '@/components/exam/mobile-ai-tutor';
import { CheckYourself } from '@/components/exam/check-yourself';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, Clock, BarChart3, AlertCircle, ChevronRight, Edit, Save, X, Brain } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';
import { BlockNoteEditor } from '@/components/exam/blocknote-editor';
import { markdownToBlockNote, blockNoteToMarkdown } from '@/lib/utils/markdown-to-blocknote';
import { Block } from '@blocknote/core';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export default function TopicDetailPage() {
    const params = useParams();
    const topicId = params.id as string;
    const { setIsCollapsed, setContextualNav } = useSidebar();

    const [topic, setTopic] = useState<Topic | null>(null);
    const [exam, setExam] = useState<ExamWithTopics | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [quizCompleted, setQuizCompleted] = useState(false);
    const [quizScore, setQuizScore] = useState<{ score: number; total: number } | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editorContent, setEditorContent] = useState<Block[]>([]);
    const [originalContent, setOriginalContent] = useState<Block[]>([]);
    const [isSaving, setIsSaving] = useState(false);

    // Collapse sidebar when topic page loads, expand when leaving
    useEffect(() => {
        setIsCollapsed(true);
        return () => {
            setIsCollapsed(false);
            setContextualNav(null);
        };
    }, [setIsCollapsed, setContextualNav]);

    // Update contextual nav when exam or topic changes
    useEffect(() => {
        if (exam && exam.topics && exam.topics.length > 0) {
            const topics = exam.topics;
            const completedCount = topics.filter(t => t.quiz_completed === true).length;
            const progressPercent = topics.length > 0 ? (completedCount / topics.length) * 100 : 0;

            setContextualNav({
                title: 'Exam Topics',
                progress: progressPercent,
                items: topics.map(t => ({
                    id: t.id,
                    name: t.topic_name,
                    href: `/dashboard/topics/${t.id}`,
                    completed: t.quiz_completed === true
                }))
            });
        }
    }, [exam, setContextualNav]);

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

            // Initialize quiz completion state from backend
            setQuizCompleted(topicData.quiz_completed || false);

            // Convert content to BlockNote format
            let blocks: Block[];
            if (topicData.content_blocknote) {
                // Use existing BlockNote content
                blocks = topicData.content_blocknote as Block[];
            } else if (topicData.content) {
                // Convert Markdown to BlockNote
                blocks = await markdownToBlockNote(topicData.content);
            } else {
                blocks = [];
            }

            // Add MCQ block at the end if content exists
            if (blocks.length > 0 && topicData.content) {
                blocks.push({
                    type: 'mcq',
                    props: {
                        topicId: topicId,
                        examId: topicData.exam_id,
                        quizCompleted: topicData.quiz_completed || false,
                    },
                    id: `mcq-${topicId}`,
                    content: [],
                } as any); // Cast to any since this is a custom block type
            }

            setEditorContent(blocks);
            setOriginalContent(blocks);

            // Load exam with topics for sidebar
            const examData = await examsApi.getById(topicData.exam_id);
            setExam(examData);

            // Mark topic as viewed
            try {
                await topicsApi.markAsViewed(topicId, topicData.exam_id);
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
                await topicsApi.markAsViewed(topicId, topic.exam_id, true);
            } catch (err) {
                console.error('Failed to mark quiz as completed:', err);
            }
        }
    };

    const handleQuizSkip = () => {
        setQuizCompleted(true);
    };

    const handleSaveContent = async () => {
        if (!topic) return;

        try {
            setIsSaving(true);

            // Convert BlockNote content to Markdown
            const markdown = blockNoteToMarkdown(editorContent);

            // Save both formats
            const updatedTopic = await topicsApi.updateTopicContent(
                topicId,
                editorContent,
                markdown
            );

            setTopic(updatedTopic);
            setOriginalContent(editorContent);
            setIsEditing(false);
            toast.success('Content saved successfully');
        } catch (error) {
            console.error('Failed to save content:', error);
            toast.error('Failed to save content. Please try again.');
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancelEdit = () => {
        setEditorContent(originalContent);
        setIsEditing(false);
    };

    const handleContentChange = (blocks: Block[]) => {
        setEditorContent(blocks);

        // Check if MCQ block was marked as completed
        const mcqBlock = blocks.find((b) => (b.type as string) === 'mcq');
        if (mcqBlock && mcqBlock.props && (mcqBlock.props as any).quizCompleted) {
            if (!quizCompleted) {
                console.log('Quiz completion detected from editor');
                setQuizCompleted(true);
            }
        }
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
        <div className="flex h-[calc(100vh-3.5rem)] sm:h-[calc(100vh-4rem)] overflow-hidden bg-background">
            {/* Left Sidebar - Topic Navigation */}
            <TopicSidebar
                exam={exam}
                currentTopicId={topicId}
                className="hidden lg:flex"
            />

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto w-full">
                <div className="container max-w-5xl py-4 sm:py-8 px-3 sm:px-6 lg:px-8 mx-auto">
                    {/* Minimal Breadcrumbs - hidden on mobile */}
                    <div className="hidden sm:flex mb-6 items-center text-sm text-muted-foreground/60">
                        <Breadcrumbs items={breadcrumbItems} className="mb-0 text-xs uppercase tracking-wider font-medium" />
                    </div>

                    {/* Topic Header - Optimized for mobile */}
                    <div className="mb-6 sm:mb-10 border-b border-border/40 pb-4 sm:pb-6">
                        <div className="flex items-start justify-between gap-2 sm:gap-4 mb-3 sm:mb-4">
                            <h1 className="text-xl sm:text-3xl lg:text-4xl font-bold tracking-tight text-foreground leading-tight">
                                {topic.topic_name}
                            </h1>

                            {/* Edit/Save/Cancel Buttons */}
                            <div className="flex items-center gap-1 sm:gap-2 shrink-0">
                                {!isEditing ? (
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setIsEditing(true)}
                                        className="gap-1 sm:gap-2 px-2 sm:px-3"
                                    >
                                        <Edit className="h-4 w-4" />
                                        <span className="hidden sm:inline">Edit</span>
                                    </Button>
                                ) : (
                                    <>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={handleCancelEdit}
                                            className="gap-1 sm:gap-2 px-2 sm:px-3"
                                            disabled={isSaving}
                                        >
                                            <X className="h-4 w-4" />
                                            <span className="hidden sm:inline">Cancel</span>
                                        </Button>
                                        <Button
                                            variant="default"
                                            size="sm"
                                            onClick={handleSaveContent}
                                            className="gap-1 sm:gap-2 px-2 sm:px-3"
                                            disabled={isSaving}
                                        >
                                            <Save className="h-4 w-4" />
                                            <span className="hidden sm:inline">{isSaving ? 'Saving...' : 'Save'}</span>
                                        </Button>
                                    </>
                                )}
                            </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-3 sm:gap-6 text-xs sm:text-sm text-muted-foreground">
                            <div className="flex items-center gap-1.5 sm:gap-2">
                                <Clock className="h-3.5 w-3.5 sm:h-4 sm:w-4 opacity-70" />
                                <span>~{topic.estimated_study_minutes || 5} min</span>
                            </div>
                            <div className="flex items-center gap-1.5 sm:gap-2">
                                <BarChart3 className="h-3.5 w-3.5 sm:h-4 sm:w-4 opacity-70" />
                                <span>Level {topic.difficulty_level}/3</span>
                            </div>
                            <div className="ml-auto text-[10px] sm:text-xs font-mono opacity-50">
                                {currentIndex + 1}/{topics.length}
                            </div>
                        </div>
                    </div>

                    {/* Onboarding Banner */}
                    <div className="mb-6">
                        <Alert className="bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800">
                            <Brain className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                            <AlertTitle className="text-blue-800 dark:text-blue-300">Ready to focus?</AlertTitle>
                            <AlertDescription className="text-blue-600 dark:text-blue-400 mt-1">
                                Start a study session from the timer 🧠 in the header to track your progress and breaks.
                            </AlertDescription>
                        </Alert>
                    </div>

                    {/* Topic Content - BlockNote Editor */}
                    <div className="mb-8 sm:mb-12 -mx-1 sm:mx-0">
                        {editorContent.length > 0 ? (
                            <BlockNoteEditor
                                topicId={topicId}
                                initialContent={editorContent}
                                editable={isEditing}
                                onChange={handleContentChange}
                            />
                        ) : (
                            <div className="p-12 text-center border border-dashed rounded-lg bg-muted/20">
                                <p className="text-muted-foreground">
                                    No content available for this topic yet.
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Check Yourself Quiz - Removed since MCQ is now in BlockNote */}

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

            {/* Mobile AI Tutor - Floating button + Bottom sheet */}
            <MobileAiTutor topicId={topicId} />
        </div>
    );
}
