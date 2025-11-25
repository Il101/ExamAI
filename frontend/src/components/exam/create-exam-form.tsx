'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileUploadZone } from './file-upload-zone';
import { useExams } from '@/lib/hooks/use-exams';
import type { CreateExamRequest, Exam } from '@/lib/api/exams';
import { toast } from 'sonner';

const createExamSchema = z.object({
  title: z.string().min(3, 'Title must be at least 3 characters'),
  subject: z.string().min(2, 'Subject is required'),
  exam_type: z.enum(['oral', 'written', 'test']),
  level: z.enum(['school', 'bachelor', 'master', 'phd']),
  original_content: z.string().min(100, 'Content must be at least 100 characters'),
});

type CreateExamFormData = z.infer<typeof createExamSchema>;

import { useRouter } from 'next/navigation';

export function CreateExamForm({ onSuccess }: { onSuccess?: () => void }) {
  const router = useRouter();
  const { createExam, isCreating, startGeneration } = useExams();
  const [uploadedFile, setUploadedFile] = useState<string>('');
  const [examType, setExamType] = useState<'oral' | 'written' | 'test'>('written');
  const [level, setLevel] = useState<'school' | 'bachelor' | 'master' | 'phd'>('bachelor');

  const form = useForm<CreateExamFormData>({
    resolver: zodResolver(createExamSchema),
    defaultValues: {
      exam_type: 'written',
      level: 'bachelor',
    },
  });

  const onSubmit = (data: CreateExamFormData) => {
    const { title, subject, exam_type, level, original_content } = data;

    // Backend expects only: title, subject, exam_type, level, original_content
    createExam({
      title,
      subject,
      exam_type,
      level,
      original_content,
    } as CreateExamRequest, {
      onSuccess: (data) => {
        form.reset();
        setUploadedFile('');

        // Redirect to exam detail page
        // Cast data to any because the hook's return type might not be fully inferred
        const newExam = data as unknown as Exam;
        if (newExam && newExam.id) {
          toast.success('Exam draft created!');
          router.push(`/dashboard/exams/${newExam.id}`);
        }

        onSuccess?.();
      },
    });
  };

  const handleFileUpload = (content: string, filename: string) => {
    form.setValue('original_content', content);
    setUploadedFile(filename);
  };

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <Label htmlFor="title">Exam Title</Label>
        <Input
          id="title"
          placeholder="e.g., Calculus I Midterm"
          {...form.register('title')}
        />
        {form.formState.errors.title && (
          <p className="text-sm text-red-500 mt-1">{form.formState.errors.title.message}</p>
        )}
      </div>

      <div>
        <Label htmlFor="subject">Subject</Label>
        <Input
          id="subject"
          placeholder="e.g., Mathematics"
          {...form.register('subject')}
        />
        {form.formState.errors.subject && (
          <p className="text-sm text-red-500 mt-1">{form.formState.errors.subject.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Exam Type</Label>
          <Select
            value={examType}
            onValueChange={(value: 'oral' | 'written' | 'test') => {
              setExamType(value);
              form.setValue('exam_type', value);
            }}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="written">Written</SelectItem>
              <SelectItem value="oral">Oral</SelectItem>
              <SelectItem value="test">Test</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label>Academic Level</Label>
          <Select
            value={level}
            onValueChange={(value: 'school' | 'bachelor' | 'master' | 'phd') => {
              setLevel(value);
              form.setValue('level', value);
            }}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="school">School</SelectItem>
              <SelectItem value="bachelor">Bachelor</SelectItem>
              <SelectItem value="master">Master</SelectItem>
              <SelectItem value="phd">PhD</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label>Study Material</Label>
        {uploadedFile ? (
          <div className="border rounded-lg p-4 flex items-center justify-between">
            <p className="text-sm">Uploaded: {uploadedFile}</p>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                setUploadedFile('');
                form.setValue('original_content', '');
              }}
            >
              Remove
            </Button>
          </div>
        ) : (
          <FileUploadZone onFileContent={handleFileUpload} />
        )}
      </div>

      <div>
        <Label htmlFor="content">Or paste content</Label>
        <Textarea
          id="content"
          rows={6}
          placeholder="Paste your study material here..."
          {...form.register('original_content')}
        />
        {form.formState.errors.original_content && (
          <p className="text-sm text-red-500 mt-1">{form.formState.errors.original_content.message}</p>
        )}
      </div>

      <Button type="submit" disabled={isCreating} className="w-full">
        {isCreating ? 'Creating...' : 'Create Exam'}
      </Button>
    </form>
  );
}
