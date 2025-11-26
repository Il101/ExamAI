'use client';

import { useQuery } from '@tanstack/react-query';
import { examsApi, ExamWithTopics } from '@/lib/api/exams';

export function useExamDetail(examId: string) {
    const examQuery = useQuery({
        queryKey: ['exam', examId],
        queryFn: () => examsApi.getById(examId),
        enabled: !!examId,
    });

    const exam = examQuery.data as ExamWithTopics | undefined;
    const shouldPoll = exam && ['generating', 'planned'].includes(exam.status);

    const statusQuery = useQuery({
        queryKey: ['exam-status', examId],
        queryFn: () => examsApi.getGenerationStatus(examId),
        enabled: !!shouldPoll,
        refetchInterval: 2000,
    });

    // Merge status data into exam if available
    const mergedExam = exam ? {
        ...exam,
        status: (statusQuery.data?.status as any) || exam.status,
        progress: statusQuery.data?.progress || 0,
        current_step: statusQuery.data?.current_step || '',
        message: statusQuery.data?.message || '',
    } : undefined;

    return {
        exam: mergedExam,
        isLoading: examQuery.isLoading,
        isError: examQuery.isError,
        error: examQuery.error,
        refetch: examQuery.refetch,
    };
}
