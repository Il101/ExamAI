'use client';

import { useTheme } from 'next-themes';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Moon, Sun, Laptop } from 'lucide-react';
import { cn } from '@/lib/utils';

export function AppearanceForm() {
    const { theme, setTheme } = useTheme();

    return (
        <Card>
            <CardHeader>
                <CardTitle>Appearance</CardTitle>
                <CardDescription>Customize the look and feel of the application.</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                        <Button
                            variant="outline"
                            className={cn(
                                "h-24 flex flex-col gap-2",
                                theme === 'light' && "border-primary ring-1 ring-primary"
                            )}
                            onClick={() => setTheme('light')}
                        >
                            <Sun className="h-6 w-6" />
                            <span>Light</span>
                        </Button>
                        <Button
                            variant="outline"
                            className={cn(
                                "h-24 flex flex-col gap-2",
                                theme === 'dark' && "border-primary ring-1 ring-primary"
                            )}
                            onClick={() => setTheme('dark')}
                        >
                            <Moon className="h-6 w-6" />
                            <span>Dark</span>
                        </Button>
                        <Button
                            variant="outline"
                            className={cn(
                                "h-24 flex flex-col gap-2",
                                theme === 'system' && "border-primary ring-1 ring-primary"
                            )}
                            onClick={() => setTheme('system')}
                        >
                            <Laptop className="h-6 w-6" />
                            <span>System</span>
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
