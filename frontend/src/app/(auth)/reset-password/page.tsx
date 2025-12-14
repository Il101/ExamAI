'use client';

import { useState, Suspense, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { authApi } from '@/lib/api/auth';
import { toast } from 'sonner';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

const resetPasswordSchema = z.object({
    password: z.string()
        .min(8, 'Password must be at least 8 characters')
        .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
        .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
        .regex(/[0-9]/, 'Password must contain at least one number')
        .regex(/[^A-Za-z0-9]/, 'Password must include any non-alphanumeric character (e.g. !@#$%^&*()-_=+)'),
    confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
});

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

function ResetPasswordContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    // Supabase recovery links may include tokens in query or hash fragment
    const token = useMemo(() => {
        const fromQuery = searchParams.get('token')
            || searchParams.get('token_hash')
            || searchParams.get('access_token');
        if (fromQuery) return fromQuery;

        if (typeof window !== 'undefined') {
            const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ''));
            return hashParams.get('access_token') || hashParams.get('token');
        }
        return null;
    }, [searchParams]);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const form = useForm<ResetPasswordFormData>({
        resolver: zodResolver(resetPasswordSchema),
    });

    const onSubmit = async (data: ResetPasswordFormData) => {
        if (!token) {
            toast.error('Invalid reset token');
            return;
        }

        setIsSubmitting(true);
        try {
            await authApi.resetPassword(token, data.password);
            toast.success('Password reset successfully!');
            router.push('/login');
        } catch (error: unknown) {
            const message = error instanceof Error && 'response' in error
                ? (error as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
                : 'Failed to reset password';
            toast.error(message || 'Failed to reset password');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!token) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4">
                <Card className="w-full max-w-md p-8 shadow-2xl border-white/10 bg-card/50 backdrop-blur-xl text-center">
                    <h1 className="text-2xl font-bold mb-4 text-foreground">Invalid Reset Link</h1>
                    <p className="text-muted-foreground mb-6">
                        This password reset link is invalid or has expired.
                    </p>
                    <Link href="/forgot-password">
                        <Button className="w-full">
                            Request new reset link
                        </Button>
                    </Link>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4">
            <Card className="w-full max-w-md p-8 shadow-2xl border-white/10 bg-card/50 backdrop-blur-xl">
                <div className="mb-8 text-center">
                    <h1 className="text-3xl font-bold mb-2 text-foreground">Reset password</h1>
                    <p className="text-muted-foreground">Enter your new password below</p>
                </div>

                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                    <div>
                        <Label htmlFor="password">New Password</Label>
                        <Input
                            id="password"
                            type="password"
                            placeholder="••••••••"
                            {...form.register('password')}
                            disabled={isSubmitting}
                        />
                        {form.formState.errors.password && (
                            <p className="text-sm text-red-500 mt-1">
                                {form.formState.errors.password.message}
                            </p>
                        )}
                    </div>

                    <div>
                        <Label htmlFor="confirmPassword">Confirm New Password</Label>
                        <Input
                            id="confirmPassword"
                            type="password"
                            placeholder="••••••••"
                            {...form.register('confirmPassword')}
                            disabled={isSubmitting}
                        />
                        {form.formState.errors.confirmPassword && (
                            <p className="text-sm text-red-500 mt-1">
                                {form.formState.errors.confirmPassword.message}
                            </p>
                        )}
                    </div>

                    <Button
                        type="submit"
                        className="w-full"
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? 'Resetting...' : 'Reset password'}
                    </Button>
                </form>

                <p className="text-center text-sm text-muted-foreground mt-6">
                    Remember your password?{' '}
                    <Link href="/login" className="text-primary hover:text-accent hover:underline font-medium transition-colors">
                        Sign in
                    </Link>
                </p>
            </Card>
        </div>
    );
}

export default function ResetPasswordPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <ResetPasswordContent />
        </Suspense>
    );
}
