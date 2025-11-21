'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { LayoutDashboard, Users, FileText } from 'lucide-react';

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();

    const isActive = (path: string) => pathname === path;

    return (
        <div className="flex gap-6">
            {/* Admin Sidebar */}
            <aside className="w-64 space-y-2">
                <Link href="/admin">
                    <Button
                        variant={isActive('/admin') ? 'default' : 'ghost'}
                        className="w-full justify-start"
                    >
                        <LayoutDashboard className="mr-2 h-4 w-4" />
                        Dashboard
                    </Button>
                </Link>
                <Link href="/admin/users">
                    <Button
                        variant={isActive('/admin/users') ? 'default' : 'ghost'}
                        className="w-full justify-start"
                    >
                        <Users className="mr-2 h-4 w-4" />
                        Users
                    </Button>
                </Link>
                <Link href="/admin/exams">
                    <Button
                        variant={isActive('/admin/exams') ? 'default' : 'ghost'}
                        className="w-full justify-start"
                    >
                        <FileText className="mr-2 h-4 w-4" />
                        Exams
                    </Button>
                </Link>
            </aside>

            {/* Main Content */}
            <main className="flex-1">{children}</main>
        </div>
    );
}
