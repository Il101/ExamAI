'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { cn } from '@/lib/utils';
import { ExamWithTopics } from '@/lib/api/exams';
import { ChevronLeft, ChevronRight, CheckCircle2, BookOpen, Circle, RotateCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

interface TopicSidebarProps {
    exam: ExamWithTopics;
    currentTopicId?: string;
    className?: string;
}

export function TopicSidebar({ exam, currentTopicId, className }: TopicSidebarProps) {
    const [collapsed, setCollapsed] = useState(false);
    const params = useParams();

    const topics = exam.topics || [];
    const completedCount = topics.filter(t => t.status === 'ready').length;
    const progressPercent = topics.length > 0 ? (completedCount / topics.length) * 100 : 0;

    const getTopicIcon = (topic: any) => {
        // For now, using simple status-based icons
        // Could be enhanced with actual completion tracking
        if (topic.id === currentTopicId) {
            return <BookOpen className="h-4 w-4 text-primary" />;
        }
        if (topic.status === 'ready') {
            return <CheckCircle2 className="h-4 w-4 text-green-600" />;
        }
        return <Circle className="h-4 w-4 text-muted-foreground" />;
    };

    if (collapsed) {
        return (
            <div className={cn('w-12 border-r bg-muted/30 flex flex-col items-center py-4', className)}>
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setCollapsed(false)}
                    className="mb-4"
                >
                    <ChevronRight className="h-4 w-4" />
                </Button>
                <div className="flex flex-col gap-2">
                    {topics.slice(0, 5).map((topic) => (
                        <div
                            key={topic.id}
                            className={cn(
                                'h-8 w-8 rounded-md flex items-center justify-center',
                                topic.id === currentTopicId ? 'bg-primary/10' : 'hover:bg-muted'
                            )}
                        >
                            {getTopicIcon(topic)}
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <aside
            className={cn(
                'w-64 border-r bg-muted/30 flex flex-col',
                className
            )}
        >
            {/* Header */}
            <div className="p-4 border-b">
                <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-sm truncate">{exam.title}</h3>
                        <p className="text-xs text-muted-foreground">
                            {completedCount} of {topics.length} topics
                        </p>
                    </div>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setCollapsed(true)}
                        className="h-8 w-8 flex-shrink-0"
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                </div>
                <Progress value={progressPercent} className="h-1" />
            </div>

            {/* Topic List */}
            <div className="flex-1 overflow-y-auto p-2">
                <div className="space-y-1">
                    {topics.map((topic, index) => {
                        const isActive = topic.id === currentTopicId;

                        return (
                            <Link
                                key={topic.id}
                                href={`/dashboard/topics/${topic.id}`}
                                className={cn(
                                    'flex items-start gap-2 p-2 rounded-md text-sm transition-colors',
                                    'hover:bg-accent',
                                    isActive && 'bg-primary/10 text-primary font-medium'
                                )}
                            >
                                <div className="pt-0.5 flex-shrink-0">
                                    {getTopicIcon(topic)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-1 mb-0.5">
                                        <span className="text-xs text-muted-foreground">
                                            {index + 1}.
                                        </span>
                                        <span className="truncate">{topic.topic_name}</span>
                                    </div>
                                    {topic.estimated_study_minutes && (
                                        <span className="text-xs text-muted-foreground">
                                            ~{topic.estimated_study_minutes} min
                                        </span>
                                    )}
                                </div>
                            </Link>
                        );
                    })}
                </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t">
                <Link href={`/dashboard/exams/${exam.id}`}>
                    <Button variant="outline" size="sm" className="w-full">
                        Back to Exam
                    </Button>
                </Link>
            </div>
        </aside>
    );
}
