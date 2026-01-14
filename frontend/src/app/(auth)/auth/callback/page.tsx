'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { authApi } from '@/lib/api/auth';
import { useAuthStore } from '@/lib/stores/auth-store';

function AuthCallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const setUser = useAuthStore((state) => state.setUser);
    const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
    const [message, setMessage] = useState('Verifying your email...');

    useEffect(() => {
        const handleEmailVerification = async () => {
            try {
                // Supabase sends tokens in URL hash (after #)
                const hash = window.location.hash;
                const params = new URLSearchParams(hash.substring(1)); // Remove # and parse

                // Also check query params (Supabase sometimes uses these)
                const queryParams = new URLSearchParams(window.location.search);

                const accessToken = params.get('access_token');
                const refreshToken = params.get('refresh_token');
                const error = params.get('error') || queryParams.get('error');
                const errorDescription = params.get('error_description') || queryParams.get('error_description');
                const type = params.get('type') || queryParams.get('type');
                const tokenHash = queryParams.get('token_hash');

                // Debug logging
                console.log('Auth callback received:', {
                    hash: hash ? 'present' : 'empty',
                    accessToken: accessToken ? 'present' : 'missing',
                    refreshToken: refreshToken ? 'present' : 'missing',
                    type,
                    tokenHash: tokenHash ? 'present' : 'missing',
                    error,
                    fullUrl: window.location.href
                });

                // Check for errors from Supabase
                if (error) {
                    setStatus('error');
                    setMessage(errorDescription || 'An error occurred during email verification');
                    return;
                }

                // If we have tokens, store them and attempt to fetch user
                if (accessToken && refreshToken) {
                    // Store tokens in localStorage
                    localStorage.setItem('access_token', accessToken);
                    localStorage.setItem('refresh_token', refreshToken);

                    setMessage('Authorization successful. Loading profile...');

                    // Fetch user data and update auth store
                    try {
                        const user = await authApi.getCurrentUser();
                        setUser(user);

                        setStatus('success');
                        setMessage('Login successful! Redirecting to dashboard...');

                        // Redirect to dashboard after 1 second
                        setTimeout(() => {
                            router.push('/dashboard');
                        }, 1000);
                    } catch (err) {
                        console.error('Failed to fetch user data:', err);
                        setStatus('error');
                        setMessage('Failed to load user profile. The account may have been deleted or blocked.');
                        // Do NOT redirect if we can't get the user, otherwise they'll just get kicked back
                        // Clear tokens to prevent loop
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                    }
                } else if (type === 'signup' || type === 'email' || type === 'email_change' || tokenHash) {
                    // Email verification without auto-login (older Supabase flow or token_hash flow)
                    setStatus('success');
                    setMessage('Email verified successfully! You can now log in.');

                    setTimeout(() => {
                        router.push('/login?verified=true');
                    }, 2000);
                } else {
                    // Unknown callback type - show message instead of silent redirect
                    console.warn('Unknown callback type, redirecting to login');
                    setStatus('success');
                    setMessage('Verification complete. Redirecting to login...');

                    setTimeout(() => {
                        router.push('/login');
                    }, 1500);
                }
            } catch (err) {
                console.error('Email verification error:', err);
                setStatus('error');
                setMessage('An error occurred while processing verification');
            }
        };

        handleEmailVerification();
    }, [router, searchParams]);

    return (
        <div className="flex min-h-screen items-center justify-center bg-background">
            <div className="w-full max-w-md space-y-6 rounded-lg border border-border bg-card p-8 shadow-lg">
                <div className="text-center">
                    {status === 'verifying' && (
                        <>
                            <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
                            <h2 className="text-2xl font-bold text-foreground">Email Verification</h2>
                            <p className="mt-2 text-muted-foreground">{message}</p>
                        </>
                    )}

                    {status === 'success' && (
                        <>
                            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                                <svg
                                    className="h-6 w-6 text-green-600 dark:text-green-300"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M5 13l4 4L19 7"
                                    />
                                </svg>
                            </div>
                            <h2 className="text-2xl font-bold text-foreground">Success!</h2>
                            <p className="mt-2 text-muted-foreground">{message}</p>
                        </>
                    )}

                    {status === 'error' && (
                        <>
                            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900">
                                <svg
                                    className="h-6 w-6 text-red-600 dark:text-red-300"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </div>
                            <h2 className="text-2xl font-bold text-foreground">Error</h2>
                            <p className="mt-2 text-muted-foreground">{message}</p>
                            <button
                                onClick={() => router.push('/login')}
                                className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                            >
                                Return to login page
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function AuthCallbackPage() {
    return (
        <Suspense fallback={
            <div className="flex min-h-screen items-center justify-center bg-background">
                <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
            </div>
        }>
            <AuthCallbackContent />
        </Suspense>
    );
}
