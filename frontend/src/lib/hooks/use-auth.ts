'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/lib/api/auth';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { useEffect, useState } from 'react';

export function useAuth() {
    const router = useRouter();
    const { setUser, logout: logoutStore } = useAuthStore();
    const queryClient = useQueryClient();
    const [hasToken, setHasToken] = useState(false);
    const [isCheckingToken, setIsCheckingToken] = useState(true);

    useEffect(() => {
        // Avoid hydration mismatch by only checking localStorage on client
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('access_token');
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setHasToken(!!token);
            setIsCheckingToken(false);
        }
    }, []);

    const { data: user, isLoading: queryIsLoading } = useQuery({
        queryKey: ['currentUser'],
        queryFn: async () => {
            if (!hasToken) return null;
            try {
                return await authApi.getCurrentUser();
            } catch {
                return null;
            }
        },
        enabled: hasToken,
        retry: false,
    });

    const isLoading = isCheckingToken || (hasToken && queryIsLoading);

    const loginMutation = useMutation({
        mutationFn: authApi.login,
        onSuccess: async (data) => {
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            setHasToken(true); // Explicitly update state

            try {
                // Fetch user with new token
                const user = await authApi.getCurrentUser();

                if (user) {
                    // Update query cache
                    queryClient.setQueryData(['currentUser'], user);
                    setUser(user);
                    toast.success('Successfully logged in!');
                    router.push('/dashboard');
                } else {
                    toast.error('Failed to fetch user data after login');
                    // Clear tokens if user fetch fails
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    setHasToken(false);
                }
            } catch (error) {
                console.error('Failed to fetch user after login:', error);
                toast.error('Failed to fetch user data after login');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                setHasToken(false);
            }
        },
        onError: (error: unknown) => {
            let message = 'Login failed';

            if (error instanceof Error) {
                // Check for network error
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                if ((error as any).isNetworkError) {
                    message = error.message || 'Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен.';
                } else if ('response' in error) {
                    const responseError = error as { response?: { data?: { error?: { message?: string } } } };
                    message = responseError.response?.data?.error?.message || 'Login failed';
                } else {
                    message = error.message || 'Login failed';
                }
            }

            toast.error(message);
        },
    });

    const registerMutation = useMutation({
        mutationFn: authApi.register,
        onSuccess: () => {
            // Success is handled by the register page UI - don't redirect
            toast.success('Registration successful! Please check your email to verify your account.');
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
        login: loginMutation.mutateAsync,
        register: registerMutation.mutateAsync,
        logout: logoutMutation.mutateAsync,
        isLoggingIn: loginMutation.isPending,
        isRegistering: registerMutation.isPending,
    };
}
