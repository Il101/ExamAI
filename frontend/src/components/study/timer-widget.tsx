import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Square, Coffee, Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { studyApi } from '@/lib/api/study';

interface TimerWidgetProps {
    sessionId: string | null;
    onCompletePomodoro?: () => void;
    className?: string;
}

type TimerState = 'work' | 'shortBreak' | 'longBreak';

const POMODORO_TIME = 25 * 60;
const SHORT_BREAK_TIME = 5 * 60;
const LONG_BREAK_TIME = 15 * 60;

export function TimerWidget({ sessionId, onCompletePomodoro, className }: TimerWidgetProps) {
    const [timeLeft, setTimeLeft] = useState(POMODORO_TIME);
    const [isActive, setIsActive] = useState(false);
    const [timerState, setTimerState] = useState<TimerState>('work');
    const [isExpanded, setIsExpanded] = useState(false);
    const [pomodorosCompleted, setPomodorosCompleted] = useState(0);
    const [isShake, setIsShake] = useState(false);

    // Audio ref for notification sound (optional)
    // const audioRef = useRef<HTMLAudioElement | null>(null);

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
        setIsShake(true);
        setIsExpanded(true); // Auto expand on complete

        if (timerState === 'work') {
            if (sessionId) {
                try {
                    await studyApi.completePomodoro(sessionId);
                    if (onCompletePomodoro) onCompletePomodoro();
                } catch (error) {
                    console.error('Failed to complete pomodoro:', error);
                }
            }
            setPomodorosCompleted((prev) => prev + 1);
        }
    };

    const toggleTimer = () => {
        setIsActive(!isActive);
        setIsShake(false); // Stop shaking if started
    };

    const resetTimer = () => {
        setIsActive(false);
        setIsShake(false);
        if (timerState === 'work') setTimeLeft(POMODORO_TIME);
        else if (timerState === 'shortBreak') setTimeLeft(SHORT_BREAK_TIME);
        else setTimeLeft(LONG_BREAK_TIME);
    };

    const switchState = (newState: TimerState) => {
        setTimerState(newState);
        setIsActive(false);
        setIsShake(false);
        if (newState === 'work') setTimeLeft(POMODORO_TIME);
        else if (newState === 'shortBreak') setTimeLeft(SHORT_BREAK_TIME);
        else setTimeLeft(LONG_BREAK_TIME);
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const getProgressColor = () => {
        if (timerState === 'work') return 'text-red-500';
        return 'text-green-500';
    };

    if (!sessionId) return null;

    return (
        <div
            className={cn(
                "fixed right-0 top-24 z-50 transition-all duration-300 ease-in-out",
                isExpanded ? "translate-x-0" : "translate-x-[calc(100%-60px)] hover:translate-x-0",
                className
            )}
            onMouseEnter={() => setIsExpanded(true)}
            onMouseLeave={() => !isActive && timeLeft > 0 && setIsExpanded(false)} // Keep expanded if timer finished
        >
            <Card className="flex overflow-hidden shadow-lg border-l-4 border-l-blue-500 rounded-l-xl bg-white dark:bg-gray-900 w-[300px]">
                {/* Collapsed View (Visible Tab) */}
                <div className="flex flex-col items-center justify-center w-[60px] bg-gray-100 dark:bg-gray-800 p-2 cursor-pointer h-[120px]">
                    {timerState === 'work' ? (
                        <Brain className={cn("h-6 w-6 mb-2", isActive ? "animate-pulse text-red-500" : "text-gray-500")} />
                    ) : (
                        <Coffee className="h-6 w-6 mb-2 text-green-500" />
                    )}
                    <span className="text-xs font-mono font-bold rotate-90 whitespace-nowrap">
                        {formatTime(timeLeft)}
                    </span>
                </div>

                {/* Expanded View */}
                <div className="flex-1 p-4 flex flex-col items-center justify-between">
                    <div className="flex items-center justify-between w-full mb-2">
                        <span className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                            {timerState === 'work' ? 'Focus' : 'Break'}
                        </span>
                        <div className="flex gap-1">
                            {[...Array(4)].map((_, i) => (
                                <div
                                    key={i}
                                    className={cn(
                                        "w-2 h-2 rounded-full",
                                        i < pomodorosCompleted % 4 ? "bg-red-500" : "bg-gray-200"
                                    )}
                                />
                            ))}
                        </div>
                    </div>

                    <div className="relative mb-4">
                        {/* Tomato Image Placeholder or Icon */}
                        <div className={cn("relative flex items-center justify-center w-20 h-20 rounded-full bg-red-100 dark:bg-red-900/20", isShake && "animate-shake")}>
                            {timerState === 'work' ? (
                                <span className="text-4xl">🍅</span>
                            ) : (
                                <span className="text-4xl">☕</span>
                            )}
                        </div>
                        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                            {/* Optional overlay */}
                        </div>
                    </div>

                    <div className="text-3xl font-mono font-bold mb-4">
                        {formatTime(timeLeft)}
                    </div>

                    <div className="flex gap-2 w-full">
                        {timeLeft === 0 ? (
                            // Timer Finished Controls
                            timerState === 'work' ? (
                                <>
                                    <Button size="sm" className="flex-1 bg-green-600 hover:bg-green-700" onClick={() => switchState('shortBreak')}>
                                        Short Break
                                    </Button>
                                    <Button size="sm" variant="outline" className="flex-1" onClick={() => switchState('longBreak')}>
                                        Long Break
                                    </Button>
                                </>
                            ) : (
                                <Button size="sm" className="w-full" onClick={() => switchState('work')}>
                                    Start Focus
                                </Button>
                            )
                        ) : (
                            // Running/Paused Controls
                            <>
                                <Button
                                    size="sm"
                                    variant={isActive ? "secondary" : "default"}
                                    className="flex-1"
                                    onClick={toggleTimer}
                                >
                                    {isActive ? <Pause className="h-4 w-4 mr-1" /> : <Play className="h-4 w-4 mr-1" />}
                                    {isActive ? "Pause" : "Start"}
                                </Button>
                                <Button size="sm" variant="ghost" onClick={resetTimer}>
                                    <Square className="h-4 w-4" />
                                </Button>
                            </>
                        )}
                    </div>
                </div>
            </Card>
        </div>
    );
}
