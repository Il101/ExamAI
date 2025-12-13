'use client';

import { Fragment, useState, useRef } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Bot } from 'lucide-react';
import { AiTutorChat } from './ai-tutor-chat';
import { cn } from '@/lib/utils';

interface MobileAiTutorProps {
    topicId: string;
}

export function MobileAiTutor({ topicId }: MobileAiTutorProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [touchStart, setTouchStart] = useState<number | null>(null);
    const [touchEnd, setTouchEnd] = useState<number | null>(null);
    const panelRef = useRef<HTMLDivElement>(null);

    // Minimum swipe distance (in px) to trigger close
    const minSwipeDistance = 50;

    const onTouchStart = (e: React.TouchEvent) => {
        setTouchEnd(null);
        setTouchStart(e.targetTouches[0].clientY);
    };

    const onTouchMove = (e: React.TouchEvent) => {
        setTouchEnd(e.targetTouches[0].clientY);
    };

    const onTouchEnd = (e: React.TouchEvent) => {
        if (!touchStart || !touchEnd) return;

        const distance = touchStart - touchEnd;
        const isDownSwipe = distance < -minSwipeDistance;

        // Only close on downward swipe
        if (isDownSwipe) {
            setIsOpen(false);
        }

        setTouchStart(null);
        setTouchEnd(null);
    };

    return (
        <>
            {/* Floating Capsule Button - only visible on mobile/tablet */}
            <button
                onClick={() => setIsOpen(true)}
                className={cn(
                    "xl:hidden fixed bottom-6 right-4 z-40",
                    "flex items-center gap-2 px-4 py-3 rounded-full",
                    "bg-card/70 backdrop-blur-xl border border-white/10",
                    "shadow-lg shadow-black/20",
                    "text-sm font-medium text-foreground",
                    "hover:bg-card/90 active:scale-95 transition-all duration-200"
                )}
            >
                <div className="relative">
                    <Bot className="h-5 w-5 text-primary" />
                    <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                </div>
                <span>AI Tutor</span>
            </button>

            {/* Bottom Sheet Dialog */}
            <Transition.Root show={isOpen} as={Fragment}>
                <Dialog as="div" className="relative z-50 xl:hidden" onClose={setIsOpen}>
                    {/* Backdrop - fully transparent, no blur */}
                    <Transition.Child
                        as={Fragment}
                        enter="ease-out duration-300"
                        enterFrom="opacity-0"
                        enterTo="opacity-100"
                        leave="ease-in duration-200"
                        leaveFrom="opacity-100"
                        leaveTo="opacity-0"
                    >
                        <div className="fixed inset-0 bg-transparent" />
                    </Transition.Child>

                    {/* Bottom Sheet Container */}
                    <div className="fixed inset-0 flex items-end justify-center pointer-events-none">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="translate-y-full opacity-0"
                            enterTo="translate-y-0 opacity-100"
                            leave="ease-in duration-200"
                            leaveFrom="translate-y-0 opacity-100"
                            leaveTo="translate-y-full opacity-0"
                        >
                            <Dialog.Panel
                                ref={panelRef}
                                className="relative w-full max-h-[85vh] flex flex-col rounded-t-3xl overflow-hidden bg-card/95 backdrop-blur-xl border-t border-x border-white/10 shadow-2xl pointer-events-auto"
                            >
                                {/* Swipeable Handle Bar Area - top third */}
                                <div
                                    className="flex justify-center pt-3 pb-2 cursor-grab active:cursor-grabbing"
                                    onTouchStart={onTouchStart}
                                    onTouchMove={onTouchMove}
                                    onTouchEnd={onTouchEnd}
                                >
                                    <div className="w-12 h-1.5 rounded-full bg-white/30" />
                                </div>

                                {/* Header - also swipeable */}
                                <div
                                    className="flex items-center justify-between px-4 pb-3 border-b border-white/10 cursor-grab active:cursor-grabbing"
                                    onTouchStart={onTouchStart}
                                    onTouchMove={onTouchMove}
                                    onTouchEnd={onTouchEnd}
                                >
                                    <div className="flex items-center gap-2">
                                        <div className="relative">
                                            <Bot className="h-5 w-5 text-primary" />
                                            <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                                        </div>
                                        <Dialog.Title className="font-semibold text-foreground">
                                            AI Tutor
                                        </Dialog.Title>
                                        <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-medium ml-1">
                                            Online
                                        </span>
                                    </div>
                                </div>

                                {/* Chat Content */}
                                <div className="flex-1 overflow-hidden min-h-[50vh]">
                                    <AiTutorChat topicId={topicId} className="h-full" />
                                </div>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </Dialog>
            </Transition.Root>
        </>
    );
}
