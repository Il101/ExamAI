'use client';

import { Fragment, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Bot, X, ChevronDown } from 'lucide-react';
import { AiTutorChat } from './ai-tutor-chat';
import { cn } from '@/lib/utils';

interface MobileAiTutorProps {
    topicId: string;
}

export function MobileAiTutor({ topicId }: MobileAiTutorProps) {
    const [isOpen, setIsOpen] = useState(false);

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
                    {/* Backdrop */}
                    <Transition.Child
                        as={Fragment}
                        enter="ease-out duration-300"
                        enterFrom="opacity-0"
                        enterTo="opacity-100"
                        leave="ease-in duration-200"
                        leaveFrom="opacity-100"
                        leaveTo="opacity-0"
                    >
                        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
                    </Transition.Child>

                    {/* Bottom Sheet Container */}
                    <div className="fixed inset-0 flex items-end justify-center">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="translate-y-full opacity-0"
                            enterTo="translate-y-0 opacity-100"
                            leave="ease-in duration-200"
                            leaveFrom="translate-y-0 opacity-100"
                            leaveTo="translate-y-full opacity-0"
                        >
                            <Dialog.Panel className="relative w-full max-h-[85vh] flex flex-col rounded-t-3xl overflow-hidden bg-card/80 backdrop-blur-xl border-t border-x border-white/10 shadow-2xl">
                                {/* Handle Bar */}
                                <div className="flex justify-center pt-3 pb-2">
                                    <div className="w-12 h-1.5 rounded-full bg-white/20" />
                                </div>

                                {/* Header */}
                                <div className="flex items-center justify-between px-4 pb-3 border-b border-white/10">
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
                                    <button
                                        onClick={() => setIsOpen(false)}
                                        className="p-2 rounded-full hover:bg-white/10 transition-colors"
                                    >
                                        <ChevronDown className="h-5 w-5 text-muted-foreground" />
                                    </button>
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
