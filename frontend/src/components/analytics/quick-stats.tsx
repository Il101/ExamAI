'use client';

import { Card } from '@/components/ui/card';
import { Flame, BookOpen, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuickStatsProps {
    streak: number;
    totalLearned: number;
    isLoading?: boolean;
}

export function QuickStats({ streak, totalLearned, isLoading }: QuickStatsProps) {
    return (
        <div className="grid grid-cols-2 gap-4">
            <Card className="p-5 flex flex-col items-center text-center transition-all hover:translate-y-[-2px] hover:shadow-md cursor-default border-orange-500/10 bg-orange-500/[0.02]">
                <div className={cn(
                    "p-3 rounded-2xl mb-3 transition-colors",
                    streak > 0 ? "bg-orange-500 text-white shadow-lg shadow-orange-500/20" : "bg-muted text-muted-foreground"
                )}>
                    <Flame className={cn("h-6 w-6", streak > 3 && "animate-pulse")} />
                </div>
                <div className="space-y-1">
                    <p className="text-2xl font-black tracking-tight">
                        {isLoading ? '--' : streak}
                    </p>
                    <p className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground">
                        Day Streak
                    </p>
                </div>
            </Card>

            <Card className="p-5 flex flex-col items-center text-center transition-all hover:translate-y-[-2px] hover:shadow-md cursor-default border-blue-500/10 bg-blue-500/[0.02]">
                <div className={cn(
                    "p-3 rounded-2xl mb-3 bg-blue-500 text-white shadow-lg shadow-blue-500/20"
                )}>
                    <BookOpen className="h-6 w-6" />
                </div>
                <div className="space-y-1">
                    <p className="text-2xl font-black tracking-tight">
                        {isLoading ? '--' : totalLearned}
                    </p>
                    <p className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground">
                        Cards Mastered
                    </p>
                </div>
            </Card>
        </div>
    );
}
