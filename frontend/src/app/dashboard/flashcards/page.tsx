'use client';

import { useExams } from '@/lib/hooks/use-exams';
import { Card } from '@/components/ui/card';
import { Loader2, Search, Book, ArrowRight, Brain } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useState } from 'react';
import type { Exam } from '@/lib/api/exams';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';

export default function FlashcardsPage() {
    const { exams, isLoading } = useExams();
    const [searchQuery, setSearchQuery] = useState('');

    const filteredExams = exams?.filter((exam: Exam) =>
        exam.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        exam.subject?.toLowerCase().includes(searchQuery.toLowerCase())
    ) || [];

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-8 container max-w-5xl py-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Flashcards Library</h1>
                    <p className="text-muted-foreground mt-2">
                        Browse your exams and topics to start reviewing.
                    </p>
                </div>
            </div>

            {/* Search */}
            <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                    placeholder="Search your subjects..."
                    className="pl-10"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            {/* Exams Grid */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {filteredExams.map((exam: Exam) => (
                    <Link key={exam.id} href={`/dashboard/flashcards/${exam.id}`} className="group">
                        <Card className="h-full p-6 transition-all hover:shadow-lg hover:border-primary/50 cursor-pointer">
                            <div className="flex flex-col h-full space-y-4">
                                <div className="flex items-start justify-between">
                                    <div className="p-3 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-colors">
                                        <Book className="h-6 w-6 text-primary" />
                                    </div>
                                    <Badge variant={(exam.status === 'ready' ? 'default' : 'secondary')}>
                                        {exam.status === 'ready' ? 'Ready to Study' : exam.status}
                                    </Badge>
                                </div>

                                <div>
                                    <h3 className="font-semibold text-lg line-clamp-1">{exam.title}</h3>
                                    <p className="text-sm text-muted-foreground line-clamp-1">{exam.subject || 'General'}</p>
                                </div>

                                <div className="mt-auto pt-4 border-t flex items-center justify-between text-sm text-muted-foreground">
                                    <div className="flex items-center gap-2">
                                        <Brain className="h-4 w-4" />
                                        <span>{exam.topic_count} Topics</span>
                                    </div>
                                    <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform text-primary" />
                                </div>
                            </div>
                        </Card>
                    </Link>
                ))}

                {filteredExams.length === 0 && (
                    <div className="col-span-full text-center py-12">
                        <p className="text-muted-foreground">No exams found matching your search.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
