'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

interface StudyControlsProps {
    onRate: (rating: number) => void;
    disabled?: boolean;
}

export function StudyControls({ onRate, disabled }: StudyControlsProps) {
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (disabled) return;

            switch (e.key) {
                case '1':
                    onRate(1);
                    break;
                case '2':
                    onRate(2);
                    break;
                case '3':
                    onRate(3);
                    break;
                case '4':
                    onRate(4);
                    break;
                case ' ': // Spacebar
                case 'Enter':
                    // Maybe flip? But this component is for rating.
                    // Let's leave space/enter for flip in the parent component.
                    break;
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onRate, disabled]);

    return (
        <div className="grid grid-cols-4 gap-4 w-full max-w-2xl mt-8">
            <Button
                variant="outline"
                className="h-auto py-4 border-red-200 hover:bg-red-50 hover:text-red-700 dark:border-red-900 dark:hover:bg-red-900/20 dark:hover:text-red-400"
                onClick={() => onRate(1)}
                disabled={disabled}
            >
                <div className="flex flex-col items-center gap-1">
                    <span className="font-bold">Again</span>
                    <span className="text-xs text-muted-foreground hidden sm:inline">Key: 1</span>
                </div>
            </Button>

            <Button
                variant="outline"
                className="h-auto py-4 border-orange-200 hover:bg-orange-50 hover:text-orange-700 dark:border-orange-900 dark:hover:bg-orange-900/20 dark:hover:text-orange-400"
                onClick={() => onRate(2)}
                disabled={disabled}
            >
                <div className="flex flex-col items-center gap-1">
                    <span className="font-bold">Hard</span>
                    <span className="text-xs text-muted-foreground hidden sm:inline">Key: 2</span>
                </div>
            </Button>

            <Button
                variant="outline"
                className="h-auto py-4 border-blue-200 hover:bg-blue-50 hover:text-blue-700 dark:border-blue-900 dark:hover:bg-blue-900/20 dark:hover:text-blue-400"
                onClick={() => onRate(3)}
                disabled={disabled}
            >
                <div className="flex flex-col items-center gap-1">
                    <span className="font-bold">Good</span>
                    <span className="text-xs text-muted-foreground hidden sm:inline">Key: 3</span>
                </div>
            </Button>

            <Button
                variant="outline"
                className="h-auto py-4 border-green-200 hover:bg-green-50 hover:text-green-700 dark:border-green-900 dark:hover:bg-green-900/20 dark:hover:text-green-400"
                onClick={() => onRate(4)}
                disabled={disabled}
            >
                <div className="flex flex-col items-center gap-1">
                    <span className="font-bold">Easy</span>
                    <span className="text-xs text-muted-foreground hidden sm:inline">Key: 4</span>
                </div>
            </Button>
        </div>
    );
}
