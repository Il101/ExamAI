"use client";

import { useEffect, useState } from "react";
import { useScrollAnimation } from "@/lib/hooks/useScrollAnimation";

interface AnimatedCounterProps {
    end: number;
    duration?: number;
    suffix?: string;
    prefix?: string;
}

const AnimatedCounter = ({ end, duration = 2000, suffix = "", prefix = "" }: AnimatedCounterProps) => {
    const [count, setCount] = useState(0);
    const { ref, isVisible } = useScrollAnimation();

    useEffect(() => {
        if (!isVisible) return;

        let startTime: number | null = null;
        const animate = (currentTime: number) => {
            if (!startTime) startTime = currentTime;
            const progress = Math.min((currentTime - startTime) / duration, 1);

            setCount(Math.floor(progress * end));

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }, [isVisible, end, duration]);

    return (
        <div ref={ref} className="scroll-reveal">
            <span className="text-5xl md:text-6xl font-bold bg-gradient-brand bg-clip-text text-transparent">
                {prefix}{count}{suffix}
            </span>
        </div>
    );
};

export default AnimatedCounter;
