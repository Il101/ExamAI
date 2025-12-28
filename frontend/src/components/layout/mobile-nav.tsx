'use client';

import { Fragment } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Dialog, Transition } from '@headlessui/react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
    Brain,
    BarChart3,
    Settings,
    CreditCard,
    Shield,
    Folder,
    CheckCircle2,
    Circle,
    BookOpen,
} from 'lucide-react';
import { useSidebar } from '@/lib/contexts/sidebar-context';
import { Progress } from '@/components/ui/progress';

const navigation = [
    { name: 'Courses', href: '/dashboard/courses', icon: Folder },
    { name: 'Flashcards', href: '/dashboard/flashcards', icon: Brain },
    { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
    { name: 'Settings', href: '/dashboard/settings', icon: Settings },
    { name: 'Pricing', href: '/dashboard/pricing', icon: CreditCard },
];

const adminNavigation = [
    { name: 'Admin Panel', href: '/dashboard/admin', icon: Shield },
];
interface MobileNavProps {
    open: boolean;
    onClose: () => void;
    isAdmin?: boolean;
}

export function MobileNav({ open, onClose, isAdmin = false }: MobileNavProps) {
    const pathname = usePathname();
    const { contextualNav } = useSidebar();
    const allNavigation = isAdmin
        ? [...navigation, ...adminNavigation]
        : navigation;

    return (
        <Transition.Root show={open} as={Fragment}>
            <Dialog as="div" className="relative z-50 lg:hidden" onClose={onClose}>
                <Transition.Child
                    as={Fragment}
                    enter="transition-opacity ease-linear duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="transition-opacity ease-linear duration-300"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-gray-900/80" />
                </Transition.Child>

                <div className="fixed inset-0 flex">
                    <Transition.Child
                        as={Fragment}
                        enter="transition ease-in-out duration-300 transform"
                        enterFrom="-translate-x-full"
                        enterTo="translate-x-0"
                        leave="transition ease-in-out duration-300 transform"
                        leaveFrom="translate-x-0"
                        leaveTo="-translate-x-full"
                    >
                        <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                            <Transition.Child
                                as={Fragment}
                                enter="ease-in-out duration-300"
                                enterFrom="opacity-0"
                                enterTo="opacity-100"
                                leave="ease-in-out duration-300"
                                leaveFrom="opacity-100"
                                leaveTo="opacity-0"
                            >
                                <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                                    <button type="button" className="-m-2.5 p-2.5" onClick={onClose}>
                                        <span className="sr-only">Close sidebar</span>
                                        <X className="h-6 w-6 text-white" aria-hidden="true" />
                                    </button>
                                </div>
                            </Transition.Child>

                            <div
                                className="flex grow flex-col gap-y-5 overflow-y-auto bg-background/95 backdrop-blur-xl px-6 pb-4 border-r border-white/10"
                                style={{ paddingTop: 'env(safe-area-inset-top)' }}
                            >
                                <div className="flex h-16 shrink-0 items-center">
                                    <Link href="/dashboard/courses" onClick={onClose}>
                                        <h1 className="text-2xl font-bold text-primary cursor-pointer hover:opacity-80 transition-opacity">
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
                                                                onClick={onClose}
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

                                        {contextualNav && (
                                            <li>
                                                <div className="flex items-center justify-between mb-4">
                                                    <div className="text-xs font-semibold leading-6 text-muted-foreground uppercase tracking-wider">
                                                        {contextualNav.title}
                                                    </div>
                                                    {contextualNav.progress !== undefined && (
                                                        <span className="text-[10px] font-mono text-primary bg-primary/10 px-1.5 py-0.5 rounded">
                                                            {Math.round(contextualNav.progress)}%
                                                        </span>
                                                    )}
                                                </div>
                                                {contextualNav.progress !== undefined && (
                                                    <Progress value={contextualNav.progress} className="h-1 mb-4 bg-white/5" />
                                                )}
                                                <ul role="list" className="-mx-2 space-y-1">
                                                    {contextualNav.items.map((item) => {
                                                        const isActive = pathname === item.href;

                                                        const getIcon = () => {
                                                            if (isActive) return <BookOpen className="h-4 w-4 text-primary animate-pulse" />;
                                                            if (item.status === 'ready') return <CheckCircle2 className="h-4 w-4 text-emerald-500/80" />;
                                                            return <Circle className="h-4 w-4 text-muted-foreground/30" />;
                                                        };

                                                        return (
                                                            <li key={item.id || item.name}>
                                                                <Link
                                                                    href={item.href}
                                                                    onClick={onClose}
                                                                    className={cn(
                                                                        isActive
                                                                            ? 'bg-primary/10 text-primary'
                                                                            : 'text-muted-foreground hover:text-primary hover:bg-white/5',
                                                                        'group flex items-center gap-x-3 rounded-md p-2 text-[13px] leading-6 font-medium transition-colors'
                                                                    )}
                                                                >
                                                                    <div className="flex-shrink-0">
                                                                        {getIcon()}
                                                                    </div>
                                                                    <span className="truncate">{item.name}</span>
                                                                </Link>
                                                            </li>
                                                        );
                                                    })}
                                                </ul>
                                            </li>
                                        )}
                                    </ul>
                                </nav>
                            </div>
                        </Dialog.Panel>
                    </Transition.Child>
                </div>
            </Dialog>
        </Transition.Root>
    );
}
