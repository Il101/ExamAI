'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

function AuthCallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
    const [message, setMessage] = useState('Подтверждаем вашу почту...');

    useEffect(() => {
        const handleEmailVerification = async () => {
            try {
                // Get the token from URL parameters
                const token = searchParams.get('token');
                const type = searchParams.get('type');
                const error = searchParams.get('error');
                const errorDescription = searchParams.get('error_description');

                // Check for errors from Supabase
                if (error) {
                    setStatus('error');
                    setMessage(errorDescription || 'Произошла ошибка при подтверждении email');
                    return;
                }

                // If this is an email confirmation
                if (type === 'signup' || type === 'email') {
                    setStatus('success');
                    setMessage('Email успешно подтвержден! Перенаправляем на страницу входа...');

                    // Redirect to login after 2 seconds
                    setTimeout(() => {
                        router.push('/login?verified=true');
                    }, 2000);
                } else {
                    // For other types or if no type specified, redirect to login
                    router.push('/login');
                }
            } catch (err) {
                console.error('Email verification error:', err);
                setStatus('error');
                setMessage('Произошла ошибка при обработке подтверждения');
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
                            <h2 className="text-2xl font-bold text-foreground">Подтверждение email</h2>
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
                            <h2 className="text-2xl font-bold text-foreground">Успешно!</h2>
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
                            <h2 className="text-2xl font-bold text-foreground">Ошибка</h2>
                            <p className="mt-2 text-muted-foreground">{message}</p>
                            <button
                                onClick={() => router.push('/login')}
                                className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                            >
                                Вернуться на страницу входа
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
