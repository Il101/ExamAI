import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { studyApi } from '@/lib/api/study';
import { toast } from 'sonner';

interface SubmitReviewData {
    reviewId: string;
    quality: number;
}

export function useReviews(limit: number = 20) {
    const queryClient = useQueryClient();

    const { data: dueReviews, isLoading } = useQuery({
        queryKey: ['reviews', 'due', limit],
        queryFn: () => studyApi.getDueReviews(limit),
    });

    const submitMutation = useMutation({
        mutationFn: ({ reviewId, quality }: SubmitReviewData) =>
            studyApi.submitReview(reviewId, quality),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['reviews'] });
            queryClient.invalidateQueries({ queryKey: ['analytics'] });
        },
        onError: (error: unknown) => {
            const message = error instanceof Error && 'response' in error
                ? (error as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
                : 'Failed to submit review';
            toast.error(message || 'Failed to submit review');
        },
    });

    return {
        dueReviews,
        isLoading,
        submitReview: submitMutation.mutate,
        isSubmitting: submitMutation.isPending,
    };
}
