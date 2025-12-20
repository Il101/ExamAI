'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { User } from '@/lib/api/auth';
import { usersApi } from '@/lib/api/users';
import { usePushNotifications } from '@/hooks/use-push-notifications';

interface NotificationSettingsProps {
    user: User | null;
}

export function NotificationSettings({ user }: NotificationSettingsProps) {
    const { isSubscribed, subscribe, unsubscribe, isLoading: isPushLoading } = usePushNotifications();
    const [isLoading, setIsLoading] = useState(false);
    const [preferences, setPreferences] = useState({
        notification_exam_ready: user?.notification_exam_ready ?? true,
        notification_study_reminders: user?.notification_study_reminders ?? true,
        notification_product_updates: user?.notification_product_updates ?? false,
    });

    const handleToggle = (key: keyof typeof preferences) => {
        setPreferences(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    const handleSave = async () => {
        try {
            setIsLoading(true);
            await usersApi.updateProfile({
                notification_exam_ready: preferences.notification_exam_ready,
                notification_study_reminders: preferences.notification_study_reminders,
                notification_product_updates: preferences.notification_product_updates,
            });
            toast.success('Notification preferences saved');
        } catch (error) {
            console.error('Failed to save preferences:', error);
            toast.error('Failed to save preferences. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Card className="p-6">
            <div className="space-y-6">
                <div>
                    <h3 className="text-lg font-semibold mb-1">Notification Preferences</h3>
                    <p className="text-sm text-gray-500 mb-4">
                        Choose how and when you want to receive updates from ExamAI.
                    </p>
                </div>

                <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 border rounded-lg transition-colors hover:bg-gray-50/50">
                        <div className="space-y-0.5">
                            <Label htmlFor="exam-ready" className="text-base font-medium">Exam Generation Complete</Label>
                            <p className="text-sm text-gray-600">
                                Get notified via email as soon as your study materials are generated and ready.
                            </p>
                        </div>
                        <Switch
                            id="exam-ready"
                            checked={preferences.notification_exam_ready}
                            onCheckedChange={() => handleToggle('notification_exam_ready')}
                            disabled={isLoading}
                        />
                    </div>

                    <div className="flex items-center justify-between p-4 border rounded-lg transition-colors hover:bg-gray-50/50">
                        <div className="space-y-0.5">
                            <Label htmlFor="study-reminders" className="text-base font-medium">Study Reminders</Label>
                            <p className="text-sm text-gray-600">
                                Receive daily reminders when you have cards due for review to keep your streak.
                            </p>
                        </div>
                        <Switch
                            id="study-reminders"
                            checked={preferences.notification_study_reminders}
                            onCheckedChange={() => handleToggle('notification_study_reminders')}
                            disabled={isLoading}
                        />
                    </div>

                    <div className="flex items-center justify-between p-4 border rounded-lg transition-colors hover:bg-gray-50/50">
                        <div className="space-y-0.5">
                            <Label htmlFor="product-updates" className="text-base font-medium">Product Updates</Label>
                            <p className="text-sm text-gray-600">
                                Be the first to know about new features, improvements, and exclusive offers.
                            </p>
                        </div>
                        <Switch
                            id="product-updates"
                            checked={preferences.notification_product_updates}
                            onCheckedChange={() => handleToggle('notification_product_updates')}
                            disabled={isLoading}
                        />
                    </div>

                    <div className="flex items-center justify-between p-4 border rounded-lg transition-colors bg-blue-50/30 border-blue-100 hover:bg-blue-50/50">
                        <div className="space-y-0.5">
                            <Label htmlFor="browser-push" className="text-base font-medium flex items-center gap-2">
                                Browser Notifications
                                <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full font-bold uppercase tracking-wider">Experimental</span>
                            </Label>
                            <p className="text-sm text-gray-600">
                                Receive real-time push notifications in your browser even when ExamAI is closed.
                            </p>
                        </div>
                        <Switch
                            id="browser-push"
                            checked={isSubscribed}
                            onCheckedChange={() => isSubscribed ? unsubscribe() : subscribe()}
                            disabled={isPushLoading}
                        />
                    </div>
                </div>

                <div className="flex justify-end pt-2">
                    <Button onClick={handleSave} disabled={isLoading} className="w-full sm:w-auto">
                        {isLoading ? 'Saving...' : 'Save Preferences'}
                    </Button>
                </div>
            </div>
        </Card>
    );
}
