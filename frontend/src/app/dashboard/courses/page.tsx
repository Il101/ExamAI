'use client';

import { useCourses } from '@/lib/hooks/use-courses';
import { CourseList } from '@/components/course/CourseList';
import { CreateCourseModal } from '@/components/modals/create-course-modal';
import { useState } from 'react';
import { FolderPlus, Search, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import Link from 'next/link';

export default function CoursesPage() {
    const { courses, isLoading } = useCourses();
    const [isCourseModalOpen, setIsCourseModalOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    const filteredCourses = courses?.filter(course =>
        course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        course.subject.toLowerCase().includes(searchQuery.toLowerCase())
    ) || [];

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <Link href="/dashboard" className="text-muted-foreground hover:text-primary transition-colors">
                            <ArrowLeft className="h-4 w-4" />
                        </Link>
                        <h1 className="text-3xl font-bold text-foreground">My Courses</h1>
                    </div>
                    <p className="text-muted-foreground">
                        Organize your exams into courses and semesters
                    </p>
                </div>
                <Button
                    onClick={() => setIsCourseModalOpen(true)}
                    className="h-10 px-4 font-bold"
                >
                    <FolderPlus className="h-4 w-4 mr-2" />
                    New Course
                </Button>
            </div>

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                    placeholder="Search courses..."
                    className="pl-10"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            {/* Courses List */}
            <CourseList
                courses={filteredCourses}
                isLoading={isLoading}
                onCourseClick={(id) => window.location.href = `/dashboard/courses/${id}`}
                onCreateClick={() => setIsCourseModalOpen(true)}
            />

            <CreateCourseModal
                isOpen={isCourseModalOpen}
                onClose={() => setIsCourseModalOpen(false)}
            />
        </div>
    );
}
