'use client';

import { useQuery } from '@tanstack/react-query';
import { examsApi, ExamWithTopics } from '@/lib/api/exams';
import { useEffect } from 'react';

export function useExamDetail(examId: string) {
    const examQuery = useQuery({
        queryKey: ['exam', examId],
        queryFn: async () => {
            console.log('[useExamDetail] Fetching exam:', examId);
            const data = await examsApi.getById(examId);
            console.log('[useExamDetail] Received data:', data);
            return data;
        },
        enabled: !!examId,
        retry: 2,
        staleTime: 0,
        refetchOnMount: true,
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

    useEffect(() => {
        console.log('[useExamDetail] State:', {
            isLoading: examQuery.isLoading,
            isError: examQuery.isError,
            error: examQuery.error,
            hasData: !!exam,
            status: exam?.status,
        });
    }, [examQuery.isLoading, examQuery.isError, examQuery.error, exam]);

    return {
        exam: mergedExam,
        isLoading: examQuery.isLoading,
        isError: examQuery.isError,
        error: examQuery.error,
        refetch: examQuery.refetch,
    };
}
