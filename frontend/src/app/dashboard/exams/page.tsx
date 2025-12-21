'use client';

import { useExams } from '@/lib/hooks/use-exams';
import { Button } from '@/components/ui/button';
import { Plus, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ExamCard } from '@/components/exam/exam-card';
import { Card } from '@/components/ui/card';
import { useState } from 'react';
import type { Exam } from '@/lib/api/exams';
import { MoveToCourseModal } from '@/components/modals/move-to-course-modal';

export default function ExamsPage() {
    const router = useRouter();
    const { exams, isLoading, deleteExam } = useExams();
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedExam, setSelectedExam] = useState<Exam | null>(null);
    const [isMoveModalOpen, setIsMoveModalOpen] = useState(false);

    const filteredExams = exams?.filter((exam: Exam) =>
        exam.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        exam.subject?.toLowerCase().includes(searchQuery.toLowerCase())
    ) || [];

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">My Exams</h1>
                    <p className="mt-2 text-muted-foreground">
                        Manage and track all your exam preparations
                    </p>
                </div>
                <Link href="/dashboard/exams/new">
                    <Button>
                        <Plus className="mr-2 h-4 w-4" />
                        New Exam
                    </Button>
                </Link>
            </div>

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                    placeholder="Search exams..."
                    className="pl-10"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            {/* Exams Grid */}
            {isLoading ? (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                        <Card key={i} className="p-6 animate-pulse">
                            <div className="h-6 bg-muted rounded mb-4" />
                            <div className="h-4 bg-muted rounded w-2/3 mb-2" />
                            <div className="h-4 bg-muted rounded w-1/2" />
                        </Card>
                    ))}
                </div>
            ) : filteredExams.length > 0 ? (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {filteredExams.map((exam: Exam) => (
                        <ExamCard
                            key={exam.id}
                            exam={exam}
                            totalTopics={exam.topic_count}
                            completedTopics={exam.completed_topics}
                            dueFlashcards={exam.due_flashcards_count}
                            onPressReview={() => {
                                router.push(`/dashboard/flashcards/${exam.id}`);
                            }}
                            onPressLearn={() => {
                                router.push(`/dashboard/exams/${exam.id}`);
                            }}
                            onDelete={() => {
                                if (window.confirm('Are you sure you want to delete this exam? This action cannot be undone.')) {
                                    deleteExam(exam.id);
                                }
                            }}
                            onMoveToCourse={() => {
                                setSelectedExam(exam);
                                setIsMoveModalOpen(true);
                            }}
                        />
                    ))}
                </div>
            ) : exams && exams.length > 0 ? (
                <Card className="p-12 text-center">
                    <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-foreground mb-2">
                        No exams found
                    </h3>
                    <p className="text-muted-foreground">
                        Try adjusting your search query
                    </p>
                </Card>
            ) : (
                <Card className="p-12 text-center">
                    <h3 className="text-lg font-medium text-foreground mb-2">
                        No exams yet
                    </h3>
                    <p className="text-muted-foreground mb-6">
                        Get started by creating your first exam
                    </p>
                    <Link href="/dashboard/exams/new">
                        <Button>
                            <Plus className="mr-2 h-4 w-4" />
                            Create Your First Exam
                        </Button>
                    </Link>
                </Card>
            )}

            <MoveToCourseModal
                exam={selectedExam}
                isOpen={isMoveModalOpen}
                onClose={() => {
                    setIsMoveModalOpen(false);
                    setSelectedExam(null);
                }}
            />
        </div>
    );
}
