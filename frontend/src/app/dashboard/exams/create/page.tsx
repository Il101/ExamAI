'use client';

import { CreateExamForm } from '@/components/exam/create-exam-form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useRouter } from 'next/navigation';

export default function CreateExamPage() {
  const router = useRouter();

  return (
    <div className="max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Create New Exam</CardTitle>
          <CardDescription>
            Upload your study materials or paste content to generate a personalized exam plan.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CreateExamForm onSuccess={() => router.push('/dashboard')} />
        </CardContent>
      </Card>
    </div>
  );
}
