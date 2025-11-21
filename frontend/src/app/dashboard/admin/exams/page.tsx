'use client';

import { useEffect, useState } from 'react';
import { adminApi, AdminExam } from '@/lib/api/admin';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Loader2, Search } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

export default function AdminExamsPage() {
    const [exams, setExams] = useState<AdminExam[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        const fetchExams = async () => {
            try {
                const data = await adminApi.getExams(0, 100);
                setExams(data.exams);
                setTotal(data.total);
            } catch (err: unknown) {
                console.error('Failed to fetch exams:', err);
                const status = err instanceof Error && 'response' in err
                    ? (err as { response?: { status?: number } }).response?.status
                    : undefined;

                if (status === 403) {
                    toast.error('Admin access required');
                } else {
                    toast.error('Failed to load exams');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchExams();
    }, []);

    const filteredExams = exams.filter(
        (exam) =>
            exam.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            exam.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
            exam.user_email.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'ready':
                return 'bg-green-500';
            case 'processing':
                return 'bg-blue-500';
            case 'failed':
                return 'bg-red-500';
            default:
                return 'bg-gray-500';
        }
    };

    return (
        <div className="container max-w-7xl py-8 space-y-6">
            <div>
                <h1 className="text-3xl font-bold mb-2">Exam Management</h1>
                <p className="text-muted-foreground">View all exams across the system</p>
            </div>

            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>Exams ({total})</CardTitle>
                            <CardDescription>All exams created by users</CardDescription>
                        </div>
                        <div className="relative w-64">
                            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search exams..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-8"
                            />
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Title</TableHead>
                                <TableHead>Subject</TableHead>
                                <TableHead>User</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Topics</TableHead>
                                <TableHead>Created</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredExams.map((exam) => (
                                <TableRow key={exam.id}>
                                    <TableCell className="font-medium">{exam.title}</TableCell>
                                    <TableCell>{exam.subject}</TableCell>
                                    <TableCell>{exam.user_email}</TableCell>
                                    <TableCell>
                                        <Badge className={getStatusColor(exam.status)}>{exam.status}</Badge>
                                    </TableCell>
                                    <TableCell>{exam.topic_count}</TableCell>
                                    <TableCell>{format(new Date(exam.created_at), 'MMM d, yyyy')}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
