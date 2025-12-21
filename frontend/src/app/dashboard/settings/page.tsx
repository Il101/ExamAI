'use client';

import { useAuth } from '@/lib/hooks/use-auth';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { User, Lock, Bell, Trash2, CreditCard } from 'lucide-react';
import { ProfileForm } from '@/components/settings/profile-form';
import { PasswordForm } from '@/components/settings/password-form';
import { NotificationSettings } from '@/components/settings/notification-settings';
import { BillingSettings } from '@/components/settings/billing-settings';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { useState } from 'react';
import { usersApi } from '@/lib/api/users';
import { useRouter } from 'next/navigation';

export default function SettingsPage() {
    const { user, logout } = useAuth();
    const router = useRouter();
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const handleDeleteAccount = async () => {
        try {
            setIsDeleting(true);
            await usersApi.deleteAccount();
            toast.success('Account deleted successfully');
            await logout();
            router.push('/');
        } catch (error) {
            console.error('Failed to delete account:', error);
            toast.error('Failed to delete account. Please try again.');
        } finally {
            setIsDeleting(false);
            setIsDeleteDialogOpen(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-foreground">Settings</h1>
                <p className="mt-2 text-muted-foreground">
                    Manage your account settings and preferences
                </p>
            </div>

            {/* Settings Tabs */}
            <Tabs defaultValue="profile" className="w-full space-y-6">
                <Card className="p-1">
                    <TabsList className="grid w-full grid-cols-4">
                        <TabsTrigger value="profile">
                            <User className="h-4 w-4 mr-2" />
                            Profile
                        </TabsTrigger>
                        <TabsTrigger value="billing">
                            <CreditCard className="h-4 w-4 mr-2" />
                            Billing
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

                {/* Billing Tab */}
                <TabsContent value="billing">
                    <BillingSettings />
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
                                    onClick={() => setIsDeleteDialogOpen(true)}
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
                    <NotificationSettings user={user ?? null} />
                </TabsContent>
            </Tabs>

            <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Are you absolutely sure?</DialogTitle>
                        <DialogDescription>
                            This action cannot be undone. This will permanently delete your account
                            and remove all your learning materials, exams, and progress from our servers.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setIsDeleteDialogOpen(false)}
                            disabled={isDeleting}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={handleDeleteAccount}
                            disabled={isDeleting}
                        >
                            {isDeleting ? 'Deleting...' : 'Delete Account'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
