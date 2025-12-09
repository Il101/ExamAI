'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
    LayoutDashboard,
    BookOpen,
    Brain,
    BarChart3,
    Settings,
    CreditCard,
    Shield,
} from 'lucide-react';

const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Exams', href: '/dashboard/exams', icon: BookOpen },
    { name: 'Flashcards', href: '/dashboard/flashcards', icon: Brain },
    { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
    { name: 'Settings', href: '/dashboard/settings', icon: Settings },
    { name: 'Pricing', href: '/dashboard/pricing', icon: CreditCard },
];

const adminNavigation = [
    { name: 'Admin Panel', href: '/dashboard/admin', icon: Shield },
];

interface SidebarProps {
    isAdmin?: boolean;
}

export function Sidebar({ isAdmin = false }: SidebarProps) {
    const pathname = usePathname();

    const allNavigation = isAdmin
        ? [...navigation, ...adminNavigation]
        : navigation;

    return (
        <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
            <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-white/10 bg-card/30 backdrop-blur-xl px-6 pb-4">
                <div className="flex h-16 shrink-0 items-center">
                    <Link href="/dashboard">
                        <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent cursor-pointer hover:opacity-80 transition-opacity">
                            ExamAI Pro
                        </h1>
                    </Link>
                </div>
                <nav className="flex flex-1 flex-col">
                    <ul role="list" className="flex flex-1 flex-col gap-y-7">
                        <li>
                            <ul role="list" className="-mx-2 space-y-1">
                                {allNavigation.map((item) => {
                                    const isActive = pathname === item.href ||
                                        (item.href !== '/dashboard' && pathname.startsWith(item.href));

                                    return (
                                        <li key={item.name}>
                                            <Link
                                                href={item.href}
                                                className={cn(
                                                    isActive
                                                        ? 'bg-white/10 text-primary'
                                                        : 'text-muted-foreground hover:text-primary hover:bg-white/5',
                                                    'group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold transition-colors'
                                                )}
                                            >
                                                <item.icon
                                                    className={cn(
                                                        isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-primary',
                                                        'h-6 w-6 shrink-0 border-0 outline-none [&>*]:border-0 [&>*]:outline-none [&_rect]:border-0 [&_rect]:outline-none'
                                                    )}
                                                    style={{ border: 'none', outline: 'none' }}
                                                    aria-hidden="true"
                                                />
                                                {item.name}
                                            </Link>
                                        </li>
                                    );
                                })}
                            </ul>
                        </li>
                    </ul>
                </nav>
            </div>
        </div>
    );
}
