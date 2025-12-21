'use client';

import { useState, useEffect } from 'react';
import { useExams } from '@/lib/hooks/use-exams';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Settings, Loader2, Trash2, Calendar, RefreshCw } from 'lucide-react';
import { Exam, examsApi } from '@/lib/api/exams';
import { useAuth } from '@/lib/hooks/use-auth';
import { usersApi } from '@/lib/api/users';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';

interface EditExamModalProps {
    isOpen: boolean;
    onClose: () => void;
    exam: Exam;
}

const DAYS = [
    { label: 'M', value: 0 },
    { label: 'T', value: 1 },
    { label: 'W', value: 2 },
    { label: 'T', value: 3 },
    { label: 'F', value: 4 },
    { label: 'S', value: 5 },
    { label: 'S', value: 6 },
];

export function EditExamModal({ isOpen, onClose, exam }: EditExamModalProps) {
    const router = useRouter();
    const { user } = useAuth();
    const { updateExam, deleteExam, isUpdating, isDeleting } = useExams();
    const [isRescheduling, setIsRescheduling] = useState(false);

    const [formData, setFormData] = useState({
        title: exam.title,
        subject: exam.subject || '',
        exam_date: exam.exam_date ? exam.exam_date.split('T')[0] : '',
    });

    const [studyDays, setStudyDays] = useState<number[]>([]);

    useEffect(() => {
        setFormData({
            title: exam.title,
            subject: exam.subject || '',
            exam_date: exam.exam_date ? exam.exam_date.split('T')[0] : '',
        });

        if (user?.study_days) {
            setStudyDays(user.study_days);
        } else {
            setStudyDays([0, 1, 2, 3, 4, 5, 6]);
        }
    }, [exam, user]);

    const toggleDay = (day: number) => {
        setStudyDays(prev =>
            prev.includes(day)
                ? prev.filter(d => d !== day)
                : [...prev, day].sort()
        );
    };

    const handleReschedule = async () => {
        try {
            setIsRescheduling(true);
            // Save study days first to ensure the planner uses latest prefs
            await usersApi.updateProfile({ study_days: studyDays });
            await examsApi.reschedule(exam.id);
            toast.success('Study plan updated based on your availability!');
            router.refresh();
        } catch (error) {
            console.error('Failed to reschedule:', error);
            toast.error('Failed to refresh schedule. Please try again.');
        } finally {
            setIsRescheduling(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.title) return;

        try {
            // Update exam
            updateExam({
                examId: exam.id,
                data: {
                    ...formData,
                    exam_date: formData.exam_date || null,
                }
            });

            // Update user study days
            await usersApi.updateProfile({ study_days: studyDays });

            onClose();
        } catch (error) {
            // Error handled by hook
        }
    };

    const handleDelete = async () => {
        if (!confirm('Are you sure you want to delete this exam? This action cannot be undone.')) return;

        try {
            await deleteExam(exam.id);
            onClose();
            window.location.href = '/dashboard/exams';
        } catch (error) {
            // Error handled by hook
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[425px] bg-card/95 backdrop-blur-xl border-border/40">
                <DialogHeader>
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                        <Settings className="h-6 w-6 text-primary" />
                    </div>
                    <DialogTitle className="text-2xl font-bold">Exam Settings</DialogTitle>
                    <DialogDescription className="text-muted-foreground">
                        Configure your study schedule and exam details.
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-6 mt-4">
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="title" className="text-sm font-bold">
                                Exam Title
                            </Label>
                            <Input
                                id="title"
                                value={formData.title}
                                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                required
                                className="bg-muted/30 border-border/40"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="exam_date" className="text-sm font-bold">
                                Exam Date
                            </Label>
                            <Input
                                id="exam_date"
                                type="date"
                                value={formData.exam_date}
                                onChange={(e) => setFormData({ ...formData, exam_date: e.target.value })}
                                className="bg-muted/30 border-border/40 [color-scheme:dark]"
                            />
                        </div>

                        <div className="space-y-3 pt-2">
                            <Label className="text-sm font-bold flex items-center gap-2">
                                <Calendar className="h-4 w-4" />
                                Study Days
                            </Label>
                            <div className="flex justify-between gap-1">
                                {DAYS.map((day) => (
                                    <button
                                        key={day.value}
                                        type="button"
                                        onClick={() => toggleDay(day.value)}
                                        className={`h-9 w-9 rounded-full text-xs font-bold transition-all border ${studyDays.includes(day.value)
                                                ? 'bg-primary text-primary-foreground border-primary shadow-lg shadow-primary/20'
                                                : 'bg-muted/30 text-muted-foreground border-border/40 hover:bg-muted/50'
                                            }`}
                                    >
                                        {day.label}
                                    </button>
                                ))}
                            </div>
                            <p className="text-[10px] text-muted-foreground italic">
                                Topics will only be scheduled for these days.
                            </p>
                        </div>

                        {exam.exam_date && (
                            <div className="pt-2">
                                <Button
                                    type="button"
                                    variant="secondary"
                                    className="w-full bg-primary/10 hover:bg-primary/20 text-primary border-primary/20 h-10 font-bold"
                                    onClick={handleReschedule}
                                    disabled={isRescheduling}
                                >
                                    {isRescheduling ? (
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    ) : (
                                        <RefreshCw className="mr-2 h-4 w-4" />
                                    )}
                                    Refresh Study Schedule
                                </Button>
                            </div>
                        )}
                    </div>

                    <div className="flex flex-col gap-3 pt-4 border-t border-border/40">
                        <div className="flex gap-3">
                            <Button
                                type="button"
                                variant="outline"
                                className="flex-1 font-bold"
                                onClick={onClose}
                                disabled={isUpdating || isDeleting || isRescheduling}
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                className="flex-1 font-bold"
                                disabled={isUpdating || isDeleting || isRescheduling || !formData.title}
                            >
                                {isUpdating ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Saving...
                                    </>
                                ) : (
                                    'Save Changes'
                                )}
                            </Button>
                        </div>

                        <Button
                            type="button"
                            variant="ghost"
                            className="w-full text-destructive hover:text-destructive hover:bg-destructive/10 font-bold"
                            onClick={handleDelete}
                            disabled={isUpdating || isDeleting || isRescheduling}
                        >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete Exam
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
