import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { examsApi, CreateExamRequest } from '@/lib/api/exams';
import { toast } from 'sonner';

export function useExams() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['exams'],
    queryFn: () => examsApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: (data: FormData) => examsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exams'] });
      toast.success('Exam created successfully');
    },
    onError: (error: unknown) => {
      let message = 'Failed to create exam';

      if (error instanceof Error && 'response' in error) {
        const responseError = error as { response?: { data?: { error?: { message?: string }, detail?: string } } };
        // Check for custom AppException format first, then fallback to standard FastAPI detail
        message = responseError.response?.data?.error?.message ||
          responseError.response?.data?.detail ||
          'Failed to create exam';
      }

      toast.error(message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (examId: string) => examsApi.delete(examId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exams'] });
      toast.success('Exam deleted');
    },
    onError: (error: unknown) => {
      let message = 'Failed to delete exam';

      if (error instanceof Error && 'response' in error) {
        const responseError = error as { response?: { data?: { error?: { message?: string }, detail?: string } } };
        message = responseError.response?.data?.error?.message ||
          responseError.response?.data?.detail ||
          'Failed to delete exam';
      }

      toast.error(message);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ examId, data }: { examId: string; data: any }) => examsApi.update(examId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exams'] });
      queryClient.invalidateQueries({ queryKey: ['exam'] });
      toast.success('Exam updated successfully');
    },
    onError: (error: unknown) => {
      let message = 'Failed to update exam';
      if (error instanceof Error && 'response' in error) {
        const responseError = error as { response?: { data?: { error?: { message?: string }, detail?: string } } };
        message = responseError.response?.data?.error?.message ||
          responseError.response?.data?.detail ||
          'Failed to update exam';
      }
      toast.error(message);
    },
  });

  return {
    exams: data?.exams || [],
    isLoading,
    createExam: createMutation.mutate,
    updateExam: updateMutation.mutate,
    deleteExam: deleteMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
