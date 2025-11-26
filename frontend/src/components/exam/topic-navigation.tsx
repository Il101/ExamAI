'use client';

import { useRouter } from 'next/navigation';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface TopicNavigationProps {
    currentIndex: number;
    totalTopics: number;
    prevTopicId?: string | null;
    nextTopicId?: string | null;
    className?: string;
}

export function TopicNavigation({
    currentIndex,
    totalTopics,
    prevTopicId,
    nextTopicId,
    className,
}: TopicNavigationProps) {
    const router = useRouter();

    const handleKeyboard = (e: KeyboardEvent) => {
        if (e.key === 'ArrowLeft' && prevTopicId) {
            router.push(`/dashboard/topics/${prevTopicId}`);
        } else if (e.key === 'ArrowRight' && nextTopicId) {
            router.push(`/dashboard/topics/${nextTopicId}`);
        } else if (e.key === 'j' && nextTopicId) {
            router.push(`/dashboard/topics/${nextTopicId}`);
        } else if (e.key === 'k' && prevTopicId) {
            router.push(`/dashboard/topics/${prevTopicId}`);
        }
    };

    // Add keyboard listeners
    if (typeof window !== 'undefined') {
        window.addEventListener('keydown', handleKeyboard);
    }

    return (
        <div className={cn('flex items-center justify-between py-6 border-t', className)}>
            <Button
                variant="outline"
                size="lg"
                disabled={!prevTopicId}
                onClick={() => prevTopicId && router.push(`/dashboard/topics/${prevTopicId}`)}
                className="gap-2"
            >
                <ArrowLeft className="h-4 w-4" />
                Previous
            </Button>

            <div className="text-sm text-muted-foreground">
                Topic <span className="font-medium text-foreground">{currentIndex + 1}</span> of {totalTopics}
            </div>

            <Button
                variant="outline"
                size="lg"
                disabled={!nextTopicId}
                onClick={() => nextTopicId && router.push(`/dashboard/topics/${nextTopicId}`)}
                className="gap-2"
            >
                Next
                <ArrowRight className="h-4 w-4" />
            </Button>
        </div>
    );
}
