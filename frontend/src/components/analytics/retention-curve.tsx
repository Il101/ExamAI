'use client';

import { RetentionPoint } from '@/lib/api/analytics';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface RetentionCurveChartProps {
    data: RetentionPoint[];
}

export function RetentionCurveChart({ data }: RetentionCurveChartProps) {
    // SVG dimensions
    const width = 500;
    const height = 200;
    const padding = 20;

    // Scales
    const maxDays = Math.max(...data.map(d => d.days_since_review), 30);

    const getX = (days: number) => {
        return padding + (days / maxDays) * (width - 2 * padding);
    };

    const getY = (rate: number) => {
        return height - padding - (rate * (height - 2 * padding));
    };

    // Generate path
    const points = data.map(d => `${getX(d.days_since_review)},${getY(d.retention_rate)}`).join(' ');
    const pathD = `M ${points}`;

    // Area path (close the loop)
    const areaPathD = `${pathD} L ${getX(data[data.length - 1].days_since_review)},${height - padding} L ${getX(data[0].days_since_review)},${height - padding} Z`;

    return (
        <Card>
            <CardHeader>
                <CardTitle>Retention Curve</CardTitle>
                <CardDescription>Estimated memory retention over time.</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="w-full overflow-hidden">
                    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
                        {/* Grid lines */}
                        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="currentColor" strokeOpacity="0.2" />
                        <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="currentColor" strokeOpacity="0.2" />

                        {/* Area */}
                        <path d={areaPathD} fill="currentColor" className="text-primary/20" />

                        {/* Line */}
                        <path d={pathD} fill="none" stroke="currentColor" strokeWidth="2" className="text-primary" />

                        {/* Points */}
                        {data.map((d) => (
                            <circle
                                key={d.days_since_review}
                                cx={getX(d.days_since_review)}
                                cy={getY(d.retention_rate)}
                                r="4"
                                className="fill-background stroke-primary"
                                strokeWidth="2"
                            />
                        ))}

                        {/* Labels */}
                        <text x={width - padding} y={height - 5} textAnchor="end" fontSize="10" fill="currentColor" className="text-muted-foreground">Days</text>
                        <text x={5} y={padding} textAnchor="start" fontSize="10" fill="currentColor" className="text-muted-foreground">Retention</text>
                    </svg>
                </div>
            </CardContent>
        </Card>
    );
}
