'use client';

import { useEffect, useState } from 'react';
import { Subscription, subscriptionsApi, UsageResponse } from '@/lib/api/subscriptions';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, CreditCard, ExternalLink, Calendar, ShieldCheck, CheckCircle2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { formatDate } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';

export function BillingSettings() {
    const [subscription, setSubscription] = useState<Subscription | null>(null);
    const [usage, setUsage] = useState<UsageResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [subData, usageData] = await Promise.all([
                    subscriptionsApi.getCurrentSubscription(),
                    subscriptionsApi.getUsage()
                ]);
                setSubscription(subData);
                setUsage(usageData);
            } catch (err) {
                console.error('Failed to fetch billing data:', err);
                toast.error('Failed to load billing information');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    const handleManage = async () => {
        setActionLoading(true);
        try {
            // Priority: URL from subscription model, then API response or generic fallback
            let portalUrl = subscription?.customer_portal_url;

            if (!portalUrl) {
                const { portal_url } = await subscriptionsApi.getPortalLink();
                portalUrl = portal_url;
            }

            window.location.href = portalUrl!;
        } catch (err) {
            console.error('Failed to get portal link:', err);
            toast.error('Failed to open billing portal');
        } finally {
            setActionLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex h-48 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (!subscription) return null;

    const isFree = subscription.plan_type === 'free';

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>Current Plan</CardTitle>
                            <CardDescription>
                                You are currently on the <span className="font-semibold text-foreground uppercase">{subscription.plan_type}</span> plan.
                            </CardDescription>
                        </div>
                        <Badge variant={isFree ? "outline" : "default"} className="px-3 py-1">
                            {subscription.status.toUpperCase()}
                        </Badge>
                    </div>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="grid gap-4 md:grid-cols-2">
                        <div className="flex items-center p-4 border rounded-lg bg-muted/30">
                            <CreditCard className="h-5 w-5 mr-3 text-primary" />
                            <div>
                                <p className="text-sm font-medium">Billing Provider</p>
                                <p className="text-sm text-muted-foreground">Lemon Squeezy</p>
                            </div>
                        </div>
                        <div className="flex items-center p-4 border rounded-lg bg-muted/30">
                            <Calendar className="h-5 w-5 mr-3 text-primary" />
                            <div>
                                <p className="text-sm font-medium">Next Billing Date</p>
                                <p className="text-sm text-muted-foreground">
                                    {isFree ? 'Never' : formatDate(subscription.current_period_end)}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Usage Stats */}
                    {usage && (
                        <div className="space-y-4">
                            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Usage Statistics</h3>
                            <div className="grid gap-6 md:grid-cols-2">
                                <UsageCard
                                    label="Exams Created"
                                    current={usage.exams.current}
                                    limit={usage.exams.limit}
                                />
                                <UsageCard
                                    label="Tutor Messages"
                                    current={usage.tutor_messages.current}
                                    limit={usage.tutor_messages.limit}
                                />
                            </div>
                        </div>
                    )}

                    {!isFree && (
                        <div className="flex items-start p-4 border border-blue-100 bg-blue-50/50 rounded-lg dark:bg-blue-900/10 dark:border-blue-900/30">
                            <ShieldCheck className="h-5 w-5 mr-3 text-blue-600 dark:text-blue-400 mt-0.5" />
                            <div className="text-sm">
                                <p className="font-medium text-blue-900 dark:text-blue-300">Self-Service Billing</p>
                                <p className="text-blue-700 dark:text-blue-400 mt-1">
                                    Manage your payment methods, download invoices, or cancel your subscription through our secure billing portal.
                                </p>
                            </div>
                        </div>
                    )}

                    <div className="pt-2 flex flex-col sm:flex-row gap-3">
                        {!isFree ? (
                            <Button
                                onClick={handleManage}
                                disabled={actionLoading}
                                className="w-full sm:w-auto"
                            >
                                {actionLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ExternalLink className="mr-2 h-4 w-4" />}
                                Manage in Lemon Squeezy
                            </Button>
                        ) : (
                            <Button
                                variant="default"
                                onClick={() => window.location.href = '/dashboard/pricing'}
                                className="w-full sm:w-auto"
                            >
                                Upgrade Plan
                            </Button>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

function UsageCard({ label, current, limit }: { label: string; current: number; limit: number | null }) {
    const percentage = limit ? Math.min(100, (current / limit) * 100) : 0;
    const isOverLimit = limit ? current >= limit : false;

    return (
        <div className="space-y-2">
            <div className="flex justify-between text-sm">
                <span className="text-muted-foreground font-medium">{label}</span>
                <span className="font-bold">
                    {current} {limit ? `/ ${limit}` : '(Unlimited)'}
                </span>
            </div>
            {limit ? (
                <Progress value={percentage} className={isOverLimit ? "bg-red-100 dark:bg-red-900/20" : ""} />
            ) : (
                <div className="h-2 w-full bg-primary/10 rounded-full" />
            )}
            {isOverLimit && (
                <p className="text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    Limit reached. Please upgrade to create more.
                </p>
            )}
            {!isOverLimit && limit && percentage > 80 && (
                <p className="text-xs text-amber-500 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    Approaching limit ({Math.round(percentage)}%)
                </p>
            )}
        </div>
    );
}
