'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ReviewItem } from '@/lib/api/study';
import { cn } from '@/lib/utils';

interface FlashcardProps {
    item: ReviewItem;
    onResult: (quality: number) => void;
    className?: string;
}

export function Flashcard({ item, onResult, className }: FlashcardProps) {
    const [isFlipped, setIsFlipped] = useState(false);

    // Reset flip state when item changes
    useEffect(() => {
        setIsFlipped(false);
    }, [item.id]);

    const handleKeyDown = useCallback(
        (event: KeyboardEvent) => {
            // Tab to flip
            if (event.code === 'Tab') {
                event.preventDefault();
                setIsFlipped(prev => !prev);
                return;
            }

            if (!isFlipped) {
                if (event.code === 'Space' || event.code === 'Enter') {
                    event.preventDefault();
                    setIsFlipped(true);
                }
            } else {
                // Number keys for rating
                switch (event.key) {
                    case '1':
                        event.preventDefault();
                        onResult(1);
                        break;
                    case '2':
                        event.preventDefault();
                        onResult(2);
                        break;
                    case '3':
                        event.preventDefault();
                        onResult(3);
                        break;
                    case '4':
                        event.preventDefault();
                        onResult(4);
                        break;
                }
            }
        },
        [isFlipped, onResult]
    );

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [handleKeyDown]);

    // Clean and format text - handle structured answers from AI
    const formatText = (text: string) => {
        // Remove excessive newlines (more than 2 in a row)
        let cleaned = text.replace(/\n{3,}/g, '\n\n');

        // Convert bullet points to readable format
        cleaned = cleaned.replace(/\n•\s*/g, ', ');
        cleaned = cleaned.replace(/^•\s*/gm, '• ');

        // Clean up whitespace
        cleaned = cleaned.trim();

        return cleaned;
    };

    return (
        <div className={cn('w-full max-w-5xl mx-auto perspective-1000', className)}>
            <div
                className={cn(
                    'relative w-full transition-all duration-500 transform-style-3d cursor-pointer',
                    isFlipped && 'rotate-y-180'
                )}
                onClick={() => setIsFlipped(!isFlipped)}
            >
                {/* Front of card */}
                <Card className={cn(
                    "w-full h-full absolute inset-0 backface-hidden shadow-lg border-2 hover:shadow-xl transition-shadow"
                )}>
                    <div className="p-16 min-h-[500px] flex flex-col items-center justify-center">
                        <p className="text-sm text-muted-foreground uppercase tracking-wide mb-8">Question</p>
                        <h2 className="text-4xl font-normal text-center leading-relaxed mb-12 whitespace-pre-line">
                            {formatText(item.question)}
                        </h2>
                        <Button
                            size="lg"
                            onClick={(e) => {
                                e.stopPropagation();
                                setIsFlipped(true);
                            }}
                            className="px-8"
                        >
                            Show Answer <span className="ml-2 text-xs opacity-60">(Space/Tab)</span>
                        </Button>
                    </div>
                </Card>

                {/* Back of card */}
                <Card className={cn(
                    "w-full h-full absolute inset-0 backface-hidden rotate-y-180 shadow-lg border-2"
                )}>
                    <div className="p-16 min-h-[500px] flex flex-col items-center justify-between">
                        <div className="flex flex-col items-center flex-1 justify-center w-full">
                            <p className="text-sm text-muted-foreground uppercase tracking-wide mb-8">Answer</p>
                            <p className="text-3xl font-normal text-center leading-relaxed whitespace-pre-line">
                                {formatText(item.answer)}
                            </p>
                        </div>

                        <div className="w-full max-w-3xl">
                            <p className="text-center text-sm text-muted-foreground mb-4">How well did you know this?</p>
                            <div className="grid grid-cols-4 gap-3">
                                <Button
                                    size="lg"
                                    variant="outline"
                                    className="h-20 flex-col gap-1 border-2 hover:border-red-500 hover:bg-red-50 dark:hover:bg-red-950"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onResult(1);
                                    }}
                                >
                                    <span className="text-3xl">😞</span>
                                    <span className="font-semibold">Again</span>
                                    <span className="text-xs opacity-60">1 min (Press 1)</span>
                                </Button>
                                <Button
                                    size="lg"
                                    variant="outline"
                                    className="h-20 flex-col gap-1 border-2 hover:border-orange-500 hover:bg-orange-50 dark:hover:bg-orange-950"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onResult(2);
                                    }}
                                >
                                    <span className="text-3xl">😐</span>
                                    <span className="font-semibold">Hard</span>
                                    <span className="text-xs opacity-60">2 days (Press 2)</span>
                                </Button>
                                <Button
                                    size="lg"
                                    variant="outline"
                                    className="h-20 flex-col gap-1 border-2 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onResult(3);
                                    }}
                                >
                                    <span className="text-3xl">🙂</span>
                                    <span className="font-semibold">Good</span>
                                    <span className="text-xs opacity-60">4 days (Press 3)</span>
                                </Button>
                                <Button
                                    size="lg"
                                    variant="outline"
                                    className="h-20 flex-col gap-1 border-2 hover:border-green-500 hover:bg-green-50 dark:hover:bg-green-950"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onResult(4);
                                    }}
                                >
                                    <span className="text-3xl">😄</span>
                                    <span className="font-semibold">Easy</span>
                                    <span className="text-xs opacity-60">7 days (Press 4)</span>
                                </Button>
                            </div>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
    );
}
