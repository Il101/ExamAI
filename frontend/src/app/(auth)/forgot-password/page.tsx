'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { authApi } from '@/lib/api/auth';
import { toast } from 'sonner';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

const forgotPasswordSchema = z.object({
    email: z.string().email('Invalid email address'),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordPage() {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [emailSent, setEmailSent] = useState(false);

    const form = useForm<ForgotPasswordFormData>({
        resolver: zodResolver(forgotPasswordSchema),
    });

    const onSubmit = async (data: ForgotPasswordFormData) => {
        setIsSubmitting(true);
        try {
            await authApi.requestPasswordReset(data.email);
            setEmailSent(true);
            toast.success('Password reset email sent! Please check your inbox.');
        } catch (error: unknown) {
            const message = error instanceof Error && 'response' in error
                ? (error as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
                : 'Failed to send reset email';
            toast.error(message || 'Failed to send reset email');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (emailSent) {
        return (
            <Card className="w-full p-8 shadow-2xl border-white/10 bg-card/50 backdrop-blur-xl text-center">
                <div className="mb-6">
                    <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                        <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <h1 className="text-2xl font-bold mb-2 text-foreground">Check your email</h1>
                    <p className="text-muted-foreground">
                        We&apos;ve sent a password reset link to <strong>{form.getValues('email')}</strong>
                    </p>
                </div>

                <p className="text-sm text-muted-foreground mb-6">
                    Didn&apos;t receive the email? Check your spam folder or try again.
                </p>

                <Link href="/login">
                    <Button variant="outline" className="w-full">
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back to login
                    </Button>
                </Link>
            </Card>
        );
    }

    return (
        <Card className="w-full p-8 shadow-2xl border-white/10 bg-card/50 backdrop-blur-xl">
            <div className="mb-8">
                <Link href="/login" className="inline-flex items-center text-sm text-primary hover:text-accent hover:underline transition-colors mb-4">
                    <ArrowLeft className="w-4 h-4 mr-1" />
                    Back to login
                </Link>
                <h1 className="text-3xl font-bold mb-2 text-foreground">Forgot password?</h1>
                <p className="text-muted-foreground">
                    No worries, we&apos;ll send you reset instructions.
                </p>
            </div>

            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                        id="email"
                        type="email"
                        placeholder="you@example.com"
                        {...form.register('email')}
                        disabled={isSubmitting}
                    />
                    {form.formState.errors.email && (
                        <p className="text-sm text-red-500 mt-1">
                            {form.formState.errors.email.message}
                        </p>
                    )}
                </div>

                <Button
                    type="submit"
                    className="w-full"
                    disabled={isSubmitting}
                >
                    {isSubmitting ? 'Sending...' : 'Send reset link'}
                </Button>
            </form>
        </Card>
    );
}
