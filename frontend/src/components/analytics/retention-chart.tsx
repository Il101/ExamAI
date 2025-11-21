'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

interface RetentionPoint {
  days_since_review: number;
  retention_rate: number;
}

interface RetentionChartProps {
  data: RetentionPoint[];
}

export function RetentionChart({ data }: RetentionChartProps) {
  const formattedData = data.map(point => ({
    ...point,
    retention_percent: Math.round(point.retention_rate * 100)
  }));

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={formattedData}
          margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="days_since_review"
            label={{ value: 'Days Since Review', position: 'insideBottom', offset: -5 }}
          />
          <YAxis
            domain={[0, 100]}
            label={{ value: 'Retention %', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            formatter={(value: number) => [`${value}%`, 'Retention']}
            labelFormatter={(label: number) => `${label} days since review`}
          />
          <ReferenceLine y={90} label="Target (90%)" stroke="green" strokeDasharray="3 3" />
          <Line
            type="monotone"
            dataKey="retention_percent"
            stroke="#2563eb"
            strokeWidth={3}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
