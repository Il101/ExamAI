'use client';

import { ArrowLeft, Calendar, BookOpen, Play, Download } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface ExamHeaderProps {
    examId: string;
    title: string;
    subject?: string;
    status: 'draft' | 'planned' | 'generating' | 'ready' | 'failed';
    topicCount: number;
    createdAt: string;
    updatedAt: string;
}

export function ExamHeader({
    examId,
    title,
    subject,
    status,
    topicCount,
    createdAt,
    updatedAt,
}: ExamHeaderProps) {
    const statusColors = {
        draft: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
        planned: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
        generating: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
        ready: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
        failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };

    return (
        <div className="border-b pb-6 mb-6">
            <div className="flex items-center justify-between mb-4">
                <Link href="/dashboard">
                    <Button variant="ghost" size="sm">
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Back to Exams
                    </Button>
                </Link>

                <div className="flex gap-2">
                    {status === 'ready' && (
                        <>
                            <Button variant="outline" size="sm">
                                <Download className="h-4 w-4 mr-2" />
                                Export
                            </Button>
                            <Link href={`/study/session?examId=${examId}`}>
                                <Button size="sm">
                                    <Play className="h-4 w-4 mr-2" />
                                    Study Now
                                </Button>
                            </Link>
                        </>
                    )}
                </div>
            </div>

            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <h1 className="text-3xl font-bold mb-2">{title}</h1>
                    {subject && (
                        <p className="text-lg text-muted-foreground mb-3">{subject}</p>
                    )}

                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                            <BookOpen className="h-4 w-4" />
                            <span>{topicCount} {topicCount === 1 ? 'topic' : 'topics'}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            <span>Created {formatDistanceToNow(new Date(createdAt), { addSuffix: true })}</span>
                        </div>
                        {updatedAt !== createdAt && (
                            <div className="flex items-center gap-1">
                                <Calendar className="h-4 w-4" />
                                <span>Updated {formatDistanceToNow(new Date(updatedAt), { addSuffix: true })}</span>
                            </div>
                        )}
                    </div>
                </div>

                <Badge className={statusColors[status]}>
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                </Badge>
            </div>
        </div>
    );
}
