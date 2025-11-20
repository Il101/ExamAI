'use client';

import { useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function SubscriptionSuccessPage() {
    const router = useRouter();

    useEffect(() => {
        // Auto-redirect after 5 seconds
        const timer = setTimeout(() => {
            router.push('/dashboard');
        }, 5000);

        return () => clearTimeout(timer);
    }, [router]);

    return (
        <div className="container max-w-2xl py-16">
            <Card>
                <CardHeader className="text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/20">
                        <CheckCircle className="h-10 w-10 text-green-600 dark:text-green-400" />
                    </div>
                    <CardTitle className="text-2xl">Subscription Activated!</CardTitle>
                    <CardDescription>
                        Your subscription has been successfully activated. You now have access to all premium features.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 text-center">
                    <p className="text-sm text-muted-foreground">
                        Redirecting to dashboard in 5 seconds...
                    </p>
                    <div className="flex gap-4 justify-center">
                        <Link href="/dashboard">
                            <Button>Go to Dashboard</Button>
                        </Link>
                        <Link href="/subscription">
                            <Button variant="outline">View Subscription</Button>
                        </Link>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
