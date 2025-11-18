import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { examsApi } from '@/lib/api/exams';

// We need to add these methods to examsApi first, but I'll define the hook assuming they exist or I'll add them.
// I'll check examsApi again.

export function useExamGeneration(examId: string) {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const queryClient = useQueryClient();

  const startMutation = useMutation({
    mutationFn: () => examsApi.startGeneration(examId) as Promise<{ task_id: string }>,
    onSuccess: (data) => {
      setTaskId(data.task_id);
    },
  });

  // Poll task status
  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(async () => {
      try {
        const taskStatus = await examsApi.getTaskStatus(taskId);

        if (taskStatus.state === 'PROGRESS') {
          setProgress(taskStatus.current);
          setStatus(taskStatus.status);
        } else if (taskStatus.state === 'SUCCESS') {
          setProgress(100);
          setStatus('Complete');
          clearInterval(interval);
          queryClient.invalidateQueries({ queryKey: ['exams'] });
          queryClient.invalidateQueries({ queryKey: ['exam', examId] });
        } else if (taskStatus.state === 'FAILURE') {
          setStatus('Failed');
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Error polling task:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [taskId, examId, queryClient]);

  return {
    startGeneration: startMutation.mutate,
    isGenerating: !!taskId && progress < 100,
    progress,
    status,
  };
}
