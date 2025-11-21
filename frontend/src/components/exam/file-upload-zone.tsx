'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { parseFile } from '@/lib/file-parser';
import { toast } from 'sonner';

interface FileUploadZoneProps {
  onFileContent: (content: string, filename: string) => void;
  accept?: Record<string, string[]>;
  maxSize?: number;
}

export function FileUploadZone({
  onFileContent,
  accept = {
    'text/plain': ['.txt'],
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  },
  maxSize = 10 * 1024 * 1024, // 10MB
}: FileUploadZoneProps) {
  const [isProcessing, setIsProcessing] = useState(false);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setIsProcessing(true);
      try {
        const content = await parseFile(file);

        if (!content.trim()) {
          toast.error('Could not extract text from this file.');
          return;
        }

        onFileContent(content, file.name);
        toast.success('File processed successfully');
      } catch (error) {
        console.error('File processing error:', error);
        toast.error('Failed to process file. Please ensure it is a valid text, PDF, or DOCX file.');
      } finally {
        setIsProcessing(false);
      }
    },
    [onFileContent]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
    disabled: isProcessing,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors relative',
        isDragActive ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-gray-400',
        isProcessing ? 'cursor-wait opacity-70' : ''
      )}
    >
      <input {...getInputProps()} />

      {isProcessing ? (
        <div className="flex flex-col items-center">
          <Loader2 className="h-12 w-12 text-primary animate-spin mb-4" />
          <p className="text-lg font-medium">Processing file...</p>
          <p className="text-sm text-gray-500">Extracting text content</p>
        </div>
      ) : (
        <>
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          {isDragActive ? (
            <p>Drop the file here...</p>
          ) : (
            <>
              <p className="text-lg font-medium mb-2">Drag & drop your study material</p>
              <p className="text-sm text-gray-500">or click to browse (PDF, DOCX, TXT)</p>
              <p className="text-xs text-gray-400 mt-2">Max file size: 10MB</p>
            </>
          )}
        </>
      )}
    </div>
  );
}
