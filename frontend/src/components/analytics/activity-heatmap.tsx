'use client';

import { Tooltip } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { addDays, format, startOfWeek, subWeeks } from 'date-fns';

interface HeatmapPoint {
  date: string;
  count: number;
  level: number;
}

interface ActivityHeatmapProps {
  data: HeatmapPoint[];
}

export function ActivityHeatmap({ data }: ActivityHeatmapProps) {
  // Generate calendar grid for last 12 weeks
  const today = new Date();
  const startDate = startOfWeek(subWeeks(today, 11)); // Start 11 weeks ago

  // Create a map for quick lookup
  const dataMap = new Map(data.map(d => [new Date(d.date).toISOString().split('T')[0], d]));

  const weeks = [];
  let currentDate = startDate;

  for (let i = 0; i < 12; i++) {
    const week = [];
    for (let j = 0; j < 7; j++) {
      const dateStr = currentDate.toISOString().split('T')[0];
      // Get data for this date, or use defaults
      // Note: We destruct 'date' from point to avoid conflict with our 'date' property
      const pointData = dataMap.get(dateStr);
      const { date: _, ...rest } = pointData || { date: '', count: 0, level: 0 };

      week.push({
        date: currentDate,
        ...rest
      });
      currentDate = addDays(currentDate, 1);
    }
    weeks.push(week);
  }

  const getLevelColor = (level: number) => {
    switch (level) {
      case 0: return 'bg-muted dark:bg-muted/50';
      case 1: return 'bg-blue-100 dark:bg-blue-900/20';
      case 2: return 'bg-blue-300 dark:bg-blue-700/40';
      case 3: return 'bg-blue-500 dark:bg-blue-500/60';
      case 4: return 'bg-blue-600 dark:bg-blue-400';
      default: return 'bg-muted';
    }
  };

  return (
    <div className="w-full overflow-x-auto">
      <div className="flex gap-1 min-w-max">
        {/* Week days labels */}
        <div className="flex flex-col gap-1 mr-2 text-xs text-gray-400 pt-6">
          <div className="h-3">Mon</div>
          <div className="h-3"></div>
          <div className="h-3">Wed</div>
          <div className="h-3"></div>
          <div className="h-3">Fri</div>
        </div>

        {/* Grid */}
        {weeks.map((week, wIndex) => (
          <div key={wIndex} className="flex flex-col gap-1">
            {/* Month label if first week of month */}
            <div className="h-4 text-xs text-gray-400">
              {week[0].date.getDate() <= 7 ? format(week[0].date, 'MMM') : ''}
            </div>

            {week.map((day, dIndex) => (
              <div
                key={dIndex}
                className={cn(
                  "h-3 w-3 rounded-sm transition-colors hover:ring-1 hover:ring-gray-400",
                  getLevelColor(day.level)
                )}
                title={`${format(day.date, 'MMM d, yyyy')}: ${day.count} reviews`}
              />
            ))}
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2 mt-4 text-[10px] text-muted-foreground uppercase tracking-wider">
        <span>Less active</span>
        <div className="flex gap-1">
          <div className="h-2 w-2 rounded-sm bg-muted" />
          <div className="h-2 w-2 rounded-sm bg-blue-100 dark:bg-blue-900/20" />
          <div className="h-2 w-2 rounded-sm bg-blue-300 dark:bg-blue-700/40" />
          <div className="h-2 w-2 rounded-sm bg-blue-500 dark:bg-blue-500/60" />
          <div className="h-2 w-2 rounded-sm bg-blue-600 dark:bg-blue-400" />
        </div>
        <span>More active</span>
      </div>
    </div>
  );
}
