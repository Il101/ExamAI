import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { coursesApi, CourseCreateRequest, CourseUpdateRequest } from '@/lib/api/courses';
import { toast } from 'sonner';

export function useCourses() {
    const queryClient = useQueryClient();

    const { data, isLoading, error } = useQuery({
        queryKey: ['courses'],
        queryFn: () => coursesApi.list(),
    });

    const createMutation = useMutation({
        mutationFn: (data: CourseCreateRequest) => coursesApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['courses'] });
            toast.success('Course created successfully');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to create course');
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: CourseUpdateRequest }) =>
            coursesApi.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['courses'] });
            toast.success('Course updated');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to update course');
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => coursesApi.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['courses'] });
            toast.success('Course deleted');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to delete course');
        },
    });

    const addExamMutation = useMutation({
        mutationFn: ({ courseId, examId }: { courseId: string; examId: string }) =>
            coursesApi.addExam(courseId, examId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['courses'] });
            queryClient.invalidateQueries({ queryKey: ['exams'] });
            toast.success('Exam added to course');
        },
    });

    const removeExamMutation = useMutation({
        mutationFn: ({ courseId, examId }: { courseId: string; examId: string }) =>
            coursesApi.removeExam(courseId, examId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['courses'] });
            queryClient.invalidateQueries({ queryKey: ['exams'] });
            toast.success('Exam removed from course');
        },
    });

    return {
        courses: data?.items || [],
        total: data?.total || 0,
        isLoading,
        error,
        createCourse: createMutation.mutateAsync,
        updateCourse: updateMutation.mutateAsync,
        deleteCourse: deleteMutation.mutateAsync,
        addExam: addExamMutation.mutateAsync,
        removeExam: removeExamMutation.mutateAsync,
        isCreating: createMutation.isPending,
        isUpdating: updateMutation.isPending,
        isDeleting: deleteMutation.isPending,
    };
}

export function useCourse(courseId: string) {
    return useQuery({
        queryKey: ['courses', courseId],
        queryFn: () => coursesApi.getById(courseId),
        enabled: !!courseId,
    });
}

export function useCourseExams(courseId: string) {
    return useQuery({
        queryKey: ['courses', courseId, 'exams'],
        queryFn: () => coursesApi.listExams(courseId),
        enabled: !!courseId,
    });
}
