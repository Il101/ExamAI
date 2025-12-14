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
  original_content: z.string().optional(),
});

type CreateExamFormData = z.infer<typeof createExamSchema>;

import { useRouter } from 'next/navigation';

const MAX_TOTAL_BYTES = 50 * 1024 * 1024; // 50MB

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
};

export function CreateExamForm({ onSuccess }: { onSuccess?: () => void }) {
  const router = useRouter();
  const { createExam, isCreating } = useExams();
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
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

    const formData = new FormData();
    formData.append('title', title);
    formData.append('subject', subject);
    formData.append('exam_type', exam_type);
    formData.append('level', level);

    if (uploadedFiles.length) {
      uploadedFiles.forEach((file) => formData.append('files', file));
    } else if (original_content) {
      const blob = new Blob([original_content], { type: 'text/plain' });
      const textFile = new File([blob], 'content.txt', { type: 'text/plain' });
      formData.append('files', textFile);
    } else {
      toast.error('Please upload a file or paste content');
      return;
    }

    createExam(formData, {
      onSuccess: (data) => {
        form.reset();
        setUploadedFiles([]);

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

  const handleFilesUpload = (files: File[]) => {
    setUploadedFiles((prev) => {
      const combined = [...prev, ...files].slice(0, 5);
      const total = combined.reduce((acc, f) => acc + f.size, 0);
      if (total > MAX_TOTAL_BYTES) {
        toast.error('Total size exceeds 50MB. Remove some files or choose smaller ones.');
        return prev;
      }
      return combined;
    });
    form.setValue('original_content', '');
  };

  const totalSize = uploadedFiles.reduce((acc, f) => acc + f.size, 0);

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
        <div className="space-y-3">
          {uploadedFiles.length > 0 && (
            <div className="border rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">Files selected ({uploadedFiles.length}/5)</p>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setUploadedFiles([])}
                >
                  Clear
                </Button>
              </div>
              <ul className="space-y-1 text-sm text-gray-700">
                {uploadedFiles.map((file, idx) => (
                  <li key={`${file.name}-${idx}`} className="flex items-center justify-between">
                    <span className="truncate">{file.name} · {formatBytes(file.size)}</span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setUploadedFiles((prev) => prev.filter((_, i) => i !== idx))}
                    >
                      Remove
                    </Button>
                  </li>
                ))}
              </ul>
              <p className="text-xs text-gray-500">Total size: {formatBytes(totalSize)} / 50MB</p>
            </div>
          )}

          <FileUploadZone
            onFilesSelected={handleFilesUpload}
            existingFilesCount={uploadedFiles.length}
            existingTotalBytes={totalSize}
          />
        </div>
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
