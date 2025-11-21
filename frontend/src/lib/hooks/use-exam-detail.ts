'use client';

import { useQuery } from '@tanstack/react-query';
import { examsApi, ExamWithTopics } from '@/lib/api/exams';

export function useExamDetail(examId: string) {
    const examQuery = useQuery({
        queryKey: ['exam', examId],
        queryFn: () => examsApi.getById(examId),
        enabled: !!examId,
    });

    return {
        exam: examQuery.data as ExamWithTopics | undefined,
        isLoading: examQuery.isLoading,
        isError: examQuery.isError,
        error: examQuery.error,
        refetch: examQuery.refetch,
    };
}
