'use client';

import { useEffect, useState, useRef } from 'react';
import { motion, useSpring, useTransform, useAnimation } from 'framer-motion';
import { useRouter } from 'next/navigation';

export function PullToRefresh({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const [isRefreshing, setIsRefreshing] = useState(false);
    const contentControls = useAnimation();

    // Internal state for gesture tracking
    const touchStart = useRef(0);
    const [pullY, setPullY] = useState(0);
    const [isMobile, setIsMobile] = useState(false);

    // Instagram-like resistance configuration
    const MAX_PULL = 150; // Increased max pull for better feel
    const REFRESH_THRESHOLD = 80; // Allow more space for status bar

    useEffect(() => {
        setIsMobile(/iPhone|iPad|iPod|Android/i.test(navigator.userAgent));
    }, []);

    useEffect(() => {
        if (!isMobile) return;

        const handleTouchStart = (e: TouchEvent) => {
            if (window.scrollY <= 1 && !isRefreshing) {
                touchStart.current = e.touches[0].clientY;
            } else {
                touchStart.current = 0;
            }
        };

        const handleTouchMove = (e: TouchEvent) => {
            if (!touchStart.current || window.scrollY > 1 || isRefreshing) return;

            const currentY = e.touches[0].clientY;
            const diff = currentY - touchStart.current;

            if (diff > 0) {
                // Logarithmic resistance formula for "native" feel
                // As you pull further, it gets harder
                const resistY = Math.min(diff * 0.45, MAX_PULL);

                // Prevent default pull-to-refresh from browser if we are handling it
                if (resistY > 5 && e.cancelable) {
                    e.preventDefault();
                }

                setPullY(resistY);
            }
        };

        const handleTouchEnd = async () => {
            if (!touchStart.current || isRefreshing) return;

            if (pullY > REFRESH_THRESHOLD) {
                // Trigger Refresh
                setIsRefreshing(true);
                // Snap content to threshold position while loading
                contentControls.start({ paddingTop: REFRESH_THRESHOLD, transition: { type: "spring", stiffness: 300, damping: 30 } });

                // Perform Soft Refresh
                router.refresh();

                // Fake network delay for UX (so user sees the spinner) + actual wait
                setTimeout(() => {
                    setIsRefreshing(false);
                    setPullY(0);
                    contentControls.start({ paddingTop: 0 });
                }, 2000);
            } else {
                // Snap back if not pulled enough
                setPullY(0);
            }
            touchStart.current = 0;
        };

        document.addEventListener('touchstart', handleTouchStart, { passive: true });
        document.addEventListener('touchmove', handleTouchMove, { passive: false }); // non-passive to allow preventDefault
        document.addEventListener('touchend', handleTouchEnd);

        return () => {
            document.removeEventListener('touchstart', handleTouchStart);
            document.removeEventListener('touchmove', handleTouchMove);
            document.removeEventListener('touchend', handleTouchEnd);
        };
    }, [isMobile, isRefreshing, pullY, contentControls, router]);

    // Use padding value for refreshing state, raw pull for gesture
    const paddingValue = isRefreshing ? REFRESH_THRESHOLD : pullY;

    if (!isMobile) return <>{children}</>;

    return (
        <motion.div
            className="relative min-h-screen bg-background"
            animate={contentControls}
            style={{ paddingTop: paddingValue }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
        >
            {/* SPINNER - Moves with padding */}
            <motion.div
                className="absolute left-0 right-0 flex justify-center"
                style={{
                    top: `calc(${Math.max(pullY - 60, -60)}px + env(safe-area-inset-top))`,
                    opacity: Math.min(pullY / (REFRESH_THRESHOLD - 20), 1),
                }}
            >
                <motion.div
                    className="text-3xl"
                    animate={isRefreshing ? { rotate: 360 } : { rotate: pullY * 2 }}
                    transition={isRefreshing ? { duration: 0.8, repeat: Infinity, ease: "linear" } : { duration: 0 }}
                >
                    🧠
                </motion.div>
            </motion.div>

            {/* CONTENT */}
            {children}
        </motion.div>
    );
}
