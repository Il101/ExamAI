'use client';

import { Bell, Menu } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuth } from '@/lib/hooks/use-auth';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ThemeToggle } from '@/components/theme-toggle';

interface HeaderProps {
    onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
    const { user, logout } = useAuth();
    // TODO: Replace with actual notification state from backend
    const hasNewNotifications = false;

    const getInitials = (name: string) => {
        return name
            .split(' ')
            .map((n) => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    };

    return (
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-white/10 bg-background/50 backdrop-blur-xl px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
            <Button
                variant="ghost"
                size="icon"
                className="lg:hidden"
                onClick={onMenuClick}
            >
                <Menu className="h-6 w-6" />
            </Button>

            <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
                <div className="flex flex-1" />

                <div className="flex items-center gap-x-4 lg:gap-x-6">
                    {/* Theme toggle */}
                    <ThemeToggle />

                    {/* Notifications */}
                    <Button
                        variant="ghost"
                        size="icon"
                        className="relative"
                        onClick={() => toast.info('No new notifications')}
                    >
                        <Bell className="h-5 w-5" />
                        {hasNewNotifications && (
                            <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-500" />
                        )}
                    </Button>

                    {/* User menu */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                                <Avatar>
                                    <AvatarFallback className="bg-blue-600 text-white">
                                        {user ? getInitials(user.full_name) : 'U'}
                                    </AvatarFallback>
                                </Avatar>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="w-56" align="end" forceMount>
                            <DropdownMenuLabel className="font-normal">
                                <div className="flex flex-col space-y-1">
                                    <p className="text-sm font-medium leading-none">
                                        {user?.full_name || 'User'}
                                    </p>
                                    <p className="text-xs leading-none text-muted-foreground">
                                        {user?.email || 'user@example.com'}
                                    </p>
                                </div>
                            </DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem asChild>
                                <a href="/dashboard/settings">Settings</a>
                            </DropdownMenuItem>
                            <DropdownMenuItem asChild>
                                <a href="/dashboard/pricing">Upgrade Plan</a>
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => logout()}>
                                Log out
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>
        </div>
    );
}
