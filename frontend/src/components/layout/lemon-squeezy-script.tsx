"use client";

import Script from "next/script";

export function LemonSqueezyScript() {
    return (
        <Script
            src="https://app.lemonsqueezy.com/js/lemon.js"
            strategy="afterInteractive"
            onLoad={() => {
                // @ts-ignore
                if (window.createLemonSqueezy) {
                    // @ts-ignore
                    window.createLemonSqueezy();
                }
            }}
        />
    );
}
