'use client';

import { Plan } from '@/lib/api/subscriptions';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, X, Sparkles, Zap, Crown, Users } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PricingCardProps {
    plan: Plan;
    currentPlan?: string;
    onSelect: (planId: string) => void;
    isLoading?: boolean;
    billingPeriod: 'monthly' | 'yearly';
}

const planIcons: Record<string, React.ReactNode> = {
    free: <Zap className="h-6 w-6" />,
    pro: <Sparkles className="h-6 w-6" />,
    premium: <Crown className="h-6 w-6" />,
    team: <Users className="h-6 w-6" />,
};

const planColors: Record<string, string> = {
    free: 'from-slate-500 to-slate-600',
    pro: 'from-violet-500 to-purple-600',
    premium: 'from-amber-500 to-orange-600',
    team: 'from-emerald-500 to-teal-600',
};

const planDescriptions: Record<string, string> = {
    free: 'Get started with AI-powered studying',
    pro: 'For serious students who want more',
    premium: 'Unlimited power for power users',
    team: 'Perfect for study groups of up to 5',
};

export function PricingCard({ plan, currentPlan, onSelect, isLoading, billingPeriod }: PricingCardProps) {
    const isCurrent = currentPlan === plan.id;
    const isPaid = (plan.price?.monthly?.amount ?? 0) > 0 || (plan.price?.amount ?? 0) > 0;

    // Handle both old and new price formats
    const getPrice = () => {
        if (plan.price?.monthly && plan.price?.yearly) {
            return billingPeriod === 'yearly'
                ? plan.price.yearly.amount
                : plan.price.monthly.amount;
        }
        return plan.price?.amount || 0;
    };

    const price = getPrice();
    const yearlyMonthlyEquivalent = plan.price?.yearly
        ? (plan.price.yearly.amount / 12).toFixed(2)
        : null;

    const features = [
        {
            name: plan.limits?.max_exams === null ? 'Unlimited exams' : `${plan.limits?.max_exams || 2} exams`,
            included: true
        },
        {
            name: plan.limits?.max_topics_per_exam === null ? 'Unlimited topics' : `${plan.limits?.max_topics_per_exam || 8} topics per exam`,
            included: true
        },
        {
            name: plan.limits?.daily_tutor_messages === null ? 'Unlimited AI tutor' : `${plan.limits?.daily_tutor_messages || 15} tutor messages/day`,
            included: true
        },
        { name: 'FSRS spaced repetition', included: plan.features?.spaced_repetition !== false },
        { name: 'Advanced analytics', included: plan.features?.advanced_analytics },
        { name: 'Export to PDF', included: plan.features?.export_pdf },
        { name: 'Priority generation', included: plan.features?.priority_generation },
        { name: 'Priority support', included: plan.features?.priority_support },
        ...(plan.id === 'team' ? [{ name: `${plan.limits?.max_team_members || 5} team members`, included: true }] : []),
    ];

    return (
        <Card
            className={cn(
                "relative flex flex-col overflow-hidden transition-all duration-300 hover:scale-[1.02]",
                plan.popular
                    ? "border-2 border-primary shadow-xl shadow-primary/20"
                    : "border border-border/50 hover:border-border",
                plan.id === 'team' && "md:col-span-2 lg:col-span-1"
            )}
        >
            {/* Gradient header */}
            <div className={cn(
                "h-2 w-full bg-gradient-to-r",
                planColors[plan.id] || planColors.free
            )} />

            {plan.popular && (
                <Badge
                    className="absolute top-4 right-4 bg-primary text-primary-foreground shadow-lg"
                >
                    Most Popular
                </Badge>
            )}

            <CardHeader className="pb-4">
                <div className={cn(
                    "mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br text-white",
                    planColors[plan.id] || planColors.free
                )}>
                    {planIcons[plan.id]}
                </div>
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <CardDescription className="text-base">
                    {plan.description || planDescriptions[plan.id]}
                </CardDescription>
            </CardHeader>

            <CardContent className="flex-1 space-y-6">
                {/* Pricing */}
                <div className="space-y-1">
                    {price === 0 ? (
                        <div className="flex items-baseline gap-1">
                            <span className="text-4xl font-bold">Free</span>
                            <span className="text-muted-foreground">forever</span>
                        </div>
                    ) : (
                        <>
                            <div className="flex items-baseline gap-1">
                                <span className="text-4xl font-bold">€{price}</span>
                                <span className="text-muted-foreground">
                                    /{billingPeriod === 'yearly' ? 'year' : 'month'}
                                </span>
                            </div>
                            {billingPeriod === 'yearly' && yearlyMonthlyEquivalent && (
                                <p className="text-sm text-muted-foreground">
                                    €{yearlyMonthlyEquivalent}/month billed annually
                                </p>
                            )}
                            {billingPeriod === 'yearly' && plan.price?.monthly && plan.price?.yearly && (
                                <Badge variant="secondary" className="mt-2">
                                    Save {Math.round((1 - plan.price.yearly.amount / (plan.price.monthly.amount * 12)) * 100)}%
                                </Badge>
                            )}
                        </>
                    )}
                </div>

                {/* Features */}
                <ul className="space-y-3">
                    {features.map((feature, index) => (
                        <li key={index} className="flex items-start gap-3">
                            {feature.included ? (
                                <Check className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
                            ) : (
                                <X className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground/40" />
                            )}
                            <span className={cn(
                                "text-sm",
                                !feature.included && "text-muted-foreground/60"
                            )}>
                                {feature.name}
                            </span>
                        </li>
                    ))}
                </ul>
            </CardContent>

            <CardFooter className="pt-4">
                {isCurrent ? (
                    <Button
                        variant="outline"
                        className="w-full"
                        disabled
                    >
                        Current Plan
                    </Button>
                ) : isPaid ? (
                    <Button
                        className={cn(
                            "w-full bg-gradient-to-r text-white shadow-lg transition-all hover:shadow-xl",
                            planColors[plan.id] || planColors.pro
                        )}
                        onClick={() => onSelect(plan.id)}
                        disabled={isLoading}
                    >
                        {isLoading ? 'Processing...' : plan.id === 'team' ? 'Start Team Trial' : 'Get Started'}
                    </Button>
                ) : (
                    <Button
                        variant="outline"
                        className="w-full"
                        onClick={() => onSelect(plan.id)}
                    >
                        Get Started Free
                    </Button>
                )}
            </CardFooter>
        </Card>
    );
}
