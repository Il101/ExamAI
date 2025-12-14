'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { usersApi } from '@/lib/api/users';
import { Loader2 } from 'lucide-react';

const passwordSchema = z.object({
    current_password: z.string().min(1, 'Current password is required'),
    new_password: z.string()
        .min(8, 'Password must be at least 8 characters')
        .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
        .regex(/[a-z]/, 'Must contain at least one lowercase letter')
        .regex(/[0-9]/, 'Must contain at least one number')
        .regex(/[^A-Za-z0-9]/, 'Must include any non-alphanumeric character (e.g. !@#$%^&*()-_=+)'),
    confirm_password: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords don't match",
    path: ["confirm_password"],
});

type PasswordFormValues = z.infer<typeof passwordSchema>;

export function PasswordForm() {
    const [isLoading, setIsLoading] = useState(false);

    const form = useForm<PasswordFormValues>({
        resolver: zodResolver(passwordSchema),
    });

    const passwordValue = form.watch('new_password', '');
    const passwordChecklist = [
        { label: 'At least 8 characters', valid: passwordValue.length >= 8 },
        { label: 'Uppercase letter', valid: /[A-Z]/.test(passwordValue) },
        { label: 'Lowercase letter', valid: /[a-z]/.test(passwordValue) },
        { label: 'Number', valid: /[0-9]/.test(passwordValue) },
        { label: 'Any symbol (e.g. !@#$%^&*()-_=+)', valid: /[^A-Za-z0-9]/.test(passwordValue) },
    ];

    const onSubmit = async (data: PasswordFormValues) => {
        setIsLoading(true);
        try {
            await usersApi.changePassword({
                current_password: data.current_password,
                new_password: data.new_password,
            });

            toast.success('Password changed successfully');
            form.reset();
        } catch (error) {
            console.error('Failed to change password:', error);
            toast.error('Failed to change password. Please check your current password.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle>Change Password</CardTitle>
                <CardDescription>Ensure your account is secure by using a strong password.</CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="current_password">Current Password</Label>
                        <Input
                            id="current_password"
                            type="password"
                            {...form.register('current_password')}
                        />
                        {form.formState.errors.current_password && (
                            <p className="text-sm text-red-500">{form.formState.errors.current_password.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="new_password">New Password</Label>
                        <Input
                            id="new_password"
                            type="password"
                            {...form.register('new_password')}
                        />
                        {form.formState.errors.new_password && (
                            <p className="text-sm text-red-500">{form.formState.errors.new_password.message}</p>
                        )}
                        <div className="mt-2 space-y-1 text-xs text-muted-foreground">
                            {passwordChecklist.map((item) => (
                                <div key={item.label} className="flex items-center gap-2">
                                    <span className={item.valid ? 'text-green-600' : 'text-gray-400'}>
                                        {item.valid ? '✓' : '•'}
                                    </span>
                                    <span className={item.valid ? 'text-green-700' : undefined}>{item.label}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="confirm_password">Confirm New Password</Label>
                        <Input
                            id="confirm_password"
                            type="password"
                            {...form.register('confirm_password')}
                        />
                        {form.formState.errors.confirm_password && (
                            <p className="text-sm text-red-500">{form.formState.errors.confirm_password.message}</p>
                        )}
                    </div>

                    <Button type="submit" disabled={isLoading}>
                        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Update Password
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}
