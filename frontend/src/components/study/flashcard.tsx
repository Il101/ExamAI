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
            if (!isFlipped) {
                if (event.code === 'Space' || event.code === 'Enter') {
                    event.preventDefault();
                    setIsFlipped(true);
                }
            } else {
                switch (event.key) {
                    case '1':
                        onResult(1);
                        break;
                    case '2':
                        onResult(2);
                        break;
                    case '3':
                        onResult(3);
                        break;
                    case '4':
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

    // Clean text - remove excessive line breaks
    const cleanText = (text: string) => {
        return text.replace(/\n+/g, ' ').trim();
    };

    return (
        <div className={cn('w-full max-w-5xl mx-auto', className)}>
            {!isFlipped ? (
                // Front of card
                <Card className="shadow-lg border-2 hover:shadow-xl transition-shadow">
                    <div className="p-16 min-h-[500px] flex flex-col items-center justify-center">
                        <p className="text-sm text-muted-foreground uppercase tracking-wide mb-8">Question</p>
                        <h2 className="text-4xl font-normal text-center leading-relaxed mb-12">
                            {cleanText(item.question)}
                        </h2>
                        <Button
                            size="lg"
                            onClick={() => setIsFlipped(true)}
                            className="px-8"
                        >
                            Show Answer
                        </Button>
                    </div>
                </Card>
            ) : (
                // Back of card
                <Card className="shadow-lg border-2">
                    <div className="p-16 min-h-[500px] flex flex-col items-center justify-between">
                        <div className="flex flex-col items-center flex-1 justify-center w-full">
                            <p className="text-sm text-muted-foreground uppercase tracking-wide mb-8">Answer</p>
                            <p className="text-3xl font-normal text-center leading-relaxed">
                                {cleanText(item.answer)}
                            </p>
                        </div>

                        <div className="w-full max-w-3xl">
                            <p className="text-center text-sm text-muted-foreground mb-4">How well did you know this?</p>
                            <div className="grid grid-cols-4 gap-3">
                                <Button
                                    size="lg"
                                    variant="outline"
                                    className="h-20 flex-col gap-1 border-2 hover:border-red-500 hover:bg-red-50 dark:hover:bg-red-950"
                                    onClick={() => onResult(1)}
                                >
                                    <span className="text-3xl">😞</span>
                                    <span className="font-semibold">Again</span>
                                    <span className="text-xs opacity-60">1 min</span>
                                </Button>
                                <Button
                                    size="lg"
                                    variant="outline"
                                    className="h-20 flex-col gap-1 border-2 hover:border-orange-500 hover:bg-orange-50 dark:hover:bg-orange-950"
                                    onClick={() => onResult(2)}
                                >
                                    <span className="text-3xl">😐</span>
                                    <span className="font-semibold">Hard</span>
                                    <span className="text-xs opacity-60">2 days</span>
                                </Button>
                                <Button
                                    size="lg"
                                    variant="outline"
                                    className="h-20 flex-col gap-1 border-2 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950"
                                    onClick={() => onResult(3)}
                                >
                                    <span className="text-3xl">🙂</span>
                                    <span className="font-semibold">Good</span>
                                    <span className="text-xs opacity-60">4 days</span>
                                </Button>
                                <Button
                                    size="lg"
                                    variant="outline"
                                    className="h-20 flex-col gap-1 border-2 hover:border-green-500 hover:bg-green-50 dark:hover:bg-green-950"
                                    onClick={() => onResult(4)}
                                >
                                    <span className="text-3xl">😄</span>
                                    <span className="font-semibold">Easy</span>
                                    <span className="text-xs opacity-60">7 days</span>
                                </Button>
                            </div>
                        </div>
                    </div>
                </Card>
            )}
        </div>
    );
}
