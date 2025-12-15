import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { FeedbackButton } from "@/components/feedback/feedback-button";
// TEMPORARILY DISABLED - Need to test on all pages before re-enabling
// import { PullToRefresh } from "@/components/layout/pull-to-refresh";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover", // This enables using the notch area
  themeColor: "#000000",
};

export const metadata: Metadata = {
  title: "ExamAI Pro",
  description: "AI-powered exam preparation platform",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent", // Allows content to go under status bar
    title: "ExamAI Pro",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Providers>
          {/* TEMPORARILY DISABLED - Need to test on all pages before re-enabling */}
          {/* <PullToRefresh> */}
          {children}
          {/* </PullToRefresh> */}
          <FeedbackButton />
        </Providers>
      </body>
    </html>
  );
}
