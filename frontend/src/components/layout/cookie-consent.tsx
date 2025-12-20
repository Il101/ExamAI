"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export function CookieConsent() {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        // Check if user has already made a choice
        const consent = localStorage.getItem("cookie-consent");
        if (!consent) {
            // Delay showing the banner for a better UX
            const timer = setTimeout(() => {
                setIsVisible(true);
            }, 1500);
            return () => clearTimeout(timer);
        }
    }, []);

    const handleAccept = () => {
        localStorage.setItem("cookie-consent", "accepted");
        setIsVisible(false);
    };

    const handleReject = () => {
        localStorage.setItem("cookie-consent", "rejected");
        setIsVisible(false);
    };

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ opacity: 0, y: 50, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 20, scale: 0.95 }}
                    className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] w-[calc(100%-2rem)] max-w-2xl"
                >
                    <div className="glass-card p-5 md:p-6 rounded-2xl flex flex-col md:flex-row items-center gap-5 md:gap-8 shadow-glow border-primary/20 relative overflow-hidden">
                        {/* Subtle background glow */}
                        <div className="absolute -top-24 -left-24 w-48 h-48 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
                        <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-secondary/10 rounded-full blur-3xl pointer-events-none" />

                        <div className="flex-shrink-0 p-3 rounded-2xl bg-primary/10 text-primary floating relative z-10">
                            <ShieldCheck className="w-8 h-8 md:w-10 md:h-10" />
                        </div>

                        <div className="flex-1 text-center md:text-left relative z-10">
                            <h3 className="text-lg font-bold text-foreground mb-1">Privacy is our priority</h3>
                            <p className="text-sm text-muted-foreground leading-relaxed">
                                ExamAI Pro uses cookies to remember your progress and provide a smoother experience. We also use <span className="text-foreground font-semibold">self-hosted analytics</span> to improve the app without sharing your data with third parties. Is that okay with you?
                            </p>
                        </div>

                        <div className="flex flex-col sm:flex-row items-center gap-2 w-full md:w-auto relative z-10">
                            <Button
                                variant="outline"
                                onClick={handleReject}
                                className="w-full sm:w-auto text-xs border-muted-foreground/20 hover:bg-destructive/5 hover:text-destructive transition-colors"
                            >
                                Reject
                            </Button>
                            <Button
                                onClick={handleAccept}
                                className="w-full sm:w-auto bg-gradient-brand hover:opacity-90 shadow-glow font-bold text-white border-0"
                            >
                                Accept
                            </Button>
                        </div>

                        <div className="absolute bottom-2 left-6 text-[10px] text-muted-foreground/30 hidden md:block">
                            <Link href="/privacy" className="hover:underline">Privacy Policy</Link>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
