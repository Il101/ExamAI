'use client';

import { MessageSquare } from 'lucide-react';
import { useEffect } from 'react';
import formbricks from '@formbricks/js';
import { useAuthStore } from '@/lib/stores/auth-store';

export function FeedbackButton() {
    const { user } = useAuthStore();

    useEffect(() => {
        // Initialize Formbricks only if environment variables are set
        const environmentId = process.env.NEXT_PUBLIC_FORMBRICKS_ENVIRONMENT_ID;
        const appUrl = process.env.NEXT_PUBLIC_FORMBRICKS_APP_URL;

        if (typeof window !== 'undefined' && environmentId && appUrl) {
            formbricks.setup({
                environmentId,
                appUrl,
            });

            // Set user information if logged in
            if (user) {
                formbricks.setUserId(user.id);
                if (user.email) {
                    formbricks.setAttribute('email', user.email);
                }
                if (user.full_name) {
                    formbricks.setAttribute('name', user.full_name);
                }
            }
        }
    }, [user]);

    const handleClick = () => {
        // Trigger Formbricks survey
        const environmentId = process.env.NEXT_PUBLIC_FORMBRICKS_ENVIRONMENT_ID;

        if (environmentId) {
            // This will show the configured survey in Formbricks dashboard
            formbricks.track('feedback_button_clicked');
        } else {
            console.warn('Formbricks not configured. Please set environment variables.');
        }
    };

    // Don't render if Formbricks is not configured
    if (!process.env.NEXT_PUBLIC_FORMBRICKS_ENVIRONMENT_ID) {
        return null;
    }

    return (
        <button
            onClick={handleClick}
            className="fixed bottom-6 right-6 z-50 group"
            aria-label="Send feedback"
        >
            {/* Frosted glass capsule button */}
            <div className="flex items-center gap-2 px-4 py-3 rounded-full bg-white/10 dark:bg-black/20 backdrop-blur-xl border border-white/20 dark:border-white/10 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                {/* Icon with gradient background */}
                <div className="relative">
                    <div className="absolute inset-0 bg-gradient-to-tr from-primary/40 to-violet-500/40 rounded-full blur-md" />
                    <MessageSquare className="w-5 h-5 text-primary relative z-10" />
                </div>

                {/* Text label */}
                <span className="text-sm font-medium text-foreground/90 whitespace-nowrap">
                    Beta Feedback
                </span>
            </div>
        </button>
    );
}
