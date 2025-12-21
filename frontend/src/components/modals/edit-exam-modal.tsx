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
import { Settings, Loader2, Trash2 } from 'lucide-react';
import { Exam } from '@/lib/api/exams';

interface EditExamModalProps {
    isOpen: boolean;
    onClose: () => void;
    exam: Exam;
}

export function EditExamModal({ isOpen, onClose, exam }: EditExamModalProps) {
    const { updateExam, deleteExam, isUpdating, isDeleting } = useExams();
    const [formData, setFormData] = useState({
        title: exam.title,
        subject: exam.subject || '',
        exam_date: exam.exam_date ? exam.exam_date.split('T')[0] : '',
    });

    useEffect(() => {
        setFormData({
            title: exam.title,
            subject: exam.subject || '',
            exam_date: exam.exam_date ? exam.exam_date.split('T')[0] : '',
        });
    }, [exam]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.title) return;

        try {
            updateExam({
                examId: exam.id,
                data: {
                    ...formData,
                    exam_date: formData.exam_date || null,
                }
            });
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
                        Update exam details or delete it.
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
                            <Label htmlFor="subject" className="text-sm font-bold">
                                Subject
                            </Label>
                            <Input
                                id="subject"
                                value={formData.subject}
                                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
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
                    </div>

                    <div className="flex flex-col gap-3 pt-2">
                        <div className="flex gap-3">
                            <Button
                                type="button"
                                variant="outline"
                                className="flex-1 font-bold"
                                onClick={onClose}
                                disabled={isUpdating || isDeleting}
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                className="flex-1 font-bold"
                                disabled={isUpdating || isDeleting || !formData.title}
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
                            disabled={isUpdating || isDeleting}
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
