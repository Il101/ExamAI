'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';
import { examsApi, Exam } from '@/lib/api/exams';

interface ExamSelectModalProps {
    open: boolean;
    onClose: () => void;
    onSelect: (examId: string) => void;
}

export function ExamSelectModal({ open, onClose, onSelect }: ExamSelectModalProps) {
    const [exams, setExams] = useState<Exam[]>([]);
    const [selectedExamId, setSelectedExamId] = useState<string>('');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        if (open) {
            loadExams();
        }
    }, [open]);

    const loadExams = async () => {
        try {
            setIsLoading(true);
            const response = await examsApi.list();
            setExams(response.exams);

            // Auto-select first exam if available
            if (response.exams.length > 0) {
                setSelectedExamId(response.exams[0].id);
            }
        } catch (error) {
            console.error('Failed to load exams:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleConfirm = () => {
        if (selectedExamId) {
            onSelect(selectedExamId);
            onClose();
        }
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Select Exam for Study Session</DialogTitle>
                    <DialogDescription>
                        Choose which exam you want to focus on during this Pomodoro session.
                    </DialogDescription>
                </DialogHeader>

                {isLoading ? (
                    <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                ) : exams.length === 0 ? (
                    <div className="py-8 text-center text-muted-foreground">
                        <p>No exams found. Create an exam first to start a study session.</p>
                    </div>
                ) : (
                    <>
                        <RadioGroup value={selectedExamId} onValueChange={setSelectedExamId}>
                            <div className="space-y-3">
                                {exams.map((exam) => (
                                    <div key={exam.id} className="flex items-center space-x-2">
                                        <RadioGroupItem value={exam.id} id={exam.id} />
                                        <Label htmlFor={exam.id} className="flex-1 cursor-pointer">
                                            {exam.title}
                                        </Label>
                                    </div>
                                ))}
                            </div>
                        </RadioGroup>

                        <div className="flex justify-end gap-2 mt-4">
                            <Button variant="outline" onClick={onClose}>
                                Cancel
                            </Button>
                            <Button onClick={handleConfirm} disabled={!selectedExamId}>
                                Start Session
                            </Button>
                        </div>
                    </>
                )}
            </DialogContent>
        </Dialog>
    );
}
