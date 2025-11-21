"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

/**
 * Theme toggle button component.
 * Switches between light, dark, and system themes.
 */
export function ThemeToggle() {
    const [mounted, setMounted] = useState(false);
    const { theme, setTheme } = useTheme();

    // useEffect only runs on the client, so now we can safely show the UI
    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setMounted(true);
    }, []);

    // Avoid hydration mismatch by not rendering until mounted
    if (!mounted) {
        // Return a placeholder with the same dimensions to avoid layout shift
        return (
            <button
                className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                aria-label="Toggle theme"
                disabled
            >
                <div className="w-5 h-5" />
            </button>
        );
    }

    return (
        <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Toggle theme"
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
            {theme === "dark" ? (
                <Sun className="w-5 h-5 text-gray-700 dark:text-gray-300" />
            ) : (
                <Moon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
            )}
        </button>
    );
}

/**
 * Theme selector component with dropdown.
 * Allows selection between light, dark, and system themes.
 */
export function ThemeSelector() {
    const [mounted, setMounted] = useState(false);
    const { theme, setTheme } = useTheme();

    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setMounted(true);
    }, []);

    if (!mounted) {
        return null;
    }

    return (
        <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Theme
            </label>
            <div className="flex gap-2">
                <button
                    onClick={() => setTheme("light")}
                    className={`flex-1 px-4 py-2 rounded-md border transition-colors ${theme === "light"
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                        }`}
                >
                    <Sun className="w-4 h-4 mx-auto" />
                    <span className="text-xs mt-1 block">Light</span>
                </button>
                <button
                    onClick={() => setTheme("dark")}
                    className={`flex-1 px-4 py-2 rounded-md border transition-colors ${theme === "dark"
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                        }`}
                >
                    <Moon className="w-4 h-4 mx-auto" />
                    <span className="text-xs mt-1 block">Dark</span>
                </button>
                <button
                    onClick={() => setTheme("system")}
                    className={`flex-1 px-4 py-2 rounded-md border transition-colors ${theme === "system"
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                        }`}
                >
                    <div className="w-4 h-4 mx-auto flex">
                        <Sun className="w-3 h-3" />
                        <Moon className="w-3 h-3" />
                    </div>
                    <span className="text-xs mt-1 block">System</span>
                </button>
            </div>
        </div>
    );
}
