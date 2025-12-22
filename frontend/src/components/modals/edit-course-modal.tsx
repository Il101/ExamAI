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
import { Settings, Loader2, Trash2, Calendar, RefreshCw } from 'lucide-react';
import { Course, coursesApi } from '@/lib/api/courses';
import { useAuth } from '@/lib/hooks/use-auth';
import { usersApi } from '@/lib/api/users';
import { toast } from 'sonner';

interface EditCourseModalProps {
    isOpen: boolean;
    onClose: () => void;
    course: Course;
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

export function EditCourseModal({ isOpen, onClose, course }: EditCourseModalProps) {
    const { user } = useAuth();
    const { updateCourse, deleteCourse, isUpdating, isDeleting } = useCourses();
    const [formData, setFormData] = useState({
        title: course.title,
        subject: course.subject,
        description: course.description || '',
        semester_start: course.semester_start || '',
        semester_end: course.semester_end || '',
        exam_date: course.exam_date ? course.exam_date.split('T')[0] : '',
    });
    const [studyDays, setStudyDays] = useState<number[]>([]);
    const [isRescheduling, setIsRescheduling] = useState(false);

    useEffect(() => {
        setFormData({
            title: course.title,
            subject: course.subject,
            description: course.description || '',
            semester_start: course.semester_start || '',
            semester_end: course.semester_end || '',
            exam_date: course.exam_date ? course.exam_date.split('T')[0] : '',
        });
        if (user?.study_days) {
            setStudyDays(user.study_days);
        } else {
            setStudyDays([0, 1, 2, 3, 4, 5, 6]);
        }
    }, [course, user]);

    const toggleDay = (day: number) => {
        setStudyDays(prev =>
            prev.includes(day)
                ? prev.filter(d => d !== day)
                : [...prev, day].sort()
        );
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.title || !formData.subject) return;

        try {
            // Update course
            await updateCourse({
                id: course.id,
                data: {
                    ...formData,
                    semester_start: formData.semester_start || undefined,
                    semester_end: formData.semester_end || undefined,
                    exam_date: formData.exam_date || undefined,
                }
            });
            // Update user study days
            await usersApi.updateProfile({ study_days: studyDays });
            toast.success('Folder settings saved!');
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

    const handleReschedule = async () => {
        if (!formData.exam_date) {
            toast.error('Please set an exam date first');
            return;
        }

        setIsRescheduling(true);
        try {
            await coursesApi.reschedule(course.id);
            toast.success('Study schedule updated!');
        } catch (error: any) {
            toast.error(error?.response?.data?.detail || 'Failed to reschedule');
        } finally {
            setIsRescheduling(false);
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
                        Update your course folder details, study schedule, or delete the folder.
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

                        <div className="space-y-2">
                            <Label htmlFor="exam_date" className="text-sm font-bold flex items-center gap-2">
                                <Calendar className="h-4 w-4" />
                                Exam Date
                            </Label>
                            <Input
                                id="exam_date"
                                type="date"
                                value={formData.exam_date}
                                onChange={(e) => setFormData({ ...formData, exam_date: e.target.value })}
                                className="bg-muted/30 border-border/40 [color-scheme:dark]"
                            />
                            <p className="text-[10px] text-muted-foreground italic">
                                The deadline for all topics in this course.
                            </p>
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
                                Topics in this course will only be scheduled for these days.
                            </p>
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
                            variant="outline"
                            className="w-full font-bold"
                            onClick={handleReschedule}
                            disabled={isUpdating || isDeleting || isRescheduling || !formData.exam_date}
                        >
                            {isRescheduling ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Rescheduling...
                                </>
                            ) : (
                                <>
                                    <RefreshCw className="mr-2 h-4 w-4" />
                                    Refresh Study Schedule
                                </>
                            )}
                        </Button>

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
