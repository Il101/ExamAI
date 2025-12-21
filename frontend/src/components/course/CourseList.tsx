'use client';

import { Course } from '@/lib/api/courses';
import { CourseCard } from './CourseCard';
import { Plus, FolderPlus } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface CourseListProps {
    courses: Course[];
    isLoading?: boolean;
    onCourseClick?: (courseId: string) => void;
    onCreateClick?: () => void;
}

export function CourseList({ courses, isLoading, onCourseClick, onCreateClick }: CourseListProps) {
    if (isLoading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="h-64 rounded-xl bg-muted/20 animate-pulse border border-border/40" />
                ))}
            </div>
        );
    }

    if (courses.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center rounded-2xl border-2 border-dashed border-border/40 bg-muted/5">
                <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                    <FolderPlus className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-bold text-foreground mb-2">No courses yet</h3>
                <p className="text-muted-foreground max-w-sm mb-6">
                    Create a course to organize your exams by semester or subject.
                </p>
                <Button onClick={onCreateClick} className="font-bold">
                    <Plus className="h-4 w-4 mr-2" />
                    Create First Course
                </Button>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map((course) => (
                <CourseCard key={course.id} course={course} onClick={onCourseClick} />
            ))}
        </div>
    );
}
