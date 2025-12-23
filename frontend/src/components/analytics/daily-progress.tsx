'use client';

import { DailyProgress } from '@/lib/api/analytics';
import { format, parseISO } from 'date-fns';

interface DailyProgressChartProps {
    data: DailyProgress[];
}

export function DailyProgressChart({ data }: DailyProgressChartProps) {
    // Find max value for scaling
    const maxCards = Math.max(...data.map(d => d.cards_reviewed), 1);

    return (
        <div className="h-[240px] w-full flex items-end justify-between gap-2 pt-8 pb-2">
            {data.map((day) => {
                const heightPercentage = Math.max((day.cards_reviewed / maxCards) * 100, 2);
                const learnedHeightPercentage = day.cards_reviewed > 0
                    ? (day.cards_learned / day.cards_reviewed) * 100
                    : 0;

                return (
                    <div key={day.date} className="flex flex-col items-center gap-2 flex-1 group relative">
                        {/* Tooltip-like info on hover */}
                        <div className="absolute bottom-[110%] left-1/2 -translate-x-1/2 mb-2 hidden group-hover:flex flex-col bg-popover text-popover-foreground text-[10px] p-2 rounded shadow-xl border z-20 min-w-[100px]">
                            <span className="font-bold border-bottom pb-1 mb-1 border-border">{format(parseISO(day.date), 'MMMM d')}</span>
                            <div className="flex justify-between gap-2">
                                <span className="text-muted-foreground">Reviewed:</span>
                                <span className="font-medium text-blue-500">{day.cards_reviewed}</span>
                            </div>
                            <div className="flex justify-between gap-2">
                                <span className="text-muted-foreground">Learned:</span>
                                <span className="font-medium text-green-500">{day.cards_learned}</span>
                            </div>
                            <div className="flex justify-between gap-2">
                                <span className="text-muted-foreground">Time:</span>
                                <span>{day.minutes_studied}m</span>
                            </div>
                        </div>

                        <div className="relative w-full max-w-[32px] bg-muted/50 rounded-t-sm overflow-hidden transition-all hover:bg-muted/80" style={{ height: `${heightPercentage}%` }}>
                            {/* Learned (Overlay) */}
                            <div
                                className="absolute bottom-0 w-full bg-blue-500 dark:bg-blue-600 transition-all"
                                style={{ height: `${learnedHeightPercentage}%` }}
                            />
                        </div>
                        <span className="text-[10px] text-muted-foreground font-medium uppercase">
                            {format(parseISO(day.date), 'EEE')}
                        </span>
                    </div>
                );
            })}
        </div>
    );
}
