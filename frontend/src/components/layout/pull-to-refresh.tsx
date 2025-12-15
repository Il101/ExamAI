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
    const contentOffset = useSpring(0, springConfig);
    const spinnerOpacity = useTransform(contentOffset, [0, 60], [0, 1]);

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
            const resistedDistance = Math.min(distance * 0.5, 100);
            setPullDistance(resistedDistance);
            contentOffset.set(resistedDistance);
        };

        const handleTouchEnd = () => {
            if (pullDistance > 60 && !isRefreshing) {
                setIsRefreshing(true);
                contentOffset.set(60); // Keep spinner visible

                router.refresh();

                // Hide after refresh
                setTimeout(() => {
                    setIsRefreshing(false);
                    contentOffset.set(0);
                }, 2500);
            } else {
                contentOffset.set(0);
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
    }, [isMobile, touchStart, pullDistance, isRefreshing, contentOffset, router]);

    if (!isMobile) return <>{children}</>;

    return (
        <div className="relative min-h-screen overflow-hidden">
            {/* Spinner - fixed at top, visible when pulling */}
            <motion.div
                className="fixed top-16 left-0 right-0 z-50 flex items-center justify-center pointer-events-none"
                style={{ opacity: spinnerOpacity }}
            >
                <motion.div
                    animate={isRefreshing ? { rotate: 360 } : { rotate: pullDistance * 3 }}
                    transition={isRefreshing ? { duration: 1, repeat: Infinity, ease: "linear" } : { duration: 0 }}
                    className="text-3xl"
                >
                    🧠
                </motion.div>
            </motion.div>

            {/* Text indicator */}
            {pullDistance > 40 && !isRefreshing && (
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="fixed top-28 left-0 right-0 z-50 text-center text-xs font-medium text-foreground/60"
                >
                    {pullDistance > 60 ? 'Release to refresh' : 'Pull to refresh'}
                </motion.p>
            )}

            {/* Content that shifts down */}
            <motion.div
                style={{ y: contentOffset }}
            >
                {children}
            </motion.div>
        </div>
    );
}
