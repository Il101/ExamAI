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
        }
    }, []);

    const handleClick = () => {
        // Set user attributes before triggering survey
        if (user) {
            console.log('Setting Formbricks attributes:', {
                userid: user.id,
                useremail: user.email,
                username: user.full_name
            });

            // Set attributes (these persist across surveys)
            formbricks.setAttribute('userid', user.id);
            if (user.email) formbricks.setAttribute('useremail', user.email);
            if (user.full_name) formbricks.setAttribute('username', user.full_name);
        }

        // Trigger survey
        console.log('Triggering Formbricks survey');
        formbricks.track('feedback_button_clicked');
    };

    // Don't render if Formbricks is not configured
    if (!process.env.NEXT_PUBLIC_FORMBRICKS_ENVIRONMENT_ID) {
        return null;
    }

    return (
        <button
            onClick={handleClick}
            className="fixed bottom-6 left-6 z-50 group"
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
