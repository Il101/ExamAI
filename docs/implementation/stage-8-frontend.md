# Stage 8: Frontend - Next.js 14 Application

**Time:** 5-7 days  
**Goal:** Build modern, responsive frontend with Next.js 14, React Server Components, and shadcn/ui

## 8.1 Frontend Architecture

### Philosophy
- **Server Components**: Use React Server Components where possible for better performance
- **Client Components**: Only for interactivity (forms, modals, animations)
- **Type Safety**: Full TypeScript coverage
- **Component Composition**: Small, reusable components
- **State Management**: Zustand for client state, React Query for server state
- **Design System**: Dark Mode by default, "Cyberpunk/Modern Clean" aesthetic (Nov 2025 trend)

### Tech Stack
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Zinc/Slate theme with vibrant accents)
- **State Management**: Zustand + React Query
- **Forms**: React Hook Form + Zod
- **HTTP Client**: Axios
- **Icons**: Lucide React

---

## 8.2 Project Setup

### Step 8.2.1: Create Next.js Project
```bash
# Create Next.js project
npx create-next-app@latest frontend --typescript --tailwind --app --eslint

cd frontend

# Install dependencies
npm install @tanstack/react-query zustand axios react-hook-form zod lucide-react
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-toast
npm install class-variance-authority clsx tailwind-merge
npm install react-dropzone react-markdown

# Install shadcn/ui CLI
npx shadcn-ui@latest init

# Add shadcn/ui components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add form
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add progress
npx shadcn-ui@latest add tabs
```

### Step 8.2.2: Project Structure
```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/             # Auth group (login, register)
│   │   ├── (dashboard)/        # Protected routes
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── components/
│   │   ├── ui/                 # shadcn/ui primitives
│   │   ├── exam/               # Exam-related components
│   │   ├── study/              # Study session components
│   │   ├── layout/             # Layout components
│   │   └── shared/             # Shared components
│   │
│   ├── lib/
│   │   ├── api/                # API client
│   │   ├── hooks/              # Custom React hooks
│   │   ├── stores/             # Zustand stores
│   │   ├── utils/              # Utility functions
│   │   └── validations/        # Zod schemas
│   │
│   └── types/                  # TypeScript types
│
├── public/                     # Static assets
└── package.json
```

---

## 8.3 API Client Setup

