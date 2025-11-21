'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/hooks/use-auth';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { User, Lock, Bell, Trash2 } from 'lucide-react';

export default function SettingsPage() {
    const { user } = useAuth();
    const [isUpdating, setIsUpdating] = useState(false);

    const handleUpdateProfile = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsUpdating(true);

        // Simulate API call
        setTimeout(() => {
            toast.success('Profile updated successfully');
            setIsUpdating(false);
        }, 1000);
    };

    const handleUpdatePassword = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsUpdating(true);

        // Simulate API call
        setTimeout(() => {
            toast.success('Password updated successfully');
            setIsUpdating(false);
        }, 1000);
    };

    const handleDeleteAccount = () => {
        if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
            toast.error('Account deletion is not yet implemented');
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
                <p className="mt-2 text-gray-600">
                    Manage your account settings and preferences
                </p>
            </div>

            {/* Settings Tabs */}
            <Card className="p-6">
                <Tabs defaultValue="profile" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                        <TabsTrigger value="profile">
                            <User className="h-4 w-4 mr-2" />
                            Profile
                        </TabsTrigger>
                        <TabsTrigger value="security">
                            <Lock className="h-4 w-4 mr-2" />
                            Security
                        </TabsTrigger>
                        <TabsTrigger value="notifications">
                            <Bell className="h-4 w-4 mr-2" />
                            Notifications
                        </TabsTrigger>
                    </TabsList>

                    {/* Profile Tab */}
                    <TabsContent value="profile" className="mt-6 space-y-6">
                        <div>
                            <h3 className="text-lg font-semibold mb-4">Profile Information</h3>
                            <form onSubmit={handleUpdateProfile} className="space-y-4">
                                <div>
                                    <Label htmlFor="full_name">Full Name</Label>
                                    <Input
                                        id="full_name"
                                        defaultValue={user?.full_name}
                                        placeholder="John Doe"
                                    />
                                </div>

                                <div>
                                    <Label htmlFor="email">Email</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        defaultValue={user?.email}
                                        placeholder="john@example.com"
                                        disabled
                                    />
                                    <p className="text-xs text-gray-500 mt-1">
                                        Email cannot be changed
                                    </p>
                                </div>

                                <div>
                                    <Label htmlFor="role">Role</Label>
                                    <Input
                                        id="role"
                                        defaultValue={user?.role}
                                        disabled
                                    />
                                </div>

                                <Button type="submit" disabled={isUpdating}>
                                    {isUpdating ? 'Saving...' : 'Save Changes'}
                                </Button>
                            </form>
                        </div>
                    </TabsContent>

                    {/* Security Tab */}
                    <TabsContent value="security" className="mt-6 space-y-6">
                        <div>
                            <h3 className="text-lg font-semibold mb-4">Change Password</h3>
                            <form onSubmit={handleUpdatePassword} className="space-y-4">
                                <div>
                                    <Label htmlFor="current_password">Current Password</Label>
                                    <Input
                                        id="current_password"
                                        type="password"
                                        placeholder="••••••••"
                                    />
                                </div>

                                <div>
                                    <Label htmlFor="new_password">New Password</Label>
                                    <Input
                                        id="new_password"
                                        type="password"
                                        placeholder="••••••••"
                                    />
                                </div>

                                <div>
                                    <Label htmlFor="confirm_password">Confirm New Password</Label>
                                    <Input
                                        id="confirm_password"
                                        type="password"
                                        placeholder="••••••••"
                                    />
                                </div>

                                <Button type="submit" disabled={isUpdating}>
                                    {isUpdating ? 'Updating...' : 'Update Password'}
                                </Button>
                            </form>
                        </div>

                        <Separator />

                        <div>
                            <h3 className="text-lg font-semibold mb-2 text-red-600">Danger Zone</h3>
                            <Card className="p-4 border-red-200 bg-red-50">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <h4 className="font-medium text-red-900">Delete Account</h4>
                                        <p className="text-sm text-red-700 mt-1">
                                            Once you delete your account, there is no going back. Please be certain.
                                        </p>
                                    </div>
                                    <Button
                                        variant="destructive"
                                        onClick={handleDeleteAccount}
                                        className="ml-4"
                                    >
                                        <Trash2 className="h-4 w-4 mr-2" />
                                        Delete
                                    </Button>
                                </div>
                            </Card>
                        </div>
                    </TabsContent>

                    {/* Notifications Tab */}
                    <TabsContent value="notifications" className="mt-6 space-y-6">
                        <div>
                            <h3 className="text-lg font-semibold mb-4">Notification Preferences</h3>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between p-4 border rounded-lg">
                                    <div>
                                        <h4 className="font-medium">Email Notifications</h4>
                                        <p className="text-sm text-gray-600">
                                            Receive email updates about your study progress
                                        </p>
                                    </div>
                                    <input type="checkbox" defaultChecked className="h-4 w-4" />
                                </div>

                                <div className="flex items-center justify-between p-4 border rounded-lg">
                                    <div>
                                        <h4 className="font-medium">Review Reminders</h4>
                                        <p className="text-sm text-gray-600">
                                            Get reminded when reviews are due
                                        </p>
                                    </div>
                                    <input type="checkbox" defaultChecked className="h-4 w-4" />
                                </div>

                                <div className="flex items-center justify-between p-4 border rounded-lg">
                                    <div>
                                        <h4 className="font-medium">Weekly Summary</h4>
                                        <p className="text-sm text-gray-600">
                                            Receive a weekly summary of your progress
                                        </p>
                                    </div>
                                    <input type="checkbox" defaultChecked className="h-4 w-4" />
                                </div>

                                <div className="flex items-center justify-between p-4 border rounded-lg">
                                    <div>
                                        <h4 className="font-medium">Exam Generation Complete</h4>
                                        <p className="text-sm text-gray-600">
                                            Get notified when exam generation is complete
                                        </p>
                                    </div>
                                    <input type="checkbox" defaultChecked className="h-4 w-4" />
                                </div>
                            </div>

                            <Button className="mt-6">
                                Save Preferences
                            </Button>
                        </div>
                    </TabsContent>
                </Tabs>
            </Card>
        </div>
    );
}
