'use client';

import { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ReviewItem, studyApi, IntervalsPreview } from '@/lib/api/study';
import { cn } from '@/lib/utils';

interface FlashcardProps {
    item: ReviewItem;
    onResult: (quality: number) => void;
    className?: string;
}

export function Flashcard({ item, onResult, className }: FlashcardProps) {
    const [isFlipped, setIsFlipped] = useState(false);
    const [intervals, setIntervals] = useState<IntervalsPreview | null>(null);
    const [loadingIntervals, setLoadingIntervals] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Reset flip state when item changes
    useEffect(() => {
        setIsFlipped(false);
        setIsSubmitting(false);

        // Fetch intervals when card is loaded
        const fetchIntervals = async () => {
            setLoadingIntervals(true);
            try {
                const preview = await studyApi.getIntervalsPreview(item.id);
                setIntervals(preview);
            } catch (error) {
                console.error('Failed to fetch intervals:', error);
                // Fallback to defaults if fetch fails
                setIntervals({ again: 1, hard: 2, good: 4, easy: 7 });
            } finally {
                setLoadingIntervals(false);
            }
        };

        fetchIntervals();
    }, [item.id]);

    const handleResult = useCallback((quality: number) => {
        if (isSubmitting) return;
        setIsSubmitting(true);
        onResult(quality);
    }, [onResult, isSubmitting]);

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
                        handleResult(1);
                        break;
                    case '2':
                        event.preventDefault();
                        handleResult(2);
                        break;
                    case '3':
                        event.preventDefault();
                        handleResult(3);
                        break;
                    case '4':
                        event.preventDefault();
                        handleResult(4);
                        break;
                }
            }
        },
        [isFlipped, handleResult]
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
                    'relative w-full transition-all duration-500 transform-style-3d cursor-pointer grid grid-cols-1',
                    isFlipped && 'rotate-y-180'
                )}
                onClick={() => setIsFlipped(!isFlipped)}
            >
                {/* Front of card */}
                <div
                    className="col-start-1 row-start-1 backface-hidden"
                    // Prevent interactions with front when flipped (though backface-visibility usually handles visual)
                    aria-hidden={isFlipped}
                    style={{ backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden' }}
                >
                    <Card className="h-full shadow-lg border-2 hover:shadow-xl transition-shadow bg-card" style={{ backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden' }}>
                        <div className="p-6 sm:p-10 md:p-16 min-h-[350px] sm:min-h-[400px] md:min-h-[500px] flex flex-col items-center justify-center">
                            <p className="text-xs sm:text-sm text-muted-foreground uppercase tracking-wide mb-4 sm:mb-8">Question</p>
                            <h2 className="text-xl sm:text-2xl md:text-4xl font-normal text-center leading-relaxed mb-6 sm:mb-12 break-words hyphens-auto" style={{ wordBreak: 'normal', overflowWrap: 'break-word' }}>
                                {item.question}
                            </h2>
                            <Button
                                size="lg"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setIsFlipped(true);
                                }}
                                className="px-6 sm:px-8"
                            >
                                Show Answer <span className="ml-2 text-xs opacity-60 hidden sm:inline">(Space/Tab)</span>
                            </Button>
                        </div>
                    </Card>
                </div>

                {/* Back of card */}
                <div
                    className="col-start-1 row-start-1 backface-hidden rotate-y-180"
                    aria-hidden={!isFlipped}
                    style={{ backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden' }}
                >
                    <Card className="h-full shadow-lg border-2 bg-card" style={{ backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden' }}>
                        <div className="p-6 sm:p-10 md:p-16 min-h-[350px] sm:min-h-[400px] md:min-h-[500px] flex flex-col items-center justify-between h-full">
                            <div className="flex flex-col items-center flex-1 justify-center w-full">
                                <p className="text-xs sm:text-sm text-muted-foreground uppercase tracking-wide mb-4 sm:mb-8">Answer</p>
                                <div className="prose prose-sm sm:prose-lg dark:prose-invert max-w-none text-center w-full" style={{ wordBreak: 'normal', overflowWrap: 'break-word' }}>
                                    <ReactMarkdown
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                            p: ({ node, ...props }) => <p className="text-base sm:text-xl md:text-2xl leading-relaxed mb-4" style={{ wordBreak: 'normal', overflowWrap: 'break-word' }} {...props} />,
                                            strong: ({ node, ...props }) => <strong className="font-semibold text-primary" {...props} />,
                                            em: ({ node, ...props }) => <em className="text-muted-foreground" {...props} />,
                                            ul: ({ node, ...props }) => <ul className="text-sm sm:text-lg md:text-xl text-left list-disc list-inside space-y-2 my-4" {...props} />,
                                            li: ({ node, ...props }) => <li className="leading-relaxed" style={{ wordBreak: 'normal', overflowWrap: 'break-word' }} {...props} />,
                                            code: ({ node, ...props }) => <code className="px-1.5 py-0.5 rounded bg-muted text-primary font-mono text-sm sm:text-base md:text-lg break-words whitespace-pre-wrap" {...props} />,
                                        }}
                                    >
                                        {item.answer}
                                    </ReactMarkdown>
                                </div>
                            </div>

                            <div className="w-full mt-6 sm:mt-8" onClick={(e) => e.stopPropagation()}>
                                <p className="text-center text-xs sm:text-sm text-muted-foreground mb-3 sm:mb-4">How well did you know this?</p>
                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
                                    <Button
                                        size="lg"
                                        variant="outline"
                                        disabled={isSubmitting}
                                        className="h-16 sm:h-20 flex-col gap-0.5 sm:gap-1 border-2 hover:border-red-500 hover:bg-red-50 dark:hover:bg-red-950 disabled:opacity-50"
                                        onClick={() => handleResult(1)}
                                    >
                                        <span className="text-2xl sm:text-3xl">😞</span>
                                        <span className="text-xs sm:text-sm font-semibold">Again</span>
                                        <span className="text-[10px] sm:text-xs opacity-60">
                                            {loadingIntervals ? '...' : `${intervals?.again || 1}m`}
                                        </span>
                                    </Button>
                                    <Button
                                        size="lg"
                                        variant="outline"
                                        disabled={isSubmitting}
                                        className="h-16 sm:h-20 flex-col gap-0.5 sm:gap-1 border-2 hover:border-orange-500 hover:bg-orange-50 dark:hover:bg-orange-950 disabled:opacity-50"
                                        onClick={() => handleResult(2)}
                                    >
                                        <span className="text-2xl sm:text-3xl">😐</span>
                                        <span className="text-xs sm:text-sm font-semibold">Hard</span>
                                        <span className="text-[10px] sm:text-xs opacity-60">
                                            {loadingIntervals ? '...' : `${intervals?.hard || 2}d`}
                                        </span>
                                    </Button>
                                    <Button
                                        size="lg"
                                        variant="outline"
                                        disabled={isSubmitting}
                                        className="h-16 sm:h-20 flex-col gap-0.5 sm:gap-1 border-2 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950 disabled:opacity-50"
                                        onClick={() => handleResult(3)}
                                    >
                                        <span className="text-2xl sm:text-3xl">🙂</span>
                                        <span className="text-xs sm:text-sm font-semibold">Good</span>
                                        <span className="text-[10px] sm:text-xs opacity-60">
                                            {loadingIntervals ? '...' : `${intervals?.good || 4}d`}
                                        </span>
                                    </Button>
                                    <Button
                                        size="lg"
                                        variant="outline"
                                        disabled={isSubmitting}
                                        className="h-16 sm:h-20 flex-col gap-0.5 sm:gap-1 border-2 hover:border-green-500 hover:bg-green-50 dark:hover:bg-green-950 disabled:opacity-50"
                                        onClick={() => handleResult(4)}
                                    >
                                        <span className="text-2xl sm:text-3xl">😄</span>
                                        <span className="text-xs sm:text-sm font-semibold">Easy</span>
                                        <span className="text-[10px] sm:text-xs opacity-60">
                                            {loadingIntervals ? '...' : `${intervals?.easy || 7}d`}
                                        </span>
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
}
