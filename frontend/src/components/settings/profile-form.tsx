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
import { useAuthStore } from '@/lib/stores/auth-store';
import { Loader2 } from 'lucide-react';

const profileSchema = z.object({
    full_name: z.string().min(2, 'Name must be at least 2 characters'),
    email: z.string().email().readonly(), // Email cannot be changed
    daily_study_goal_minutes: z.number().min(5).max(480).optional(),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

export function ProfileForm() {
    const { user, setUser } = useAuthStore();
    const [isLoading, setIsLoading] = useState(false);

    const form = useForm<ProfileFormValues>({
        resolver: zodResolver(profileSchema),
        defaultValues: {
            full_name: user?.full_name || '',
            email: user?.email || '',
            daily_study_goal_minutes: 30, // Default or from user object if available
        },
    });

    const onSubmit = async (data: ProfileFormValues) => {
        setIsLoading(true);
        try {
            const updatedUser = await usersApi.updateProfile({
                full_name: data.full_name,
                daily_study_goal_minutes: data.daily_study_goal_minutes,
            });

            // Update local store
            // Note: The backend currently returns the user object, so we can update the store
            // But we might need to merge if the backend response is partial or different
            if (user) {
                setUser({ ...user, full_name: updatedUser.full_name });
            }

            toast.success('Profile updated successfully');
        } catch (error) {
            console.error('Failed to update profile:', error);
            toast.error('Failed to update profile');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>Update your personal details and study preferences.</CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" {...form.register('email')} disabled />
                        <p className="text-xs text-muted-foreground">Email cannot be changed.</p>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="full_name">Full Name</Label>
                        <Input id="full_name" {...form.register('full_name')} />
                        {form.formState.errors.full_name && (
                            <p className="text-sm text-red-500">{form.formState.errors.full_name.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="daily_study_goal_minutes">Daily Study Goal (minutes)</Label>
                        <Input
                            id="daily_study_goal_minutes"
                            type="number"
                            {...form.register('daily_study_goal_minutes', { valueAsNumber: true })}
                        />
                        <p className="text-xs text-muted-foreground">Target minutes per day for study sessions.</p>
                        {form.formState.errors.daily_study_goal_minutes && (
                            <p className="text-sm text-red-500">{form.formState.errors.daily_study_goal_minutes.message}</p>
                        )}
                    </div>

                    <Button type="submit" disabled={isLoading}>
                        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Save Changes
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}
