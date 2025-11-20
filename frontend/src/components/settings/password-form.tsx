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
    new_password: z.string().min(8, 'Password must be at least 8 characters'),
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
