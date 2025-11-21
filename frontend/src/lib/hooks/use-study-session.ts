import { useMutation, useQueryClient } from '@tanstack/react-query';
import { studyApi } from '@/lib/api/study';
import { toast } from 'sonner';

export function useStudySession() {
    const queryClient = useQueryClient();

    const startMutation = useMutation({
        mutationFn: ({ examId, duration }: { examId: string; duration?: number }) =>
            studyApi.startSession(examId, duration),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['studySession'] });
            toast.success('Study session started!');
        },
        onError: (error: unknown) => {
            const message = error instanceof Error && 'response' in error
                ? (error as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
                : 'Failed to start session';
            toast.error(message || 'Failed to start session');
        },
    });

    const endMutation = useMutation({
        mutationFn: (sessionId: string) => studyApi.endSession(sessionId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['studySession'] });
            queryClient.invalidateQueries({ queryKey: ['analytics'] });
            toast.success('Study session completed!');
        },
        onError: (error: unknown) => {
            const message = error instanceof Error && 'response' in error
                ? (error as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
                : 'Failed to end session';
            toast.error(message || 'Failed to end session');
        },
    });

    return {
        startSession: startMutation.mutate,
        endSession: endMutation.mutate,
        isStarting: startMutation.isPending,
        isEnding: endMutation.isPending,
    };
}
