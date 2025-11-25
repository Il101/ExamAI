'use client';

import { useQuery } from '@tanstack/react-query';
import { examsApi, ExamWithTopics } from '@/lib/api/exams';

export function useExamDetail(examId: string) {
    const examQuery = useQuery({
        queryKey: ['exam', examId],
        queryFn: () => examsApi.getById(examId),
        enabled: !!examId,
        refetchInterval: (data) => {
            if (!data) return false;
            // Poll if generating or if we just started planning (status might still be draft/generating)
            const exam = data as unknown as ExamWithTopics;
            return ['generating', 'planned'].includes(exam.status) ? 2000 : false;
        },
    });

    return {
        exam: examQuery.data as ExamWithTopics | undefined,
        isLoading: examQuery.isLoading,
        isError: examQuery.isError,
        error: examQuery.error,
        refetch: examQuery.refetch,
    };
}
