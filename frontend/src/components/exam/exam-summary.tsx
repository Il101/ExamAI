'use client';

import { Exam } from '@/lib/api/exams';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calendar, FileText, ArrowRight, BookOpen } from 'lucide-react';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';

interface ExamSummaryProps {
    exam: Exam;
}

export function ExamSummary({ exam }: ExamSummaryProps) {
    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            <Card className="border-2 border-primary/10 shadow-lg">
                <CardHeader className="bg-gradient-to-r from-primary/5 to-transparent pb-8">
                    <div className="flex items-start justify-between">
                        <div className="space-y-2">
                            <Badge variant="outline" className="mb-2 bg-background">
                                {exam.subject}
                            </Badge>
                            <CardTitle className="text-3xl font-bold text-primary">
                                {exam.title}
                            </CardTitle>
                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                <div className="flex items-center gap-1">
                                    <Calendar className="h-4 w-4" />
                                    {format(new Date(exam.created_at), 'PPP')}
                                </div>
                                <div className="flex items-center gap-1">
                                    <BookOpen className="h-4 w-4" />
                                    {exam.level}
                                </div>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-2xl font-bold">{exam.topic_count}</div>
                            <div className="text-xs text-muted-foreground uppercase tracking-wider">Topics</div>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="pt-8">
                    <div className="prose prose-slate dark:prose-invert max-w-none">
                        <h3 className="flex items-center gap-2 text-xl font-semibold mb-4">
                            <FileText className="h-5 w-5 text-primary" />
                            AI Summary
                        </h3>
                        {exam.ai_summary ? (
                            <ReactMarkdown>{exam.ai_summary}</ReactMarkdown>
                        ) : (
                            <p className="text-muted-foreground italic">
                                No summary available. This might be because the exam was created without AI generation or is still processing.
                            </p>
                        )}
                    </div>


                </CardContent>
            </Card>

            {/* Celebration Animation Placeholder - In a real app, this would be a Lottie animation or similar */}
            <div className="fixed inset-0 pointer-events-none flex items-center justify-center z-50 opacity-0 animate-fade-in-out">
                <div className="bg-background/80 backdrop-blur-sm p-8 rounded-2xl shadow-2xl border transform scale-110">
                    <div className="text-center">
                        <div className="text-6xl mb-4">🎉</div>
                        <h2 className="text-2xl font-bold mb-2">Summary Ready!</h2>
                        <p className="text-muted-foreground">Your study material has been analyzed.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
