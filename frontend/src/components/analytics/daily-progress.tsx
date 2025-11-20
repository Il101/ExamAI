'use client';

import { DailyProgress } from '@/lib/api/analytics';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { format, parseISO } from 'date-fns';

interface DailyProgressChartProps {
    data: DailyProgress[];
}

export function DailyProgressChart({ data }: DailyProgressChartProps) {
    // Find max value for scaling
    const maxCards = Math.max(...data.map(d => d.cards_reviewed), 1);

    return (
        <Card>
            <CardHeader>
                <CardTitle>Daily Progress</CardTitle>
                <CardDescription>Cards reviewed and learned over the last 7 days.</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="h-[200px] w-full flex items-end justify-between gap-2 sm:gap-4 pt-4">
                    {data.map((day) => {
                        const heightPercentage = (day.cards_reviewed / maxCards) * 100;
                        const learnedHeightPercentage = (day.cards_learned / day.cards_reviewed) * 100;

                        return (
                            <div key={day.date} className="flex flex-col items-center gap-2 flex-1 group">
                                <div className="relative w-full max-w-[40px] bg-muted rounded-t-md overflow-hidden transition-all hover:opacity-80" style={{ height: `${heightPercentage}%` }}>
                                    {/* Reviewed (Background is muted, this is the total height) */}

                                    {/* Learned (Overlay) */}
                                    <div
                                        className="absolute bottom-0 w-full bg-primary transition-all"
                                        style={{ height: `${learnedHeightPercentage}%` }}
                                    />
                                </div>
                                <span className="text-xs text-muted-foreground truncate w-full text-center">
                                    {format(parseISO(day.date), 'EEE')}
                                </span>

                                {/* Tooltip-like info on hover (could be a real tooltip) */}
                                <div className="absolute bottom-full mb-2 hidden group-hover:flex flex-col bg-popover text-popover-foreground text-xs p-2 rounded shadow-md border z-10">
                                    <span className="font-bold">{format(parseISO(day.date), 'MMM d')}</span>
                                    <span>Reviewed: {day.cards_reviewed}</span>
                                    <span>Learned: {day.cards_learned}</span>
                                    <span>Time: {day.minutes_studied}m</span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </CardContent>
        </Card>
    );
}
