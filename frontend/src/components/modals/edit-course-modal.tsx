'use client';

import { useState, useEffect } from 'react';
import { useCourses } from '@/lib/hooks/use-courses';
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
import { Textarea } from '@/components/ui/textarea';
import { Settings, Loader2, Trash2 } from 'lucide-react';
import { Course } from '@/lib/api/courses';

interface EditCourseModalProps {
    isOpen: boolean;
    onClose: () => void;
    course: Course;
}

export function EditCourseModal({ isOpen, onClose, course }: EditCourseModalProps) {
    const { updateCourse, deleteCourse, isUpdating, isDeleting } = useCourses();
    const [formData, setFormData] = useState({
        title: course.title,
        subject: course.subject,
        description: course.description || '',
    });

    useEffect(() => {
        setFormData({
            title: course.title,
            subject: course.subject,
            description: course.description || '',
        });
    }, [course]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.title || !formData.subject) return;

        try {
            await updateCourse({ id: course.id, data: formData });
            onClose();
        } catch (error) {
            // Error handled by hook
        }
    };

    const handleDelete = async () => {
        if (!confirm('Are you sure you want to delete this folder? Exams will not be deleted.')) return;

        try {
            await deleteCourse(course.id);
            onClose();
            window.location.href = '/dashboard/courses';
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
                    <DialogTitle className="text-2xl font-bold">Folder Settings</DialogTitle>
                    <DialogDescription className="text-muted-foreground">
                        Update your course folder details or delete the folder.
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-6 mt-4">
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="title" className="text-sm font-bold">
                                Course Title
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
                                required
                                className="bg-muted/30 border-border/40"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="description" className="text-sm font-bold">
                                Description
                            </Label>
                            <Textarea
                                id="description"
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                className="bg-muted/30 border-border/40 min-h-[100px] resize-none"
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
                                disabled={isUpdating || isDeleting || !formData.title || !formData.subject}
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
                            Delete Folder
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
