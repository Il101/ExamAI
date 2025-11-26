'use client';

import Link from 'next/link';
import { ChevronRight, Home, BookOpen, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface BreadcrumbItem {
    label: string;
    href?: string;
    icon?: 'home' | 'exam' | 'topic';
}

interface BreadcrumbsProps {
    items: BreadcrumbItem[];
    className?: string;
}

const iconMap = {
    home: Home,
    exam: BookOpen,
    topic: FileText,
};

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
    return (
        <nav
            aria-label="Breadcrumb"
            className={cn('flex items-center space-x-1 text-sm text-muted-foreground', className)}
        >
            {items.map((item, index) => {
                const Icon = item.icon ? iconMap[item.icon] : null;
                const isLast = index === items.length - 1;

                return (
                    <div key={index} className="flex items-center space-x-1">
                        {index > 0 && (
                            <ChevronRight className="h-4 w-4 flex-shrink-0" />
                        )}
                        {item.href && !isLast ? (
                            <Link
                                href={item.href}
                                className="flex items-center space-x-1 hover:text-foreground transition-colors"
                            >
                                {Icon && <Icon className="h-4 w-4" />}
                                <span>{item.label}</span>
                            </Link>
                        ) : (
                            <span
                                className={cn(
                                    'flex items-center space-x-1',
                                    isLast && 'font-medium text-foreground'
                                )}
                            >
                                {Icon && <Icon className="h-4 w-4" />}
                                <span>{item.label}</span>
                            </span>
                        )}
                    </div>
                );
            })}
        </nav>
    );
}
