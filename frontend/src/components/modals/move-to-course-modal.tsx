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
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Folder, Loader2 } from 'lucide-react';
import { Exam } from '@/lib/api/exams';

interface MoveToCourseModalProps {
    exam: Exam | null;
    isOpen: boolean;
    onClose: () => void;
}

export function MoveToCourseModal({ exam, isOpen, onClose }: MoveToCourseModalProps) {
    const { courses, addExam, removeExam } = useCourses();
    const [selectedCourseId, setSelectedCourseId] = useState<string>(exam?.course_id || 'none');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleConfirm = async () => {
        if (!exam) return;

        try {
            setIsSubmitting(true);

            // If was in a course and now 'none' or different course, we might need to remove first
            // But the backend POST /courses/{course_id}/exams/{exam_id} handles moving

            if (selectedCourseId === 'none') {
                if (exam.course_id) {
                    await removeExam({ courseId: exam.course_id, examId: exam.id });
                }
            } else {
                await addExam({ courseId: selectedCourseId, examId: exam.id });
            }

            onClose();
        } catch (error) {
            // Error handled by hook
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-md bg-card/95 backdrop-blur-xl border-border/40">
                <DialogHeader>
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                        <Folder className="h-6 w-6 text-primary" />
                    </div>
                    <DialogTitle className="text-2xl font-bold">Move to Folder</DialogTitle>
                    <DialogDescription className="text-muted-foreground">
                        Select a course folder for &quot;{exam?.title}&quot;.
                    </DialogDescription>
                </DialogHeader>

                <div className="py-4">
                    <RadioGroup
                        value={selectedCourseId}
                        onValueChange={setSelectedCourseId}
                        className="space-y-3"
                    >
                        <div className="flex items-center space-x-3 rounded-lg border border-border/40 p-3 hover:bg-muted/30 transition-colors cursor-pointer">
                            <RadioGroupItem value="none" id="none" />
                            <Label htmlFor="none" className="flex-1 font-medium cursor-pointer">
                                Standalone (No Folder)
                            </Label>
                        </div>

                        {courses.map((course) => (
                            <div
                                key={course.id}
                                className="flex items-center space-x-3 rounded-lg border border-border/40 p-3 hover:bg-muted/30 transition-colors cursor-pointer"
                            >
                                <RadioGroupItem value={course.id} id={course.id} />
                                <div className="flex-1 cursor-pointer">
                                    <Label htmlFor={course.id} className="font-bold block">
                                        {course.title}
                                    </Label>
                                    <span className="text-xs text-muted-foreground">{course.subject}</span>
                                </div>
                            </div>
                        ))}
                    </RadioGroup>
                </div>

                <div className="flex gap-3 pt-2">
                    <Button
                        variant="outline"
                        className="flex-1 font-bold"
                        onClick={onClose}
                        disabled={isSubmitting}
                    >
                        Cancel
                    </Button>
                    <Button
                        className="flex-1 font-bold bg-primary hover:bg-primary/90"
                        onClick={handleConfirm}
                        disabled={isSubmitting || selectedCourseId === (exam?.course_id || 'none')}
                    >
                        {isSubmitting ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Moving...
                            </>
                        ) : (
                            'Confirm Move'
                        )}
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}
