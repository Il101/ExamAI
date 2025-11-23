'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ReviewItem } from '@/lib/api/study';
import { cn } from '@/lib/utils';
import { Eye, RotateCcw, ThumbsUp, Trophy, AlertCircle } from 'lucide-react';

interface FlashcardProps {
    item: ReviewItem;
    onResult: (quality: number) => void;
    className?: string;
    disabled?: boolean;
}

export function Flashcard({ item, onResult, className, disabled = false }: FlashcardProps) {
    const [isFlipped, setIsFlipped] = useState(false);


    const handleKeyDown = useCallback(
        (event: KeyboardEvent) => {
            if (disabled) return;

            if (!isFlipped) {
                if (event.code === 'Space' || event.code === 'Enter') {
                    event.preventDefault();
                    setIsFlipped(true);
                }
            } else {
                switch (event.key) {
                    case '1':
                        onResult(1); // Again
                        break;
                    case '2':
                        onResult(2); // Hard
                        break;
                    case '3':
                        onResult(3); // Good
                        break;
                    case '4':
                        onResult(4); // Easy
                        break;
                }
            }
        },
        [isFlipped, onResult, disabled]
    );

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [handleKeyDown]);

    return (
        <div className={cn('w-full max-w-2xl mx-auto perspective-1000', className)}>
            <div
                className={cn(
                    'relative w-full transition-all duration-500 transform-style-3d min-h-[400px]',
                    isFlipped ? 'rotate-y-180' : ''
                )}
            >
                {/* Front of Card */}
                {!isFlipped && (
                    <Card className="w-full h-full absolute backface-hidden flex flex-col shadow-xl border-2 border-primary/5">
                        <CardContent className="flex-1 flex flex-col items-center justify-center p-8 md:p-12 text-center">
                            <span className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-6">
                                Question
                            </span>
                            <h3 className="text-2xl md:text-3xl font-semibold leading-relaxed">
                                {item.question}
                            </h3>
                            <div className="mt-auto pt-12 w-full">
                                <Button
                                    className="w-full max-w-xs mx-auto group"
                                    size="lg"
                                    onClick={() => setIsFlipped(true)}
                                    disabled={disabled}
                                >
                                    <Eye className="mr-2 h-4 w-4 group-hover:scale-110 transition-transform" />
                                    Show Answer
                                    <span className="ml-2 text-xs opacity-50 font-normal hidden md:inline">
                                        (Space)
                                    </span>
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Back of Card */}
                {isFlipped && (
                    <Card className="w-full h-full absolute backface-hidden rotate-y-180 flex flex-col shadow-xl border-2 border-primary/5">
                        <CardContent className="flex-1 flex flex-col items-center justify-center p-8 md:p-12 text-center">
                            <span className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-6">
                                Answer
                            </span>
                            <div className="prose prose-lg dark:prose-invert mb-8">
                                <p className="text-xl md:text-2xl leading-relaxed">{item.answer}</p>
                            </div>

                            <div className="mt-auto w-full grid grid-cols-2 md:grid-cols-4 gap-3">
                                <Button
                                    variant="outline"
                                    className="border-red-200 hover:bg-red-50 hover:text-red-600 dark:border-red-900/50 dark:hover:bg-red-900/20"
                                    onClick={() => onResult(1)}
                                    disabled={disabled}
                                >
                                    <div className="flex flex-col items-center py-1">
                                        <RotateCcw className="h-4 w-4 mb-1" />
                                        <span>Again</span>
                                        <span className="text-[10px] opacity-50 font-normal">1 min</span>
                                    </div>
                                </Button>
                                <Button
                                    variant="outline"
                                    className="border-orange-200 hover:bg-orange-50 hover:text-orange-600 dark:border-orange-900/50 dark:hover:bg-orange-900/20"
                                    onClick={() => onResult(2)}
                                    disabled={disabled}
                                >
                                    <div className="flex flex-col items-center py-1">
                                        <AlertCircle className="h-4 w-4 mb-1" />
                                        <span>Hard</span>
                                        <span className="text-[10px] opacity-50 font-normal">2 days</span>
                                    </div>
                                </Button>
                                <Button
                                    variant="outline"
                                    className="border-blue-200 hover:bg-blue-50 hover:text-blue-600 dark:border-blue-900/50 dark:hover:bg-blue-900/20"
                                    onClick={() => onResult(3)}
                                    disabled={disabled}
                                >
                                    <div className="flex flex-col items-center py-1">
                                        <ThumbsUp className="h-4 w-4 mb-1" />
                                        <span>Good</span>
                                        <span className="text-[10px] opacity-50 font-normal">4 days</span>
                                    </div>
                                </Button>
                                <Button
                                    variant="outline"
                                    className="border-green-200 hover:bg-green-50 hover:text-green-600 dark:border-green-900/50 dark:hover:bg-green-900/20"
                                    onClick={() => onResult(4)}
                                    disabled={disabled}
                                >
                                    <div className="flex flex-col items-center py-1">
                                        <Trophy className="h-4 w-4 mb-1" />
                                        <span>Easy</span>
                                        <span className="text-[10px] opacity-50 font-normal">7 days</span>
                                    </div>
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
}
