'use client';

import { Plan } from '@/lib/api/subscriptions';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check } from 'lucide-react';

interface PricingCardProps {
    plan: Plan;
    currentPlan?: string;
    onSelect: (planId: string) => void;
    isLoading?: boolean;
}

export function PricingCard({ plan, currentPlan, onSelect, isLoading }: PricingCardProps) {
    const isCurrent = currentPlan === plan.id;
    const isPaid = plan.price.amount > 0;

    return (
        <Card className={`relative ${plan.popular ? 'border-primary shadow-lg' : ''}`}>
            {plan.popular && (
                <Badge className="absolute top-0 right-0 transform translate-x-2 -translate-y-2">Popular</Badge>
            )}

            <CardHeader>
                <CardTitle>{plan.name}</CardTitle>
                <CardDescription>
                    {plan.price.amount === 0 ? (
                        <span className="text-3xl font-bold">Free</span>
                    ) : (
                        <div>
                            <span className="text-3xl font-bold">€{plan.price.amount}</span>
                            <span className="text-muted-foreground">/{plan.price.billing_period}</span>
                        </div>
                    )}
                </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
                <ul className="space-y-2">
                    {plan.features.max_exams && (
                        <li className="flex items-center">
                            <Check className="mr-2 h-4 w-4 text-primary" />
                            <span>
                                {plan.features.max_exams === null ? 'Unlimited' : plan.features.max_exams} exams
                            </span>
                        </li>
                    )}
                    <li className="flex items-center">
                        <Check className="mr-2 h-4 w-4 text-primary" />
                        <span>{plan.features.ai_model}</span>
                    </li>
                    {plan.features.advanced_analytics && (
                        <li className="flex items-center">
                            <Check className="mr-2 h-4 w-4 text-primary" />
                            <span>Advanced Analytics</span>
                        </li>
                    )}
                    {plan.features.export && (
                        <li className="flex items-center">
                            <Check className="mr-2 h-4 w-4 text-primary" />
                            <span>Export to PDF</span>
                        </li>
                    )}
                    {plan.features.priority_support && (
                        <li className="flex items-center">
                            <Check className="mr-2 h-4 w-4 text-primary" />
                            <span>Priority Support</span>
                        </li>
                    )}
                </ul>
            </CardContent>

            <CardFooter>
                {isCurrent ? (
                    <Button variant="outline" className="w-full" disabled>
                        Current Plan
                    </Button>
                ) : isPaid ? (
                    <Button
                        className="w-full"
                        onClick={() => onSelect(plan.id)}
                        disabled={isLoading}
                    >
                        {isLoading ? 'Loading...' : 'Upgrade'}
                    </Button>
                ) : (
                    <Button variant="outline" className="w-full" disabled>
                        Free Plan
                    </Button>
                )}
            </CardFooter>
        </Card>
    );
}
