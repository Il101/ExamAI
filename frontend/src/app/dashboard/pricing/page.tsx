'use client';

import { useEffect, useState } from 'react';
import { Plan, subscriptionsApi } from '@/lib/api/subscriptions';
import { PricingCard } from '@/components/pricing/pricing-card';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Loader2, Sparkles, Shield, Zap, MessageCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export default function PricingPage() {
    const [plans, setPlans] = useState<Plan[]>([]);
    const [currentPlan, setCurrentPlan] = useState<string>('free');
    const [loading, setLoading] = useState(true);
    const [checkoutLoading, setCheckoutLoading] = useState(false);
    const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('yearly');
    const { user } = useAuthStore();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const plansData = await subscriptionsApi.getPlans();
                setPlans(plansData);

                if (user) {
                    try {
                        const subscription = await subscriptionsApi.getCurrentSubscription();
                        setCurrentPlan(subscription.plan_type);
                    } catch (err) {
                        console.error('Failed to fetch subscription:', err);
                    }
                }
            } catch (err) {
                console.error('Failed to fetch plans:', err);
                toast.error('Failed to load plans');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [user]);

    const handleSelectPlan = async (planId: string) => {
        if (!user) {
            toast.error('Please sign in to upgrade');
            return;
        }

        setCheckoutLoading(true);
        try {
            const origin = typeof window !== 'undefined' ? window.location.origin : '';
            const successUrl = `${origin}/dashboard?upgrade=success`;
            const cancelUrl = `${origin}/dashboard/pricing`;

            const { checkout_url } = await subscriptionsApi.createCheckout(
                planId,
                successUrl,
                cancelUrl,
                billingPeriod
            );

            // Use Lemon Squeezy Overlay
            console.log('Attempting overlay with URL:', checkout_url);

            // Helper to check for LemonSqueezy with retries
            const openOverlay = async (retries = 3) => {
                // @ts-ignore
                if (window.LemonSqueezy) {
                    console.log('LemonSqueezy object found, opening overlay...');
                    // @ts-ignore
                    window.LemonSqueezy.Url.Open(checkout_url);
                    return true;
                }

                if (retries > 0) {
                    console.log(`LemonSqueezy not found, retrying in 300ms... (${retries} retries left)`);
                    await new Promise(resolve => setTimeout(resolve, 300));
                    return openOverlay(retries - 1);
                }

                return false;
            };

            const success = await openOverlay();

            if (!success) {
                console.warn('LemonSqueezy object NOT found after retries, falling back to redirect');
                window.location.href = checkout_url;
            }
        } catch (err) {
            console.error('Failed to create checkout:', err);
            toast.error('Failed to start checkout');
        } finally {
            setCheckoutLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    return (
        <div className="space-y-16">
            {/* Hero Section */}
            <div className="text-center space-y-6">
                <Badge variant="secondary" className="px-4 py-1.5">
                    <Sparkles className="mr-2 h-3.5 w-3.5" />
                    Simple, transparent pricing
                </Badge>
                <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
                    Choose the plan that fits your
                    <span className="bg-gradient-to-r from-violet-500 to-purple-600 bg-clip-text text-transparent"> study goals</span>
                </h1>
                <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                    Start free, upgrade when you need more. All plans include our core AI features.
                    Cancel anytime.
                </p>

                {/* Billing Toggle */}
                <div className="flex items-center justify-center pt-8">
                    <div className="flex items-center gap-6 bg-muted/50 p-1.5 rounded-full border border-border/50">
                        <label
                            onClick={() => setBillingPeriod('monthly')}
                            className={cn(
                                "px-4 py-1.5 rounded-full cursor-pointer transition-all duration-200 text-sm font-medium",
                                billingPeriod === 'monthly'
                                    ? "bg-white dark:bg-zinc-900 shadow-sm text-primary"
                                    : "text-muted-foreground hover:text-foreground"
                            )}
                        >
                            Monthly
                        </label>
                        <Switch
                            id="billing-toggle"
                            checked={billingPeriod === 'yearly'}
                            onCheckedChange={(checked: boolean) => setBillingPeriod(checked ? 'yearly' : 'monthly')}
                            className="data-[state=unchecked]:bg-zinc-300 dark:data-[state=unchecked]:bg-zinc-700"
                        />
                        <label
                            onClick={() => setBillingPeriod('yearly')}
                            className={cn(
                                "px-4 py-1.5 rounded-full cursor-pointer transition-all duration-200 text-sm font-medium flex items-center gap-2",
                                billingPeriod === 'yearly'
                                    ? "bg-white dark:bg-zinc-900 shadow-sm text-primary"
                                    : "text-muted-foreground hover:text-foreground"
                            )}
                        >
                            Yearly
                            <Badge variant="secondary" className="bg-green-500/10 text-green-600 border-none px-1.5 py-0 h-5">
                                -38%
                            </Badge>
                        </label>
                    </div>
                </div>
            </div>

            {/* Pricing Cards */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                {plans.map((plan) => (
                    <PricingCard
                        key={plan.id}
                        plan={plan}
                        currentPlan={currentPlan}
                        onSelect={handleSelectPlan}
                        isLoading={checkoutLoading}
                        billingPeriod={billingPeriod}
                    />
                ))}
            </div>

            {/* Trust Badges */}
            <div className="border-t pt-12">
                <div className="grid gap-8 md:grid-cols-3 text-center">
                    <div className="space-y-2">
                        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                            <Shield className="h-6 w-6 text-primary" />
                        </div>
                        <h3 className="font-semibold">14-Day Money Back</h3>
                        <p className="text-sm text-muted-foreground">
                            Not satisfied? Get a full refund within 14 days, no questions asked.
                        </p>
                    </div>
                    <div className="space-y-2">
                        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                            <Zap className="h-6 w-6 text-primary" />
                        </div>
                        <h3 className="font-semibold">Instant Access</h3>
                        <p className="text-sm text-muted-foreground">
                            Get immediate access to all features as soon as you upgrade.
                        </p>
                    </div>
                    <div className="space-y-2">
                        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                            <MessageCircle className="h-6 w-6 text-primary" />
                        </div>
                        <h3 className="font-semibold">Priority Support</h3>
                        <p className="text-sm text-muted-foreground">
                            Premium and Team plans get dedicated support within 24 hours.
                        </p>
                    </div>
                </div>
            </div>

            {/* FAQ Teaser */}
            <div className="text-center space-y-4 pb-8">
                <h2 className="text-2xl font-semibold">Have questions?</h2>
                <p className="text-muted-foreground">
                    Check out our <a href="/faq" className="text-primary underline hover:no-underline">FAQ</a> or{' '}
                    <a href="mailto:support@examai.pro" className="text-primary underline hover:no-underline">contact us</a>.
                </p>
            </div>
        </div>
    );
}
