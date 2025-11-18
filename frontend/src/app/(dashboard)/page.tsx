'use client';

import { useExams } from '@/lib/hooks/use-exams';
import { ExamCard } from '@/components/exam/exam-card';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import Link from 'next/link';
import { Exam } from '@/lib/api/exams';

export default function DashboardPage() {
  const { exams, isLoading, deleteExam } = useExams();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">
            Manage your exams and study materials.
          </p>
        </div>
        <Link href="/exams/create">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Exam
          </Button>
        </Link>
      </div>

      {exams.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed rounded-lg">
          <h3 className="text-lg font-medium text-gray-900">No exams yet</h3>
          <p className="text-gray-500 mt-1">Get started by creating your first exam.</p>
          <Link href="/exams/create" className="mt-4 inline-block">
            <Button variant="outline">Create Exam</Button>
          </Link>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {exams.map((exam: Exam) => (
            <ExamCard
              key={exam.id}
              exam={exam}
              onDelete={() => {
                if (confirm('Are you sure you want to delete this exam?')) {
                  deleteExam(exam.id);
                }
              }}
              onGenerate={() => {
                // Handle generation start
                console.log('Generate', exam.id);
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
