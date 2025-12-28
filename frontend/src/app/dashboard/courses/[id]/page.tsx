'use client';

import { useParams, useRouter } from 'next/navigation';
import { useCourse, useCourseExams } from '@/lib/hooks/use-courses';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
    ArrowLeft,
    Folder,
    Book,
    Brain,
    Clock,
    Plus,
    Settings,
    Calendar
} from 'lucide-react';
import { format } from 'date-fns';
import { EditCourseModal } from '@/components/modals/edit-course-modal';
import { useState } from 'react';
import { ExamCard } from '@/components/exam/exam-card';

export default function CourseDetailPage() {
    const { id } = useParams();
    const router = useRouter();
    const { data: course, isLoading: isLoadingCourse } = useCourse(id as string);
    const { data: exams, isLoading: isLoadingExams } = useCourseExams(id as string);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);

    if (isLoadingCourse) {
        return (
            <div className="space-y-8 animate-pulse">
                <div className="h-10 w-48 bg-muted rounded" />
                <div className="h-32 bg-muted rounded-2xl" />
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map(i => <div key={i} className="h-64 bg-muted rounded-xl" />)}
                </div>
            </div>
        );
    }

    if (!course) {
        return (
            <div className="flex flex-col items-center justify-center py-20 text-center">
                <h2 className="text-2xl font-bold mb-2">Course not found</h2>
                <Button onClick={() => router.push('/dashboard')}>Back to Dashboard</Button>
            </div>
        );
    }

    const stats = course.stats || {
        exam_count: 0,
        topic_count: 0,
        completed_topics: 0,
        due_flashcards_count: 0,
        total_actual_study_minutes: 0,
        total_planned_study_minutes: 0,
        average_difficulty: 0,
    };

    const progress = stats.topic_count > 0 ? (stats.completed_topics / stats.topic_count) * 100 : 0;

    const formatMinutes = (mins: number) => {
        if (mins <= 0) return '0m';
        if (mins < 60) return `${mins}m`;
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        return m > 0 ? `${h}h ${m}m` : `${h}h`;
    };

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col gap-4">
                <Button
                    variant="ghost"
                    size="sm"
                    className="-ml-2 text-muted-foreground hover:text-foreground w-fit"
                    onClick={() => router.push('/dashboard')}
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Dashboard
                </Button>

                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 mb-1">
                            <Folder className="h-5 w-5 text-primary" />
                            <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Course Folder</span>
                        </div>
                        <h1 className="text-4xl font-extrabold text-foreground tracking-tight">{course.title}</h1>
                        <p className="text-lg text-muted-foreground font-medium">{course.subject}</p>
                    </div>

                    <div className="flex gap-3">
                        <Button
                            variant="outline"
                            className="font-bold border-white/10 hover:bg-white/5"
                            onClick={() => setIsEditModalOpen(true)}
                        >
                            <Settings className="h-4 w-4 mr-2" />
                            Settings
                        </Button>
                        <Button
                            variant="default"
                            className="font-bold"
                            onClick={() => router.push(`/dashboard/exams/new?course_id=${course.id}`)}
                        >
                            <Plus className="h-4 w-4 mr-2" />
                            Add Exam
                        </Button>
                    </div>
                </div>
            </div>

            {/* Course Stats Card */}
            <Card className="border-border bg-card/40 backdrop-blur-xl overflow-hidden shadow-sm">
                <CardContent className="p-0">
                    <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-border/20">
                        {/* Overall Progress */}
                        <div className="p-4 flex flex-col justify-center border-b md:border-b-0 space-y-2 col-span-2 md:col-span-1">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase">
                                    <Book className="h-3.5 w-3.5" />
                                    <span>Progress</span>
                                </div>
                                <span className="text-lg font-black text-foreground">{Math.round(progress)}%</span>
                            </div>
                            <Progress value={progress} className="h-2 bg-muted/20" />
                            <div className="flex justify-between text-[10px] text-muted-foreground">
                                <span>{stats.completed_topics}/{stats.topic_count} topics</span>
                                <span>{stats.exam_count} exams</span>
                            </div>
                        </div>

                        {/* Time Stats */}
                        <div className="p-4 flex flex-col justify-center border-b md:border-b-0">
                            <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase mb-1">
                                <Clock className="h-3.5 w-3.5" />
                                <span>Study Time</span>
                            </div>
                            <div className="flex items-baseline gap-1.5">
                                <span className="text-lg font-bold text-foreground">{formatMinutes(stats.total_actual_study_minutes)}</span>
                                <span className="text-[10px] text-muted-foreground">/ {formatMinutes(stats.total_planned_study_minutes)}</span>
                            </div>
                        </div>

                        {/* Review Stats */}
                        <div className="p-4 flex flex-col justify-center border-l border-b md:border-b-0">
                            <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase mb-1">
                                <Brain className="h-3.5 w-3.5" />
                                <span>Review</span>
                            </div>
                            {stats.due_flashcards_count > 0 ? (
                                <Badge className="bg-orange-500/10 text-orange-500 border-none hover:bg-orange-500/20 py-0 text-[10px] h-5">
                                    {stats.due_flashcards_count} cards
                                </Badge>
                            ) : (
                                <span className="text-[10px] font-medium text-emerald-500">Up to date</span>
                            )}
                        </div>

                        {/* Difficulty & Semester */}
                        <div className="p-4 flex flex-col justify-center">
                            <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase mb-1">
                                <Calendar className="h-3.5 w-3.5" />
                                <span>Range</span>
                            </div>
                            <div className="text-[10px] font-medium truncate">
                                {course.semester_start ? format(new Date(course.semester_start), 'MMM yy') : 'No date'}
                                {' - '}
                                {course.semester_end ? format(new Date(course.semester_end), 'MMM yy') : 'TBD'}
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Exams in Course */}
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-foreground">Exams & Materials</h2>
                </div>

                {isLoadingExams ? (
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {[1, 2, 3].map(i => <div key={i} className="h-64 bg-muted/20 animate-pulse rounded-xl border border-border/40" />)}
                    </div>
                ) : exams && exams.length > 0 ? (
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {exams.map(exam => (
                            <ExamCard
                                key={exam.id}
                                exam={exam}
                                totalTopics={exam.topic_count}
                                completedTopics={exam.completed_topics}
                                dueFlashcards={exam.due_flashcards_count}
                                onPressLearn={() => router.push(`/dashboard/exams/${exam.id}`)}
                                onPressReview={() => router.push(`/dashboard/flashcards?exam_id=${exam.id}`)}
                            />
                        ))}
                    </div>
                ) : (
                    <Card className="p-12 text-center border-dashed border-2 border-border/40 bg-muted/5">
                        <Book className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                        <h3 className="text-lg font-bold mb-2">No exams in this course</h3>
                        <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
                            Add your first exam or study material to this course folder to start tracking progress.
                        </p>
                        <Button onClick={() => router.push(`/dashboard/exams/new?course_id=${course.id}`)} className="font-bold">
                            <Plus className="h-4 w-4 mr-2" />
                            Add First Material
                        </Button>
                    </Card>
                )}
            </div>

            <EditCourseModal
                isOpen={isEditModalOpen}
                onClose={() => setIsEditModalOpen(false)}
                course={course}
            />
        </div>
    );
}
