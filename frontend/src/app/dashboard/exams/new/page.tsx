'use client';

import { Card } from '@/components/ui/card';
import { CreateExamForm } from '@/components/exam/create-exam-form';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { useRouter, useSearchParams } from 'next/navigation';
import { useCourse } from '@/lib/hooks/use-courses';
import { Suspense } from 'react';

export default function NewExamPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <NewExamContent />
        </Suspense>
    );
}

function NewExamContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const courseId = searchParams.get('course_id');
    const { data: course } = useCourse(courseId || '');

    const handleSuccess = () => {
        if (courseId) {
            router.push(`/dashboard/courses/${courseId}`);
        } else {
            router.push('/dashboard/exams');
        }
    };

    return (
        <div className="max-w-3xl mx-auto space-y-8">
            {/* Header */}
            <div>
                <Link href={courseId ? `/dashboard/courses/${courseId}` : "/dashboard/exams"}>
                    <Button variant="ghost" className="mb-4">
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Back to {courseId ? 'Course' : 'Exams'}
                    </Button>
                </Link>
                <h1 className="text-3xl font-bold text-foreground">
                    Create New Exam {course ? `for ${course.title}` : ''}
                </h1>
                <p className="mt-2 text-muted-foreground">
                    Upload your study materials and let AI generate personalized exam content
                </p>
            </div>

            {/* Form */}
            <Card className="p-8">
                <CreateExamForm onSuccess={handleSuccess} initialCourseId={courseId} />
            </Card>
        </div>
    );
}
