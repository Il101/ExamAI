'use client';

import { useEffect, useState } from 'react';
import { Plan, subscriptionsApi } from '@/lib/api/subscriptions';
import { PricingCard } from '@/components/pricing/pricing-card';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function PricingPage() {
    const [plans, setPlans] = useState<Plan[]>([]);
    const [currentPlan, setCurrentPlan] = useState<string>('free');
    const [loading, setLoading] = useState(true);
    const [checkoutLoading, setCheckoutLoading] = useState(false);
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
                        // User might not have a subscription yet
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
            const successUrl = `${origin}/subscription/success`;
            const cancelUrl = `${origin}/pricing`;

            const { checkout_url } = await subscriptionsApi.createCheckout(
                planId,
                successUrl,
                cancelUrl
            );

            // Redirect to Stripe Checkout
            window.location.href = checkout_url;
        } catch (err) {
            console.error('Failed to create checkout:', err);
            toast.error('Failed to start checkout');
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
        <div className="container max-w-7xl py-8 space-y-8">
            <div className="text-center space-y-4">
                <h1 className="text-4xl font-bold">Choose Your Plan</h1>
                <p className="text-xl text-muted-foreground">
                    Select the plan that best fits your study needs
                </p>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                {plans.map((plan) => (
                    <PricingCard
                        key={plan.id}
                        plan={plan}
                        currentPlan={currentPlan}
                        onSelect={handleSelectPlan}
                        isLoading={checkoutLoading}
                    />
                ))}
            </div>

            <div className="text-center text-sm text-muted-foreground">
                <p>All plans include a 14-day money-back guarantee. Cancel anytime.</p>
            </div>
        </div>
    );
}
