'use client';

import { useState } from 'react';
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
import { FolderPlus, Loader2 } from 'lucide-react';

interface CreateCourseModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function CreateCourseModal({ isOpen, onClose }: CreateCourseModalProps) {
    const { createCourse, isCreating } = useCourses();
    const [formData, setFormData] = useState({
        title: '',
        subject: '',
        description: '',
        semester_start: '',
        semester_end: '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.title || !formData.subject) return;

        try {
            await createCourse({
                ...formData,
                semester_start: formData.semester_start || undefined,
                semester_end: formData.semester_end || undefined,
            });
            setFormData({ title: '', subject: '', description: '', semester_start: '', semester_end: '' });
            onClose();
        } catch (error) {
            // Error handled by hook
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[425px] bg-card/95 backdrop-blur-xl border-border/40">
                <DialogHeader>
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                        <FolderPlus className="h-6 w-6 text-primary" />
                    </div>
                    <DialogTitle className="text-2xl font-bold">Create Course Folder</DialogTitle>
                    <DialogDescription className="text-muted-foreground">
                        Organize your exams into a semester-long course folder.
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
                                placeholder="e.g. Physics 101, Fall 2024"
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
                                placeholder="e.g. Physics"
                                value={formData.subject}
                                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                                required
                                className="bg-muted/30 border-border/40"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="description" className="text-sm font-bold">
                                Description (Optional)
                            </Label>
                            <Textarea
                                id="description"
                                placeholder="Briefly describe what this course covers..."
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                className="bg-muted/30 border-border/40 min-h-[100px] resize-none"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="semester_start" className="text-sm font-bold">
                                    Semester Start
                                </Label>
                                <Input
                                    id="semester_start"
                                    type="date"
                                    value={formData.semester_start}
                                    onChange={(e) => setFormData({ ...formData, semester_start: e.target.value })}
                                    className="bg-muted/30 border-border/40 [color-scheme:dark]"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="semester_end" className="text-sm font-bold">
                                    Semester End
                                </Label>
                                <Input
                                    id="semester_end"
                                    type="date"
                                    value={formData.semester_end}
                                    onChange={(e) => setFormData({ ...formData, semester_end: e.target.value })}
                                    className="bg-muted/30 border-border/40 [color-scheme:dark]"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-3 pt-2">
                        <Button
                            type="button"
                            variant="outline"
                            className="flex-1 font-bold"
                            onClick={onClose}
                            disabled={isCreating}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            className="flex-1 font-bold bg-primary hover:bg-primary/90"
                            disabled={isCreating || !formData.title || !formData.subject}
                        >
                            {isCreating ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Creating...
                                </>
                            ) : (
                                'Create Course'
                            )}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
