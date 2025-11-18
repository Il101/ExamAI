import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { examsApi, CreateExamRequest } from '@/lib/api/exams';
import { toast } from 'sonner';

export function useExams() {
  const queryClient = useQueryClient();

  const { data: exams, isLoading } = useQuery({
    queryKey: ['exams'],
    queryFn: () => examsApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateExamRequest) => examsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exams'] });
      toast.success('Exam created successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create exam');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (examId: string) => examsApi.delete(examId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exams'] });
      toast.success('Exam deleted');
    },
    onError: (error: any) => {
      toast.error('Failed to delete exam');
    },
  });

  return {
    exams: exams || [],
    isLoading,
    createExam: createMutation.mutate,
    deleteExam: deleteMutation.mutate,
    isCreating: createMutation.isPending,
  };
}
