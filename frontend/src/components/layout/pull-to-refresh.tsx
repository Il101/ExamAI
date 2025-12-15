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
    const MAX_PULL = 120; // Maximum pixels you can pull down visually
    const REFRESH_THRESHOLD = 70; // Pixel point where release triggers refresh

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
                contentControls.start({ y: REFRESH_THRESHOLD, transition: { type: "spring", stiffness: 300, damping: 30 } });

                // Perform Soft Refresh
                router.refresh();

                // Fake network delay for UX (so user sees the spinner) + actual wait
                setTimeout(() => {
                    setIsRefreshing(false);
                    setPullY(0);
                    contentControls.start({ y: 0 });
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

    // Use framer motion controls for programmatic animation (snap back),
    // but fall back to raw translation during gesture for zero-latency performance
    const yValue = isRefreshing ? REFRESH_THRESHOLD : pullY;

    if (!isMobile) return <>{children}</>;

    return (
        <div className="relative min-h-screen bg-black"> {/* Background color behind spinner */}

            {/* SPINNER LAYER (Z-0) - Fixed behind content */}
            <div className="absolute top-0 left-0 w-full h-[120px] flex items-center justify-center z-0 overflow-hidden">
                <motion.div
                    className="flex flex-col items-center justify-center pt-8"
                    style={{
                        opacity: Math.min(pullY / REFRESH_THRESHOLD, 1),
                        scale: Math.min(0.5 + (pullY / MAX_PULL) * 0.5, 1) // Subtle zoom in
                    }}
                >
                    <motion.div
                        className="text-3xl mb-2"
                        animate={isRefreshing ? { rotate: 360 } : { rotate: pullY * 2 }}
                        transition={isRefreshing ? { duration: 0.8, repeat: Infinity, ease: "linear" } : { duration: 0 }}
                    >
                        🧠
                    </motion.div>
                </motion.div>
            </div>

            {/* CONTENT LAYER (Z-10) - Slides over spinner */}
            <motion.div
                className="relative z-10 bg-background min-h-screen shadow-2xl" // shadow creates depth separation
                animate={contentControls}
                style={{ y: yValue }}
                transition={{ type: "spring", stiffness: 400, damping: 30 }} // Bounce effect
            >
                {children}
            </motion.div>
        </div>
    );
}
