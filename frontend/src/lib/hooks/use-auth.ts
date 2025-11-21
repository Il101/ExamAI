import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/lib/api/auth';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

export function useAuth() {
    const router = useRouter();
    const { setUser, logout: logoutStore } = useAuthStore();
    const queryClient = useQueryClient();

    const { data: user, isLoading } = useQuery({
        queryKey: ['currentUser'],
        queryFn: authApi.getCurrentUser,
        retry: false,
        enabled: typeof window !== 'undefined' && !!localStorage.getItem('access_token'),
    });

    const loginMutation = useMutation({
        mutationFn: authApi.login,
        onSuccess: async (data) => {
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);

            try {
                const user = await authApi.getCurrentUser();
                setUser(user);
                toast.success('Successfully logged in!');
                router.push('/dashboard');
            } catch {
                toast.error('Failed to fetch user data');
            }
        },
        onError: (error: unknown) => {
            const message = error instanceof Error && 'response' in error
                ? (error as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
                : 'Login failed';
            toast.error(message || 'Login failed');
        },
    });

    const registerMutation = useMutation({
        mutationFn: authApi.register,
        onSuccess: () => {
            toast.success('Registration successful! Please check your email to verify your account.');
            router.push('/login');
        },
        onError: (error: unknown) => {
            const message = error instanceof Error && 'response' in error
                ? (error as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
                : 'Registration failed';
            toast.error(message || 'Registration failed');
        },
    });

    const logoutMutation = useMutation({
        mutationFn: authApi.logout,
        onSuccess: () => {
            logoutStore();
            queryClient.clear();
            toast.success('Logged out successfully');
            router.push('/login');
        },
        onError: () => {
            // Even if API call fails, clear local state
            logoutStore();
            queryClient.clear();
            router.push('/login');
        },
    });

    return {
        user,
        isLoading,
        isAuthenticated: !!user,
        login: loginMutation.mutate,
        register: registerMutation.mutate,
        logout: logoutMutation.mutate,
        isLoggingIn: loginMutation.isPending,
        isRegistering: registerMutation.isPending,
    };
}
