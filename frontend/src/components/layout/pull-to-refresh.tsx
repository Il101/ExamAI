'use client';

import { useEffect, useState } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';
import { useRouter } from 'next/navigation';

export function PullToRefresh({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const [pullDistance, setPullDistance] = useState(0);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [touchStart, setTouchStart] = useState(0);
    const [isMobile, setIsMobile] = useState(false);

    // Spring for smooth animation
    const springConfig = { stiffness: 400, damping: 30 };
    const pullProgress = useSpring(0, springConfig);
    const spinnerOpacity = useTransform(pullProgress, [0, 1], [0, 1]);

    useEffect(() => {
        setIsMobile(/iPhone|iPad|iPod|Android/i.test(navigator.userAgent));
    }, []);

    useEffect(() => {
        if (!isMobile) return;

        const handleTouchStart = (e: TouchEvent) => {
            if (window.scrollY === 0 && !isRefreshing) {
                setTouchStart(e.touches[0].clientY);
            }
        };

        const handleTouchMove = (e: TouchEvent) => {
            if (touchStart === 0 || window.scrollY > 0 || isRefreshing) return;

            const touchY = e.touches[0].clientY;
            const distance = Math.max(0, touchY - touchStart);

            // Apply resistance for natural feel
            const resistedDistance = Math.min(distance * 0.4, 80);
            setPullDistance(resistedDistance);
            pullProgress.set(resistedDistance / 80);
        };

        const handleTouchEnd = () => {
            if (pullDistance > 50 && !isRefreshing) {
                setIsRefreshing(true);
                pullProgress.set(1);

                router.refresh();

                // Hide after refresh
                setTimeout(() => {
                    setIsRefreshing(false);
                    pullProgress.set(0);
                }, 2500);
            } else {
                pullProgress.set(0);
            }

            setPullDistance(0);
            setTouchStart(0);
        };

        document.addEventListener('touchstart', handleTouchStart, { passive: true });
        document.addEventListener('touchmove', handleTouchMove, { passive: true });
        document.addEventListener('touchend', handleTouchEnd);

        return () => {
            document.removeEventListener('touchstart', handleTouchStart);
            document.removeEventListener('touchmove', handleTouchMove);
            document.removeEventListener('touchend', handleTouchEnd);
        };
    }, [isMobile, touchStart, pullDistance, isRefreshing, pullProgress, router]);

    if (!isMobile) return <>{children}</>;

    return (
        <>
            {/* Spinner in header area - behind content */}
            <motion.div
                className="fixed top-0 left-0 right-0 h-16 z-40 flex items-center justify-center bg-background pointer-events-none"
                style={{ opacity: spinnerOpacity }}
            >
                <motion.div
                    animate={isRefreshing ? { rotate: 360 } : { rotate: pullDistance * 4 }}
                    transition={isRefreshing ? { duration: 1, repeat: Infinity, ease: "linear" } : { duration: 0 }}
                    className="text-2xl"
                >
                    🧠
                </motion.div>
            </motion.div>

            {/* Text hint */}
            {pullDistance > 30 && !isRefreshing && (
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.6 }}
                    className="fixed top-12 left-0 right-0 z-50 text-center text-xs font-medium text-foreground/50 pointer-events-none"
                >
                    {pullDistance > 50 ? 'Release to refresh' : 'Pull to refresh'}
                </motion.p>
            )}

            {children}
        </>
    );
}
