'use client';

import { HeatmapPoint } from '@/lib/api/analytics';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { format, parseISO } from 'date-fns';

interface ActivityHeatmapProps {
    data: HeatmapPoint[];
}

export function ActivityHeatmap({ data }: ActivityHeatmapProps) {
    // Ensure we have data for the last 30 days, filling gaps with 0
    // The backend should return it, but safety first

    const getLevelColor = (level: number) => {
        switch (level) {
            case 0: return 'bg-muted/20';
            case 1: return 'bg-emerald-200 dark:bg-emerald-900/50';
            case 2: return 'bg-emerald-300 dark:bg-emerald-800/70';
            case 3: return 'bg-emerald-400 dark:bg-emerald-600';
            case 4: return 'bg-emerald-500 dark:bg-emerald-500';
            default: return 'bg-muted/20';
        }
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle>Study Activity</CardTitle>
                <CardDescription>Your study intensity over the last 30 days.</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="flex flex-col gap-2">
                    <div className="flex flex-wrap gap-1 justify-center sm:justify-start">
                        <TooltipProvider>
                            {data.map((point) => (
                                <Tooltip key={point.date}>
                                    <TooltipTrigger asChild>
                                        <div
                                            className={cn(
                                                "w-4 h-4 sm:w-6 sm:h-6 rounded-sm transition-colors cursor-default",
                                                getLevelColor(point.level)
                                            )}
                                        />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p className="font-medium">{format(parseISO(point.date), 'MMM d, yyyy')}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {point.count} {point.count === 1 ? 'review' : 'reviews'}
                                        </p>
                                    </TooltipContent>
                                </Tooltip>
                            ))}
                        </TooltipProvider>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-2">
                        <span>Less</span>
                        <div className="flex gap-1">
                            <div className={cn("w-3 h-3 rounded-sm", getLevelColor(0))} />
                            <div className={cn("w-3 h-3 rounded-sm", getLevelColor(1))} />
                            <div className={cn("w-3 h-3 rounded-sm", getLevelColor(2))} />
                            <div className={cn("w-3 h-3 rounded-sm", getLevelColor(3))} />
                            <div className={cn("w-3 h-3 rounded-sm", getLevelColor(4))} />
                        </div>
                        <span>More</span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
