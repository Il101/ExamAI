import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Square, Coffee, Brain, Timer as TimerIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { studyApi, StudySession } from '@/lib/api/study';
import { ExamSelectModal } from '@/components/modals/exam-select-modal';
Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';
import { toast } from 'sonner';

type TimerState = 'work' | 'shortBreak' | 'longBreak';

const POMODORO_TIME = 25 * 60;
const SHORT_BREAK_TIME = 5 * 60;
const LONG_BREAK_TIME = 15 * 60;

export function HeaderTimer() {
    const [timeLeft, setTimeLeft] = useState(POMODORO_TIME);
    const [isActive, setIsActive] = useState(false);
    const [timerState, setTimerState] = useState<TimerState>('work');
    const [isOpen, setIsOpen] = useState(false);
    const [showExamSelect, setShowExamSelect] = useState(false);

    // Session tracking
    const [activeSession, setActiveSession] = useState<StudySession | null>(null);

    useEffect(() => {
        let interval: NodeJS.Timeout;

        if (isActive && timeLeft > 0) {
            interval = setInterval(() => {
                setTimeLeft((prev) => prev - 1);
            }, 1000);
        } else if (timeLeft === 0) {
            handleTimerComplete();
        }

        return () => clearInterval(interval);
    }, [isActive, timeLeft]);

    const handleTimerComplete = async () => {
        setIsActive(false);
        setIsOpen(true); // Auto open popover on complete

        if (timerState === 'work' && activeSession) {
            // Record completed pomodoro to backend
            try {
                const updated = await studyApi.completePomodoro(activeSession.id);
                setActiveSession(updated);
                toast.success('Pomodoro completed! 🍅');
            } catch (error) {
                console.error('Failed to record pomodoro:', error);
                toast.error('Failed to save progress');
            }
        }
    };

    const handleStartTimer = () => {
        if (timerState === 'work' && !activeSession) {
            // Need to select exam first
            setShowExamSelect(true);
        } else {
            setIsActive(true);
        }
    };

    const handleExamSelected = async (examId: string) => {
        try {
            const session = await studyApi.startSession(examId, POMODORO_TIME / 60);
            setActiveSession(session);
            setIsActive(true);
            toast.success('Study session started!');
        } catch (error) {
            console.error('Failed to start session:', error);
            toast.error('Failed to start session');
        }
    };

    const toggleTimer = () => {
        if (!isActive) {
            handleStartTimer();
        } else {
            setIsActive(false);
        }
    };

    const resetTimer = async () => {
        setIsActive(false);
        if (timerState === 'work') setTimeLeft(POMODORO_TIME);
        else if (timerState === 'shortBreak') setTimeLeft(SHORT_BREAK_TIME);
        else setTimeLeft(LONG_BREAK_TIME);

        // End session if active
        if (activeSession && timerState === 'work') {
            try {
                await studyApi.endSession(activeSession.id);
                setActiveSession(null);
            } catch (error) {
                console.error('Failed to end session:', error);
            }
        }
    };

    const switchState = async (newState: TimerState) => {
        setTimerState(newState);
        setIsActive(false);
        if (newState === 'work') {
            setTimeLeft(POMODORO_TIME);
            // Clear session when switching to work
            if (activeSession) {
                try {
                    await studyApi.endSession(activeSession.id);
                    setActiveSession(null);
                } catch (error) {
                    console.error('Failed to end session:', error);
                }
            }
        } else if (newState === 'shortBreak') {
            setTimeLeft(SHORT_BREAK_TIME);
        } else {
            setTimeLeft(LONG_BREAK_TIME);
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const pomodorosCompleted = activeSession?.pomodoros_completed || 0;

    return (
        <>
            <ExamSelectModal
                open={showExamSelect}
                onClose={() => setShowExamSelect(false)}
                onSelect={handleExamSelected}
            />

            <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm" className={cn("h-9 gap-2 font-mono", isActive && "text-blue-500 bg-blue-500/10")}>
                                    {timerState === 'work' ? (
                                        <Brain className="h-4 w-4" />
                                    ) : (
                                        <Coffee className="h-4 w-4" />
                                    )}
                                    <span>{formatTime(timeLeft)}</span>
                                </Button>
                            </DropdownMenuTrigger>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>Pomodoro Timer: Track your focus time</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
                <DropdownMenuContent className="w-80 p-4" align="end">
                    <div className="flex flex-col space-y-4">
                        <div className="flex items-center justify-between">
                            <h4 className="font-medium leading-none">
                                {timerState === 'work' ? 'Focus Timer' : 'Break Timer'}
                            </h4>
                            <div className="flex gap-1">
                                {[...Array(4)].map((_, i) => (
                                    <div
                                        key={i}
                                        className={cn(
                                            "w-1.5 h-1.5 rounded-full",
                                            i < pomodorosCompleted % 4 ? "bg-red-500" : "bg-gray-200 dark:bg-gray-700"
                                        )}
                                    />
                                ))}
                            </div>
                        </div>

                        <div className="flex justify-center py-4">
                            <div className="text-4xl font-mono font-bold tracking-wider">
                                {formatTime(timeLeft)}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                            {timeLeft === 0 ? (
                                timerState === 'work' ? (
                                    <>
                                        <Button onClick={() => switchState('shortBreak')} className="bg-green-600 hover:bg-green-700">Short Break</Button>
                                        <Button onClick={() => switchState('longBreak')} variant="outline">Long Break</Button>
                                    </>
                                ) : (
                                    <Button onClick={() => switchState('work')} className="col-span-2">Start Focus</Button>
                                )
                            ) : (
                                <>
                                    <Button
                                        variant={isActive ? "secondary" : "default"}
                                        onClick={toggleTimer}
                                    >
                                        {isActive ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                                        {isActive ? "Pause" : "Start"}
                                    </Button>
                                    <Button variant="outline" onClick={resetTimer}>
                                        <Square className="h-4 w-4 mr-2" />
                                        Reset
                                    </Button>
                                </>
                            )}
                        </div>

                        <div className="flex justify-center gap-2 pt-2 border-t text-muted-foreground">
                            <Button variant="ghost" size="sm" onClick={() => switchState('work')} className={cn("text-xs h-7", timerState === 'work' && "bg-accent text-accent-foreground")}>Work</Button>
                            <Button variant="ghost" size="sm" onClick={() => switchState('shortBreak')} className={cn("text-xs h-7", timerState === 'shortBreak' && "bg-accent text-accent-foreground")}>Short</Button>
                            <Button variant="ghost" size="sm" onClick={() => switchState('longBreak')} className={cn("text-xs h-7", timerState === 'longBreak' && "bg-accent text-accent-foreground")}>Long</Button>
                        </div>
                    </div>
                </DropdownMenuContent>
            </DropdownMenu>
        </>
    );
}
