'use client';

import { useEffect, useState } from 'react';
import { Subscription, subscriptionsApi } from '@/lib/api/subscriptions';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';
import Link from 'next/link';

export default function SubscriptionPage() {
    const [subscription, setSubscription] = useState<Subscription | null>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        fetchSubscription();
    }, []);

    const fetchSubscription = async () => {
        try {
            const data = await subscriptionsApi.getCurrentSubscription();
            setSubscription(data);
        } catch (err) {
            console.error('Failed to fetch subscription:', err);
            toast.error('Failed to load subscription');
        } finally {
            setLoading(false);
        }
    };

    const handleOpenPortal = async () => {
        setActionLoading(true);
        try {
            const { portal_url } = await subscriptionsApi.getPortalLink();
            window.location.href = portal_url;
        } catch (err) {
            console.error('Failed to get portal link:', err);
            toast.error('Failed to open billing portal');
            setActionLoading(false);
        }
    };

    const handleCancel = async () => {
        if (!confirm('Are you sure you want to cancel? Your subscription will remain active until the end of the billing period.')) {
            return;
        }

        setActionLoading(true);
        try {
            const updated = await subscriptionsApi.cancelSubscription();
            setSubscription(updated);
            toast.success('Subscription will be canceled at period end');
        } catch (err) {
            console.error('Failed to cancel subscription:', err);
            toast.error('Failed to cancel subscription');
        } finally {
            setActionLoading(false);
        }
    };

    const handleReactivate = async () => {
        setActionLoading(true);
        try {
            const updated = await subscriptionsApi.reactivateSubscription();
            setSubscription(updated);
            toast.success('Subscription reactivated');
        } catch (err) {
            console.error('Failed to reactivate subscription:', err);
            toast.error('Failed to reactivate subscription');
        } finally {
            setActionLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (!subscription) {
        return (
            <div className="container max-w-4xl py-8">
                <Card>
                    <CardHeader>
                        <CardTitle>No Subscription Found</CardTitle>
                        <CardDescription>You don&apos;t have an active subscription.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Link href="/pricing">
                            <Button>View Plans</Button>
                        </Link>
                    </CardContent>
                </Card>
            </div>
        );
    }

    const statusColor = subscription.status === 'active' ? 'bg-green-500' : 'bg-gray-500';

    return (
        <div className="container max-w-4xl py-8 space-y-6">
            <div>
                <h1 className="text-3xl font-bold mb-2">Subscription</h1>
                <p className="text-muted-foreground">Manage your subscription and billing</p>
            </div>

            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle className="capitalize">{subscription.plan_type} Plan</CardTitle>
                        <Badge className={statusColor}>{subscription.status}</Badge>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <p className="text-sm text-muted-foreground">Current Period</p>
                        <p className="font-medium">
                            {format(new Date(subscription.current_period_start), 'MMM d, yyyy')} -{' '}
                            {format(new Date(subscription.current_period_end), 'MMM d, yyyy')}
                        </p>
                    </div>

                    {subscription.cancel_at_period_end && (
                        <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-md">
                            <p className="text-sm text-yellow-800 dark:text-yellow-200">
                                Your subscription will be canceled on{' '}
                                {format(new Date(subscription.current_period_end), 'MMM d, yyyy')}
                            </p>
                        </div>
                    )}

                    <div className="flex gap-4 pt-4">
                        {subscription.stripe_customer_id && (
                            <Button
                                onClick={handleOpenPortal}
                                disabled={actionLoading}
                                variant="outline"
                            >
                                {actionLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ExternalLink className="mr-2 h-4 w-4" />}
                                Manage Billing
                            </Button>
                        )}

                        {subscription.plan_type !== 'free' && (
                            <>
                                {subscription.cancel_at_period_end ? (
                                    <Button onClick={handleReactivate} disabled={actionLoading}>
                                        Reactivate Subscription
                                    </Button>
                                ) : (
                                    <Button variant="destructive" onClick={handleCancel} disabled={actionLoading}>
                                        Cancel Subscription
                                    </Button>
                                )}
                            </>
                        )}

                        {subscription.plan_type === 'free' && (
                            <Link href="/pricing">
                                <Button>Upgrade Plan</Button>
                            </Link>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