### Step 8.3.1: Axios Instance
```typescript
// src/lib/api/client.ts
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add auth token)
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor (handle errors)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

### Step 8.3.2: API Service Functions
```typescript
// src/lib/api/auth.ts
import { apiClient } from './client';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post('/auth/login', data);
    return response.data;
  },

  register: async (data: RegisterRequest) => {
    const response = await apiClient.post('/auth/register', data);
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  logout: async () => {
    await apiClient.post('/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};
```

```typescript
// src/lib/api/exams.ts
import { apiClient } from './client';

export interface CreateExamRequest {
  title: string;
  subject: string;
  exam_type: 'oral' | 'written' | 'test';
  level: 'school' | 'bachelor' | 'master' | 'phd';
  original_content: string;
}

export const examsApi = {
  create: async (data: CreateExamRequest) => {
    const response = await apiClient.post('/exams', data);
    return response.data;
  },

  list: async (params?: { status?: string; limit?: number; offset?: number }) => {
    const response = await apiClient.get('/exams', { params });
    return response.data;
  },

  getById: async (examId: string) => {
    const response = await apiClient.get(`/exams/${examId}`);
    return response.data;
  },

  delete: async (examId: string) => {
    await apiClient.delete(`/exams/${examId}`);
  },

  startGeneration: async (examId: string) => {
    const response = await apiClient.post(`/exams/${examId}/generate`);
    return response.data;
  },

  getTaskStatus: async (taskId: string) => {
    const response = await apiClient.get(`/tasks/${taskId}`);
    return response.data;
  },
};
```

---

## 8.4 State Management

### Step 8.4.1: Auth Store (Zustand)
```typescript
// src/lib/stores/auth-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  full_name: string;
  subscription_plan: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,

      setUser: (user) => set({ user, isAuthenticated: !!user }),

      logout: () => {
        set({ user: null, isAuthenticated: false });
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

### Step 8.4.2: React Query Setup
```typescript
// src/lib/providers/query-provider.tsx
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

---

## 8.5 Custom Hooks

### Step 8.5.1: useExams Hook
```typescript
// src/lib/hooks/use-exams.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { examsApi, CreateExamRequest } from '@/lib/api/exams';
import { useToast } from '@/components/ui/use-toast';

export function useExams() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: exams, isLoading } = useQuery({
    queryKey: ['exams'],
    queryFn: () => examsApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateExamRequest) => examsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exams'] });
      toast({
        title: 'Exam created',
        description: 'Your exam has been created successfully.',
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.error?.message || 'Failed to create exam',
        variant: 'destructive',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (examId: string) => examsApi.delete(examId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exams'] });
      toast({
        title: 'Exam deleted',
        description: 'Your exam has been deleted.',
      });
    },
  });

  return {
    exams: exams?.exams || [],
    isLoading,
    createExam: createMutation.mutate,
    deleteExam: deleteMutation.mutate,
    isCreating: createMutation.isPending,
  };
}
```

### Step 8.5.2: useExamGeneration Hook
```typescript
// src/lib/hooks/use-exam-generation.ts
import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { examsApi } from '@/lib/api/exams';

export function useExamGeneration(examId: string) {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const queryClient = useQueryClient();

  const startMutation = useMutation({
    mutationFn: () => examsApi.startGeneration(examId),
    onSuccess: (data) => {
      setTaskId(data.task_id);
    },
  });

  // Poll task status
  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(async () => {
      try {
        const taskStatus = await examsApi.getTaskStatus(taskId);

        if (taskStatus.state === 'PROGRESS') {
          setProgress(taskStatus.current);
          setStatus(taskStatus.status);
        } else if (taskStatus.state === 'SUCCESS') {
          setProgress(100);
          setStatus('Complete');
          clearInterval(interval);
          queryClient.invalidateQueries({ queryKey: ['exam', examId] });
        } else if (taskStatus.state === 'FAILURE') {
          setStatus('Failed');
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Error polling task:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [taskId, examId, queryClient]);

  return {
    startGeneration: startMutation.mutate,
    isGenerating: !!taskId && progress < 100,
    progress,
    status,
  };
}
```

---

## 8.6 Key Components

### Step 8.6.1: File Upload Component
```typescript
// src/components/exam/file-upload-zone.tsx
'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File } from 'lucide-react';
import { cn } from '@/lib/utils';

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
  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      // Read file content
      const reader = new FileReader();
      reader.onload = () => {
        const content = reader.result as string;
        onFileContent(content, file.name);
      };
      reader.readAsText(file);
    },
    [onFileContent]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
        isDragActive ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-gray-400'
      )}
    >
      <input {...getInputProps()} />
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
    </div>
  );
}
```

### Step 8.6.2: Create Exam Form
```typescript
// src/components/exam/create-exam-form.tsx
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

const createExamSchema = z.object({
  title: z.string().min(3, 'Title must be at least 3 characters'),
  subject: z.string().min(2, 'Subject is required'),
  exam_type: z.enum(['oral', 'written', 'test']),
  level: z.enum(['school', 'bachelor', 'master', 'phd']),
  original_content: z.string().min(100, 'Content must be at least 100 characters'),
});

type CreateExamFormData = z.infer<typeof createExamSchema>;

export function CreateExamForm({ onSuccess }: { onSuccess?: () => void }) {
  const { createExam, isCreating } = useExams();
  const [uploadedFile, setUploadedFile] = useState<string>('');

  const form = useForm<CreateExamFormData>({
    resolver: zodResolver(createExamSchema),
    defaultValues: {
      exam_type: 'written',
      level: 'bachelor',
    },
  });

  const onSubmit = (data: CreateExamFormData) => {
    createExam(data, {
      onSuccess: () => {
        form.reset();
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
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Exam Type</Label>
          <Select
            value={form.watch('exam_type')}
            onValueChange={(value) => form.setValue('exam_type', value as any)}
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
            value={form.watch('level')}
            onValueChange={(value) => form.setValue('level', value as any)}
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
          <div className="border rounded-lg p-4">
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
      </div>

      <Button type="submit" disabled={isCreating} className="w-full">
        {isCreating ? 'Creating...' : 'Create Exam'}
      </Button>
    </form>
  );
}
```

### Step 8.6.3: Exam Card Component
```typescript
// src/components/exam/exam-card.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FileText, Trash2, Play } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';

interface ExamCardProps {
  exam: {
    id: string;
    title: string;
    subject: string;
    status: string;
    topic_count: number;
    created_at: string;
  };
  onDelete?: () => void;
  onGenerate?: () => void;
}

export function ExamCard({ exam, onDelete, onGenerate }: ExamCardProps) {
  const statusColors = {
    draft: 'bg-gray-100 text-gray-800',
    generating: 'bg-blue-100 text-blue-800',
    ready: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{exam.title}</CardTitle>
            <p className="text-sm text-gray-500 mt-1">{exam.subject}</p>
          </div>
          <Badge className={statusColors[exam.status as keyof typeof statusColors]}>
            {exam.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            <p>{exam.topic_count} topics</p>
            <p>Created {formatDistanceToNow(new Date(exam.created_at), { addSuffix: true })}</p>
          </div>
          <div className="flex gap-2">
            {exam.status === 'draft' && onGenerate && (
              <Button size="sm" onClick={onGenerate}>
                <Play className="h-4 w-4 mr-1" />
                Generate
              </Button>
            )}
            {exam.status === 'ready' && (
              <Link href={`/exams/${exam.id}`}>
                <Button size="sm">
                  <FileText className="h-4 w-4 mr-1" />
                  View
                </Button>
              </Link>
            )}
            {onDelete && (
              <Button size="sm" variant="ghost" onClick={onDelete}>
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## 8.7 Pages

### Step 8.7.1: Login Page
```typescript
// src/app/(auth)/login/page.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { authApi } from '@/lib/api/auth';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const setUser = useAuthStore((state) => state.setUser);
  
  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      const response = await authApi.login(data);
      
      // Save tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      
      // Get user info
      const user = await authApi.getCurrentUser();
      setUser(user);
      
      router.push('/dashboard');
    } catch (error: any) {
      alert(error.response?.data?.error?.message || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md p-8">
        <h1 className="text-2xl font-bold mb-6">Login to ExamAI Pro</h1>
        
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              {...form.register('email')}
            />
          </div>

          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              {...form.register('password')}
            />
          </div>

          <Button type="submit" className="w-full">
            Login
          </Button>
        </form>

        <p className="text-center text-sm text-gray-600 mt-4">
          Don't have an account?{' '}
          <Link href="/register" className="text-primary hover:underline">
            Register
          </Link>
        </p>
      </Card>
    </div>
  );
}
```

---

## 8.8 Best Practices & Next Steps

### Best Practices
- **Server Components by default**: Only use 'use client' when needed
- **Type safety**: TypeScript everywhere
- **Error boundaries**: Handle errors gracefully
- **Loading states**: Show skeletons/spinners
- **Responsive design**: Mobile-first approach

### Next Steps
1. Implement all pages and components
2. Add animations with Framer Motion
3. Implement dark mode
4. Add PWA support
5. Proceed to **Stage 9: Testing**
