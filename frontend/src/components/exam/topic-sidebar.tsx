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
            return <BookOpen className="h-4 w-4 text-primary animate-pulse" />;
        }
        if (topic.status === 'ready') {
            return <CheckCircle2 className="h-4 w-4 text-green-600/80" />;
        }
        return <Circle className="h-4 w-4 text-muted-foreground/30" />;
    };

    if (collapsed) {
        return (
            <div className={cn('w-12 bg-background border-r border-border/40 flex flex-col items-center py-4', className)}>
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setCollapsed(false)}
                    className="mb-4 h-8 w-8 text-muted-foreground hover:text-foreground"
                >
                    <ChevronRight className="h-4 w-4" />
                </Button>
                <div className="flex flex-col gap-2">
                    {topics.slice(0, 5).map((topic) => (
                        <div
                            key={topic.id}
                            className={cn(
                                'h-8 w-8 rounded-md flex items-center justify-center transition-colors',
                                topic.id === currentTopicId ? 'bg-primary/10 text-primary' : 'hover:bg-muted text-muted-foreground'
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
                'w-72 bg-background border-r border-border/40 flex flex-col',
                className
            )}
        >
            {/* Header */}
            <div className="px-4 py-4 border-b border-border/30">
                <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0 pr-2">
                        <h3 className="font-semibold text-sm truncate tracking-tight text-foreground">{exam.title}</h3>
                        <p className="text-[10px] uppercase tracking-wider text-muted-foreground/70 mt-1">
                            {completedCount} of {topics.length} topics
                        </p>
                    </div>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setCollapsed(true)}
                        className="h-6 w-6 text-muted-foreground hover:text-foreground -mr-2"
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                </div>
                <Progress value={progressPercent} className="h-0.5 bg-muted" />
            </div>

            {/* Topic List */}
            <div className="flex-1 overflow-y-auto px-2 py-3">
                <div className="space-y-0.5">
                    {topics.map((topic, index) => {
                        const isActive = topic.id === currentTopicId;

                        return (
                            <Link
                                key={topic.id}
                                href={`/dashboard/topics/${topic.id}`}
                                className={cn(
                                    'flex items-start gap-3 px-3 py-2.5 rounded-md text-sm transition-all duration-200 group',
                                    isActive
                                        ? 'bg-muted/50 text-foreground font-medium shadow-sm ring-1 ring-border/50'
                                        : 'text-muted-foreground hover:bg-muted/30 hover:text-foreground'
                                )}
                            >
                                <div className="pt-0.5 flex-shrink-0 opacity-70 group-hover:opacity-100 transition-opacity">
                                    {getTopicIcon(topic)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-0.5">
                                        <span className={cn(
                                            "truncate text-[13px]",
                                            isActive && "text-primary"
                                        )}>{topic.topic_name}</span>
                                    </div>
                                </div>
                            </Link>
                        );
                    })}
                </div>
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-border/30 bg-muted/5">
                <Link href={`/dashboard/exams/${exam.id}`}>
                    <Button variant="ghost" size="sm" className="w-full text-xs text-muted-foreground hover:text-foreground justify-start px-2">
                        <ChevronLeft className="h-3 w-3 mr-2" />
                        Back to Exam Overview
                    </Button>
                </Link>
            </div>
        </aside>
    );
}
