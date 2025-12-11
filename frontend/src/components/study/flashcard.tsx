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
        [isFlipped, onResult]
    );

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [handleKeyDown]);

    return (
        <div className={cn('w-full max-w-3xl mx-auto perspective-1000', className)}>
            <div
                className={cn(
                    'relative w-full transition-all duration-500 transform-style-3d cursor-pointer',
                    isFlipped && 'rotate-y-180'
                )}
                onClick={() => setIsFlipped(!isFlipped)}
            >
                {/* Front of Card */}
                <Card className={cn(
                    "w-full h-full absolute inset-0 backface-hidden flex flex-col shadow-xl border-2 border-primary/5"
                )}>
                    <CardContent className="flex flex-col p-8 md:p-10">
                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-6 text-center">
                            Question
                        </span>
                        <div className="flex-1 flex items-center justify-center py-8 px-4">
                            <h3 className="text-2xl md:text-3xl font-semibold leading-relaxed text-center max-w-2xl whitespace-pre-wrap">
                                {item.question}
                            </h3>
                        </div>
                        <div className="w-full flex justify-center pt-6">
                            <Button
                                className="w-full max-w-xs group"
                                size="lg"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setIsFlipped(true);
                                }}
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

                {/* Back of Card */}
                <Card className={cn(
                    "w-full h-full absolute inset-0 backface-hidden rotate-y-180 flex flex-col shadow-xl border-2 border-primary/5"
                )}>
                    <CardContent className="flex flex-col p-8 md:p-10">
                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-6 text-center">
                            Answer
                        </span>
                        <div className="flex-1 flex items-center justify-center py-8 px-4">
                            <p className="text-xl md:text-2xl leading-relaxed text-center max-w-2xl whitespace-pre-wrap">{item.answer}</p>
                        </div>

                        <div className="w-full grid grid-cols-2 md:grid-cols-4 gap-3 pt-6">
                            <Button
                                variant="outline"
                                className="border-red-200 hover:bg-red-50 hover:text-red-600 dark:border-red-900/50 dark:hover:bg-red-900/20"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onResult(1);
                                }}
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
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onResult(2);
                                }}
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
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onResult(3);
                                }}
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
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onResult(4);
                                }}
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
            </div>
        </div>
    );
}
