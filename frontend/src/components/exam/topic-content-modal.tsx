'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { topicsApi, Topic } from '@/lib/api/topics';
import { Loader2, BookOpen } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AiTutorChat } from './ai-tutor-chat';
import { Badge } from '@/components/ui/badge';

interface TopicContentModalProps {
    topicId: string | null;
    topicName?: string;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function TopicContentModal({ topicId, topicName, open, onOpenChange }: TopicContentModalProps) {
    const [topic, setTopic] = useState<Topic | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (open && topicId) {
            loadTopic();
        }
    }, [open, topicId]);

    const loadTopic = async () => {
        if (!topicId) return;

        setIsLoading(true);
        setError(null);

        try {
            const data = await topicsApi.getById(topicId);
            setTopic(data);
        } catch (err) {
            console.error('Failed to load topic:', err);
            setError('Failed to load topic content. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl max-h-[90vh] p-0">
                <DialogHeader className="px-6 pt-6 pb-4 border-b">
                    <div className="flex items-start gap-3">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                            <BookOpen className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1">
                            <DialogTitle className="text-2xl font-bold">
                                {topic?.topic_name || topicName || 'Topic Content'}
                            </DialogTitle>
                            {topic && (
                                <div className="flex items-center gap-2 mt-2">
                                    <Badge variant="secondary" className="text-xs">
                                        ~{topic.estimated_study_minutes} min read
                                    </Badge>
                                    <Badge variant="outline" className="text-xs">
                                        Difficulty: {topic.difficulty_level}/3
                                    </Badge>
                                </div>
                            )}
                        </div>
                    </div>
                </DialogHeader>

                <div className="flex-1 px-6 py-4 overflow-auto" style={{ maxHeight: 'calc(90vh - 200px)' }}>
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        </div>
                    ) : error ? (
                        <div className="text-center py-12">
                            <p className="text-destructive">{error}</p>
                        </div>
                    ) : topic ? (
                        <div className="space-y-6">
                            {/* Topic Content */}
                            <div className="prose prose-slate dark:prose-invert max-w-none">
                                {topic.content ? (
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {topic.content}
                                    </ReactMarkdown>
                                ) : (
                                    <p className="text-muted-foreground italic">
                                        No content available for this topic yet.
                                    </p>
                                )}
                            </div>

                            {/* AI Tutor Chat */}
                            {topic.content && (
                                <div className="border-t pt-6">
                                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                        💬 Ask AI Tutor
                                    </h3>
                                    <AiTutorChat topicId={topic.id} />
                                </div>
                            )}
                        </div>
                    ) : null}
                </div>
            </DialogContent>
        </Dialog>
    );
}
