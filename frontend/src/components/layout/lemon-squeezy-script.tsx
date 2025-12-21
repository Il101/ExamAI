"use client";

import Script from "next/script";

export function LemonSqueezyScript() {
    return (
        <Script
            src="https://assets.lemonsqueezy.com/lemon.js"
            strategy="afterInteractive"
            onLoad={() => {
                console.log("Lemon Squeezy script loaded");
                // @ts-ignore
                if (window.createLemonSqueezy) {
                    // @ts-ignore
                    window.createLemonSqueezy();
                }
            }}
        />
    );
}
