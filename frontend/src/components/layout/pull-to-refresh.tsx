'use client';

import { useEffect, useState } from 'react';
import { motion, useSpring, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';

export function PullToRefresh({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const [pullDistance, setPullDistance] = useState(0);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [touchStart, setTouchStart] = useState(0);
    const [isMobile, setIsMobile] = useState(false);

    const pullProgress = useSpring(0, { stiffness: 300, damping: 30 });

    useEffect(() => {
        // Detect mobile device
        setIsMobile(/iPhone|iPad|iPod|Android/i.test(navigator.userAgent));
    }, []);

    useEffect(() => {
        if (!isMobile) return;

        const handleTouchStart = (e: TouchEvent) => {
            // Only trigger if at top of page
            if (window.scrollY === 0) {
                setTouchStart(e.touches[0].clientY);
            }
        };

        const handleTouchMove = (e: TouchEvent) => {
            if (touchStart === 0 || window.scrollY > 0) return;

            const touchY = e.touches[0].clientY;
            const distance = touchY - touchStart;

            if (distance > 0 && distance < 150) {
                setPullDistance(distance);
                pullProgress.set(distance / 150);
            }
        };

        const handleTouchEnd = async () => {
            if (pullDistance > 80 && !isRefreshing) {
                setIsRefreshing(true);

                // Soft refresh - reload data without full page reload
                router.refresh();

                // Hide loading indicator after animation
                setTimeout(() => {
                    setIsRefreshing(false);
                    setPullDistance(0);
                    setTouchStart(0);
                    pullProgress.set(0);
                }, 1500);
            } else {
                setPullDistance(0);
                setTouchStart(0);
                pullProgress.set(0);
            }
        };

        document.addEventListener('touchstart', handleTouchStart, { passive: true });
        document.addEventListener('touchmove', handleTouchMove, { passive: true });
        document.addEventListener('touchend', handleTouchEnd);

        return () => {
            document.removeEventListener('touchstart', handleTouchStart);
            document.removeEventListener('touchmove', handleTouchMove);
            document.removeEventListener('touchend', handleTouchEnd);
        };
    }, [isMobile, touchStart, pullDistance, isRefreshing, pullProgress]);

    if (!isMobile) return <>{children}</>;

    return (
        <>
            {/* Loading overlay during refresh */}
            <AnimatePresence>
                {isRefreshing && (
                    <motion.div
                        initial={{ y: -100, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: -100, opacity: 0 }}
                        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                        className="fixed top-0 left-0 right-0 z-[100] flex items-center justify-center py-8 bg-background/80 backdrop-blur-xl border-b border-border"
                    >
                        <div className="flex items-center gap-3">
                            {/* Animated brain */}
                            <motion.div
                                animate={{
                                    rotate: [0, 360],
                                }}
                                transition={{
                                    duration: 2,
                                    repeat: Infinity,
                                    ease: "linear"
                                }}
                                className="text-3xl"
                            >
                                🧠
                            </motion.div>

                            {/* Loading text */}
                            <motion.p
                                animate={{ opacity: [0.5, 1, 0.5] }}
                                transition={{ duration: 1.5, repeat: Infinity }}
                                className="text-sm font-medium text-foreground"
                            >
                                Refreshing...
                            </motion.p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Pull indicator */}
            <motion.div
                className="fixed top-0 left-0 right-0 z-50 flex items-center justify-center pointer-events-none"
                style={{
                    height: pullDistance,
                    opacity: pullDistance / 100,
                }}
            >
                <motion.div
                    className="relative"
                    animate={{
                        rotate: pullProgress.get() * 360,
                        scale: 0.5 + pullProgress.get() * 0.5,
                    }}
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                >
                    {/* Brain emoji as loading icon */}
                    <div className="text-4xl">🧠</div>

                    {/* Sparkle effect */}
                    {pullDistance > 60 && (
                        <motion.div
                            className="absolute -top-2 -right-2 text-2xl"
                            animate={{ scale: [1, 1.2, 1], rotate: [0, 180, 360] }}
                            transition={{ duration: 1, repeat: Infinity }}
                        >
                            ✨
                        </motion.div>
                    )}
                </motion.div>

                {/* Progress text */}
                {pullDistance > 40 && (
                    <motion.p
                        className="absolute bottom-4 text-sm font-medium text-foreground/70"
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        {pullDistance > 80 ? 'Release to refresh' : 'Pull to refresh'}
                    </motion.p>
                )}
            </motion.div>

            {children}
        </>
    );
}
