'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { Brain } from 'lucide-react';

interface MemoryHealthScoreProps {
    score: number; // 0-100
    isLoading?: boolean;
}

export function MemoryHealthScore({ score, isLoading }: MemoryHealthScoreProps) {
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        if (!isLoading) {
            const timer = setTimeout(() => setProgress(score), 100);
            return () => clearTimeout(timer);
        }
    }, [score, isLoading]);

    const size = 200;
    const strokeWidth = 12;
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (progress / 100) * circumference;

    const getColor = (s: number) => {
        if (s < 50) return 'text-red-500';
        if (s < 80) return 'text-orange-500';
        return 'text-green-500';
    };

    const getBgColor = (s: number) => {
        if (s < 50) return 'bg-red-500/10';
        if (s < 80) return 'bg-orange-500/10';
        return 'bg-green-500/10';
    };

    return (
        <div className="flex flex-col items-center justify-center p-6 relative">
            <div className="relative" style={{ width: size, height: size }}>
                {/* Background Track */}
                <svg className="w-full h-full -rotate-90">
                    <circle
                        cx={size / 2}
                        cy={size / 2}
                        r={radius}
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={strokeWidth}
                        className="text-muted/20"
                    />
                    {/* Progress Circle */}
                    <circle
                        cx={size / 2}
                        cy={size / 2}
                        r={radius}
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={strokeWidth}
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        strokeLinecap="round"
                        className={cn(
                            "transition-all duration-1000 ease-out",
                            getColor(progress)
                        )}
                    />
                </svg>

                {/* Center Content */}
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                    <div className={cn(
                        "p-3 rounded-full mb-1",
                        getBgColor(progress)
                    )}>
                        <Brain className={cn("h-6 w-6", getColor(progress))} />
                    </div>
                    <span className="text-4xl font-bold tracking-tighter">
                        {isLoading ? '--' : `${Math.round(progress)}%`}
                    </span>
                    <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                        Memory Health
                    </span>
                </div>
            </div>

            <p className="mt-4 text-sm text-muted-foreground text-center max-w-[240px]">
                {score >= 90
                    ? "Your brain is in top shape! Information is safely stored."
                    : score >= 75
                        ? "Good retention. Keep going to reach mastery!"
                        : "Time for a quick refresh to avoid forgetting."}
            </p>
        </div>
    );
}
