"use client";

import Script from "next/script";
import { useEffect } from "react";

export function LemonSqueezyScript() {
    useEffect(() => {
        // If navigating back to the page and script is already there
        // @ts-ignore
        if (window.LemonSqueezy) {
            // @ts-ignore
            window.LemonSqueezy.Setup();
        }
    }, []);

    return (
        <Script
            src="https://app.lemonsqueezy.com/js/lemon.js"
            strategy="afterInteractive"
            onLoad={() => {
                console.log("Lemon Squeezy script loaded (v4)");
                // @ts-ignore
                if (window.createLemonSqueezy) {
                    // @ts-ignore
                    window.createLemonSqueezy();
                }

                // @ts-ignore
                if (window.LemonSqueezy) {
                    // @ts-ignore
                    window.LemonSqueezy.Setup({
                        eventHandler: (event: any) => {
                            console.log('Lemon Squeezy Event:', event);
                        }
                    });
                }
            }}
        />
    );
}
