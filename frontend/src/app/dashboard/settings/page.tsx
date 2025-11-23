'use client';

import { useAuth } from '@/lib/hooks/use-auth';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { User, Lock, Bell, Trash2 } from 'lucide-react';
import { ProfileForm } from '@/components/settings/profile-form';
import { PasswordForm } from '@/components/settings/password-form';

import { NotificationSettings } from '@/components/settings/notification-settings';

export default function SettingsPage() {
    const { user } = useAuth();

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
            <Tabs defaultValue="profile" className="w-full space-y-6">
                <Card className="p-1">
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
                </Card>

                {/* Profile Tab */}
                <TabsContent value="profile">
                    <ProfileForm />
                </TabsContent>

                {/* Security Tab */}
                <TabsContent value="security" className="space-y-6">
                    <PasswordForm />

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
                <TabsContent value="notifications">
                    <NotificationSettings />
                </TabsContent>
            </Tabs>
        </div>
    );
}
