'use client';

import { Card } from '@/components/ui/card';
import { CreateExamForm } from '@/components/exam/create-exam-form';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';

export default function NewExamPage() {
    const router = useRouter();

    const handleSuccess = () => {
        router.push('/dashboard/exams');
    };

    return (
        <div className="max-w-3xl mx-auto space-y-8">
            {/* Header */}
            <div>
                <Link href="/dashboard/exams">
                    <Button variant="ghost" className="mb-4">
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Back to Exams
                    </Button>
                </Link>
                <h1 className="text-3xl font-bold text-foreground">Create New Exam</h1>
                <p className="mt-2 text-muted-foreground">
                    Upload your study materials and let AI generate personalized exam content
                </p>
            </div>

            {/* Form */}
            <Card className="p-8">
                <CreateExamForm onSuccess={handleSuccess} />
            </Card>
        </div>
    );
}
