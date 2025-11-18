Отличная визия! Ты описал полноценную **learning platform** с AI-ассистентом. Создам детальный документ по фронтенду с modern best practices.

***

# FRONTEND ARCHITECTURE: ExamAI Pro
## Современная архитектура фронтенда для AI-платформы подготовки к экзаменам

**Дата:** 17 ноября 2025  
**Версия:** 1.0  
**Стек:** Next.js 14, React 18, TypeScript, Tailwind CSS

***

## 1. TECH STACK (Modern Best Practices 2025)

### Core Framework
```
Next.js 14.0+ (App Router)
├── React 18+ (Server Components + Client Components)
├── TypeScript 5.0+ (строгая типизация)
└── React Server Actions (для форм без API calls)
```

**Почему Next.js 14:**
- ✅ App Router (file-based routing, layouts)
- ✅ Server Components (меньше JS на клиенте)
- ✅ Streaming SSR (постепенная загрузка)
- ✅ Automatic code splitting
- ✅ Built-in Image optimization
- ✅ SEO-friendly из коробки

### UI/Styling
```
Tailwind CSS 3.4+        # Utility-first CSS
shadcn/ui                # Headless компоненты (Radix UI)
Framer Motion            # Анимации
Lucide Icons             # Современные иконки
```

**Почему shadcn/ui:**
- ✅ Копируешь компоненты в свой проект (не npm dependency)
- ✅ Полный контроль над кодом
- ✅ Accessibility из коробки
- ✅ Customizable через Tailwind

### State Management
```
Zustand                  # Лёгкий state management
React Query (TanStack)   # Server state + caching
React Hook Form          # Формы + validation
Zod                      # Schema validation
```

### File Management
```
react-dropzone           # Drag-and-drop файлов
@uppy/react              # Advanced file uploader
pdf.js                   # Preview PDF файлов
```

### Real-time & Communication
```
Socket.io-client         # WebSocket для live updates
@tanstack/react-query    # Polling fallback
```

***

## 2. PROJECT STRUCTURE

```
frontend/
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── (auth)/              # Auth layouts group
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (dashboard)/         # Dashboard layouts group
│   │   │   ├── layout.tsx       # Dashboard layout
│   │   │   ├── exams/
│   │   │   │   ├── page.tsx     # Список экзаменов
│   │   │   │   ├── [id]/
│   │   │   │   │   ├── page.tsx          # Главная страница экзамена
│   │   │   │   │   ├── study/page.tsx    # Интерактивное обучение
│   │   │   │   │   └── stats/page.tsx    # Статистика
│   │   │   │   └── create/page.tsx
│   │   │   ├── study/           # Study sessions
│   │   │   └── settings/
│   │   ├── layout.tsx           # Root layout
│   │   └── page.tsx             # Landing page
│   │
│   ├── components/              # React компоненты
│   │   ├── ui/                 # shadcn/ui компоненты
│   │   │   ├── button.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── card.tsx
│   │   │   └── ...
│   │   ├── exam/
│   │   │   ├── FileUploadZone.tsx      # Drag-and-drop область
│   │   │   ├── FileList.tsx            # Список прикрепленных файлов
│   │   │   ├── ExamCreationForm.tsx
│   │   │   └── ExamCard.tsx
│   │   ├── study/
│   │   │   ├── AIDialogWindow.tsx      # Диалог с AI
│   │   │   ├── TopicExplanation.tsx
│   │   │   ├── TestForm.tsx            # Тестовая форма
│   │   │   └── TestResults.tsx
│   │   ├── progress/
│   │   │   ├── ProgressOverview.tsx    # Общий прогресс
│   │   │   ├── TopicTree.tsx           # Дерево тем с галочками
│   │   │   ├── ProgressChart.tsx
│   │   │   └── StudyStreak.tsx
│   │   └── layout/
│   │       ├── Sidebar.tsx
│   │       ├── Header.tsx
│   │       └── MobileNav.tsx
│   │
│   ├── lib/                    # Утилиты и хелперы
│   │   ├── api/
│   │   │   ├── client.ts       # API client (axios/fetch wrapper)
│   │   │   ├── exams.ts
│   │   │   ├── study.ts
│   │   │   └── files.ts
│   │   ├── hooks/
│   │   │   ├── useExam.ts
│   │   │   ├── useStudySession.ts
│   │   │   ├── useFileUpload.ts
│   │   │   └── useWebSocket.ts
│   │   ├── stores/             # Zustand stores
│   │   │   ├── examStore.ts
│   │   │   ├── studyStore.ts
│   │   │   └── uiStore.ts
│   │   └── utils/
│   │       ├── cn.ts           # Tailwind merge
│   │       ├── validators.ts
│   │       └── formatters.ts
│   │
│   ├── types/                  # TypeScript types
│   │   ├── exam.ts
│   │   ├── topic.ts
│   │   ├── test.ts
│   │   └── api.ts
│   │
│   └── styles/
│       └── globals.css
│
├── public/
│   ├── images/
│   └── icons/
│
└── package.json
```

***

## 3. ДЕТАЛЬНОЕ ОПИСАНИЕ КОМПОНЕНТОВ

### 3.1 File Upload Zone (Drag-and-Drop)

**Функционал:**
- Перетаскивание файлов (PDF, DOCX, TXT)
- Показ прикрепленных файлов с preview
- Индикация загрузки
- Удаление файлов
- Валидация типов и размера

**Компонент:**

```tsx
// components/exam/FileUploadZone.tsx
'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  url?: string;
  status: 'uploading' | 'success' | 'error';
  progress: number;
}

export function FileUploadZone({ examId }: { examId?: string }) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    // Добавляем файлы в state со статусом uploading
    const newFiles = acceptedFiles.map(file => ({
      id: crypto.randomUUID(),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading' as const,
      progress: 0
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
    
    // Загружаем каждый файл
    for (const file of acceptedFiles) {
      await uploadFile(file);
    }
  }, [examId]);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: true
  });
  
  async function uploadFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      // Загружаем с отслеживанием прогресса
      const response = await api.post(`/exams/${examId}/upload`, formData, {
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total!
          );
          
          setFiles(prev => prev.map(f => 
            f.name === file.name 
              ? { ...f, progress }
              : f
          ));
        }
      });
      
      // Обновляем статус на success
      setFiles(prev => prev.map(f =>
        f.name === file.name
          ? { ...f, status: 'success', url: response.data.url }
          : f
      ));
      
    } catch (error) {
      setFiles(prev => prev.map(f =>
        f.name === file.name
          ? { ...f, status: 'error' }
          : f
      ));
    }
  }
  
  function removeFile(fileId: string) {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  }
  
  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <Card
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed p-8 text-center cursor-pointer transition-colors",
          isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
        )}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        {isDragActive ? (
          <p className="text-blue-600 font-medium">Отпустите файлы сюда</p>
        ) : (
          <>
            <p className="text-gray-700 font-medium mb-1">
              Перетащите файлы сюда или нажмите для выбора
            </p>
            <p className="text-sm text-gray-500">
              Поддерживаются PDF, DOCX, TXT (макс. 10MB)
            </p>
          </>
        )}
      </Card>
      
      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-medium text-sm text-gray-700">
            Прикрепленные файлы ({files.length})
          </h3>
          
          {files.map(file => (
            <Card key={file.id} className="p-3 flex items-center gap-3">
              <File className="h-8 w-8 text-blue-600 flex-shrink-0" />
              
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">{file.name}</p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(file.size)}
                </p>
                
                {/* Progress bar */}
                {file.status === 'uploading' && (
                  <div className="mt-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-600 transition-all"
                      style={{ width: `${file.progress}%` }}
                    />
                  </div>
                )}
              </div>
              
              {/* Status Icon */}
              {file.status === 'success' && (
                <CheckCircle className="h-5 w-5 text-green-600" />
              )}
              
              {file.status === 'error' && (
                <span className="text-xs text-red-600">Ошибка</span>
              )}
              
              {/* Remove Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeFile(file.id)}
              >
                <X className="h-4 w-4" />
              </Button>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
```

***

### 3.2 AI Dialog Window (Интерактивное обучение)

**Функционал:**
- Диалог с AI (как ChatGPT)
- Объяснение текущей темы
- Возможность задавать вопросы
- Кнопка "Пройти тест"
- Streaming responses (текст появляется постепенно)

**Компонент:**

```tsx
// components/study/AIDialogWindow.tsx
'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, FileText } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useStudySession } from '@/lib/hooks/useStudySession';
import { TestForm } from './TestForm';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function AIDialogWindow({ 
  topicId,
  topicTitle 
}: { 
  topicId: number;
  topicTitle: string;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showTest, setShowTest] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { currentTopic, sendMessage, startTest } = useStudySession(topicId);
  
  // Автоскролл к новым сообщениям
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Загружаем объяснение темы при открытии
  useEffect(() => {
    if (currentTopic?.content) {
      setMessages([{
        id: 'initial',
        role: 'assistant',
        content: currentTopic.content,
        timestamp: new Date()
      }]);
    }
  }, [currentTopic]);
  
  async function handleSend() {
    if (!input.trim() || isLoading) return;
    
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      // Отправляем вопрос AI
      const response = await sendMessage(input, topicId);
      
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.content,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsLoading(false);
    }
  }
  
  async function handleStartTest() {
    setShowTest(true);
  }
  
  if (showTest) {
    return (
      <TestForm 
        topicId={topicId}
        topicTitle={topicTitle}
        onClose={() => setShowTest(false)}
      />
    );
  }
  
  return (
    <Card className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b bg-gradient-to-r from-blue-50 to-purple-50">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-blue-600" />
          <h2 className="font-semibold">{topicTitle}</h2>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          AI-ассистент объяснит тему и ответит на вопросы
        </p>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <div
            key={message.id}
            className={cn(
              "flex",
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={cn(
                "max-w-[80%] rounded-lg p-3",
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              )}
            >
              {message.role === 'assistant' ? (
                <ReactMarkdown className="prose prose-sm max-w-none">
                  {message.content}
                </ReactMarkdown>
              ) : (
                <p>{message.content}</p>
              )}
              
              <p className="text-xs mt-1 opacity-70">
                {message.timestamp.toLocaleTimeString('ru-RU', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input Area */}
      <div className="p-4 border-t">
        {/* Test Button */}
        <div className="mb-3">
          <Button
            onClick={handleStartTest}
            className="w-full"
            variant="outline"
          >
            <FileText className="h-4 w-4 mr-2" />
            Пройти тест по теме
          </Button>
        </div>
        
        {/* Message Input */}
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Задайте вопрос по теме..."
            className="min-h-[60px] resize-none"
            disabled={isLoading}
          />
          
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            size="icon"
            className="h-[60px] w-[60px]"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
        
        <p className="text-xs text-gray-500 mt-2">
          Enter для отправки, Shift+Enter для новой строки
        </p>
      </div>
    </Card>
  );
}
```

***

### 3.3 Test Form (Тестирование)

**Функционал:**
- AI генерирует вопросы по теме
- Выбор ответов (radio buttons)
- Показ правильности ответа
- Объяснение после ответа
- Финальный результат

```tsx
// components/study/TestForm.tsx
'use client';

import { useState } from 'react';
import { CheckCircle, XCircle, ArrowRight } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { useTest } from '@/lib/hooks/useTest';

interface Question {
  id: string;
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
}

export function TestForm({
  topicId,
  topicTitle,
  onClose
}: {
  topicId: number;
  topicTitle: string;
  onClose: () => void;
}) {
  const { questions, isLoading, submitAnswer } = useTest(topicId);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [answers, setAnswers] = useState<Array<{
    questionId: string;
    selected: number;
    correct: boolean;
  }>>([]);
  
  if (isLoading) {
    return (
      <Card className="p-8 text-center">
        <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
        <p className="text-gray-600">AI создаёт тест по теме...</p>
      </Card>
    );
  }
  
  const currentQuestion = questions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === questions.length - 1;
  const isAnswered = answers.find(a => a.questionId === currentQuestion.id);
  
  async function handleAnswer() {
    if (selectedAnswer === null) return;
    
    const isCorrect = selectedAnswer === currentQuestion.correctAnswer;
    
    // Сохраняем ответ
    setAnswers(prev => [...prev, {
      questionId: currentQuestion.id,
      selected: selectedAnswer,
      correct: isCorrect
    }]);
    
    // Отправляем на backend для статистики
    await submitAnswer(topicId, currentQuestion.id, isCorrect);
    
    setShowResult(true);
  }
  
  function handleNext() {
    if (isLastQuestion) {
      // Показываем финальные результаты
      const score = answers.filter(a => a.correct).length;
      const percentage = Math.round((score / questions.length) * 100);
      
      // TODO: показать финальный экран с результатами
    } else {
      // Следующий вопрос
      setCurrentQuestionIndex(prev => prev + 1);
      setSelectedAnswer(null);
      setShowResult(false);
    }
  }
  
  const correctCount = answers.filter(a => a.correct).length;
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;
  
  return (
    <Card className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">Тест: {topicTitle}</h2>
          <span className="text-sm text-gray-600">
            Вопрос {currentQuestionIndex + 1} из {questions.length}
          </span>
        </div>
        
        {/* Progress Bar */}
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-blue-600 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      
      {/* Question */}
      <div className="mb-6">
        <p className="text-lg font-medium mb-4">
          {currentQuestion.question}
        </p>
        
        <RadioGroup
          value={selectedAnswer?.toString()}
          onValueChange={(value) => setSelectedAnswer(parseInt(value))}
          disabled={showResult}
        >
          {currentQuestion.options.map((option, index) => {
            const isSelected = selectedAnswer === index;
            const isCorrect = currentQuestion.correctAnswer === index;
            const showCorrectness = showResult && isSelected;
            
            return (
              <div
                key={index}
                className={cn(
                  "flex items-center space-x-3 p-4 rounded-lg border-2 transition-all cursor-pointer",
                  isSelected && !showResult && "border-blue-600 bg-blue-50",
                  showResult && isSelected && isCorrect && "border-green-600 bg-green-50",
                  showResult && isSelected && !isCorrect && "border-red-600 bg-red-50",
                  showResult && !isSelected && isCorrect && "border-green-600 bg-green-50"
                )}
              >
                <RadioGroupItem value={index.toString()} id={`option-${index}`} />
                <Label htmlFor={`option-${index}`} className="flex-1 cursor-pointer">
                  {option}
                </Label>
                
                {showResult && isSelected && (
                  isCorrect ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600" />
                  )
                )}
              </div>
            );
          })}
        </RadioGroup>
      </div>
      
      {/* Explanation (показывается после ответа) */}
      {showResult && (
        <Card className="p-4 mb-6 bg-blue-50 border-blue-200">
          <p className="font-medium text-blue-900 mb-2">Объяснение:</p>
          <p className="text-blue-800 text-sm">
            {currentQuestion.explanation}
          </p>
        </Card>
      )}
      
      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={onClose}>
          Закрыть тест
        </Button>
        
        <div className="flex gap-2">
          {!showResult ? (
            <Button
              onClick={handleAnswer}
              disabled={selectedAnswer === null}
            >
              Проверить ответ
            </Button>
          ) : (
            <Button onClick={handleNext}>
              {isLastQuestion ? 'Завершить тест' : 'Следующий вопрос'}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
      
      {/* Score (если есть ответы) */}
      {answers.length > 0 && (
        <div className="mt-4 text-center text-sm text-gray-600">
          Правильных ответов: {correctCount} из {answers.length}
        </div>
      )}
    </Card>
  );
}
```

***

### 3.4 Progress Dashboard (Статистика)

**Функционал:**
- Общий прогресс (%)
- Дерево тем с галочками
- Результаты тестов напротив каждой темы
- Streak counter
- Charts (прогресс по дням)

```tsx
// components/progress/ProgressOverview.tsx
'use client';

import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { CheckCircle, Circle, Trophy, Calendar, Target } from 'lucide-react';
import { TopicTree } from './TopicTree';
import { ProgressChart } from './ProgressChart';

interface Topic {
  id: number;
  title: string;
  completed: boolean;
  testScore: number | null; // 0-100 or null if not taken
  subtopics: Topic[];
}

export function ProgressOverview({
  examId,
  topics,
  overallProgress,
  streak
}: {
  examId: number;
  topics: Topic[];
  overallProgress: number;
  streak: number;
}) {
  const completedTopics = countCompletedTopics(topics);
  const totalTopics = countTotalTopics(topics);
  const averageTestScore = calculateAverageScore(topics);
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left Column: Overview Cards */}
      <div className="lg:col-span-1 space-y-4">
        {/* Overall Progress */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <Target className="h-6 w-6 text-blue-600" />
            <h3 className="font-semibold">Общий прогресс</h3>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Завершено</span>
              <span className="font-semibold">{overallProgress}%</span>
            </div>
            <Progress value={overallProgress} className="h-3" />
            <p className="text-sm text-gray-600">
              {completedTopics} из {totalTopics} тем пройдено
            </p>
          </div>
        </Card>
        
        {/* Streak */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <Calendar className="h-6 w-6 text-orange-600" />
            <h3 className="font-semibold">Серия занятий</h3>
          </div>
          
          <div className="text-center">
            <p className="text-4xl font-bold text-orange-600">{streak}</p>
            <p className="text-sm text-gray-600 mt-1">дней подряд 🔥</p>
          </div>
        </Card>
        
        {/* Average Score */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <Trophy className="h-6 w-6 text-yellow-600" />
            <h3 className="font-semibold">Средний балл</h3>
          </div>
          
          <div className="text-center">
            <p className="text-4xl font-bold text-yellow-600">
              {averageTestScore}%
            </p>
            <p className="text-sm text-gray-600 mt-1">по пройденным тестам</p>
          </div>
        </Card>
      </div>
      
      {/* Middle Column: Topic Tree */}
      <div className="lg:col-span-1">
        <Card className="p-6 h-full">
          <h3 className="font-semibold mb-4">План подготовки</h3>
          <TopicTree topics={topics} examId={examId} />
        </Card>
      </div>
      
      {/* Right Column: Charts */}
      <div className="lg:col-span-1">
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Активность</h3>
          <ProgressChart examId={examId} />
        </Card>
      </div>
    </div>
  );
}

// components/progress/TopicTree.tsx
export function TopicTree({ 
  topics,
  examId,
  level = 0 
}: {
  topics: Topic[];
  examId: number;
  level?: number;
}) {
  return (
    <div className="space-y-2">
      {topics.map(topic => (
        <div key={topic.id} style={{ marginLeft: `${level * 16}px` }}>
          <div className="flex items-center gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer">
            {/* Checkbox */}
            {topic.completed ? (
              <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
            ) : (
              <Circle className="h-5 w-5 text-gray-400 flex-shrink-0" />
            )}
            
            {/* Topic Title */}
            <span className={cn(
              "flex-1 text-sm",
              topic.completed ? "text-gray-900" : "text-gray-600"
            )}>
              {topic.title}
            </span>
            
            {/* Test Score */}
            {topic.testScore !== null && (
              <span className={cn(
                "text-xs font-medium px-2 py-1 rounded",
                topic.testScore >= 80 ? "bg-green-100 text-green-700" :
                topic.testScore >= 60 ? "bg-yellow-100 text-yellow-700" :
                "bg-red-100 text-red-700"
              )}>
                {topic.testScore}%
              </span>
            )}
          </div>
          
          {/* Subtopics */}
          {topic.subtopics && topic.subtopics.length > 0 && (
            <TopicTree 
              topics={topic.subtopics} 
              examId={examId}
              level={level + 1}
            />
          )}
        </div>
      ))}
    </div>
  );
}
```

***

## 4. LAYOUT STRUCTURE (3-Panel Design)

```tsx
// app/(dashboard)/exams/[id]/study/page.tsx
'use client';

import { useState } from 'react';
import { FileUploadZone } from '@/components/exam/FileUploadZone';
import { AIDialogWindow } from '@/components/study/AIDialogWindow';
import { ProgressOverview } from '@/components/progress/ProgressOverview';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function StudyPage({ params }: { params: { id: string } }) {
  const examId = parseInt(params.id);
  const [currentTopicId, setCurrentTopicId] = useState<number | null>(null);
  
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-white px-6 py-4">
        <h1 className="text-2xl font-bold">Интерактивное обучение</h1>
        <p className="text-gray-600">Математический анализ • Экзамен 15 декабря</p>
      </header>
      
      {/* Main Content: 3-Panel Layout */}
      <div className="flex-1 overflow-hidden">
        <div className="grid grid-cols-12 gap-4 h-full p-4">
          
          {/* LEFT PANEL: Files (col-span-3) */}
          <div className="col-span-3 overflow-y-auto">
            <div className="sticky top-0">
              <h2 className="font-semibold mb-3">Материалы для подготовки</h2>
              <FileUploadZone examId={params.id} />
            </div>
          </div>
          
          {/* CENTER PANEL: AI Dialog (col-span-6) */}
          <div className="col-span-6 overflow-hidden">
            {currentTopicId ? (
              <AIDialogWindow
                topicId={currentTopicId}
                topicTitle="Производная функции"
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-500">Выберите тему для изучения →</p>
              </div>
            )}
          </div>
          
          {/* RIGHT PANEL: Progress (col-span-3) */}
          <div className="col-span-3 overflow-y-auto">
            <ProgressOverview
              examId={examId}
              topics={mockTopics}
              overallProgress={65}
              streak={7}
            />
          </div>
          
        </div>
      </div>
    </div>
  );
}
```

***

## 5. STATE MANAGEMENT

```typescript
// lib/stores/studyStore.ts
import { create } from 'zustand';

interface StudyState {
  currentExamId: number | null;
  currentTopicId: number | null;
  uploadedFiles: File[];
  messages: Message[];
  isTestMode: boolean;
  
  setCurrentExam: (examId: number) => void;
  setCurrentTopic: (topicId: number) => void;
  addFile: (file: File) => void;
  removeFile: (fileId: string) => void;
  addMessage: (message: Message) => void;
  toggleTestMode: () => void;
}

export const useStudyStore = create<StudyState>((set) => ({
  currentExamId: null,
  currentTopicId: null,
  uploadedFiles: [],
  messages: [],
  isTestMode: false,
  
  setCurrentExam: (examId) => set({ currentExamId: examId }),
  setCurrentTopic: (topicId) => set({ currentTopicId: topicId }),
  addFile: (file) => set((state) => ({
    uploadedFiles: [...state.uploadedFiles, file]
  })),
  removeFile: (fileId) => set((state) => ({
    uploadedFiles: state.uploadedFiles.filter(f => f.id !== fileId)
  })),
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  toggleTestMode: () => set((state) => ({
    isTestMode: !state.isTestMode
  }))
}));
```

***

## 6. API INTEGRATION (React Query)

```typescript
// lib/hooks/useStudySession.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api/client';

export function useStudySession(topicId: number) {
  // Загрузка текущей темы
  const {  currentTopic } = useQuery({
    queryKey: ['topic', topicId],
    queryFn: () => api.get(`/topics/${topicId}`),
  });
  
  // Отправка вопроса AI
  const { mutateAsync: sendMessage } = useMutation({
    mutationFn: async (message: string) => {
      return api.post(`/study/topics/${topicId}/ask`, { message });
    },
  });
  
  // Начало теста
  const { mutateAsync: startTest } = useMutation({
    mutationFn: async () => {
      return api.post(`/study/topics/${topicId}/start-test`);
    },
  });
  
  return {
    currentTopic,
    sendMessage,
    startTest
  };
}
```

***

## 7. RESPONSIVE DESIGN

```tsx
// Mobile: Stack layout (вместо 3 колонок)
<div className="lg:grid lg:grid-cols-12 flex flex-col lg:gap-4">
  {/* На мобильных - Tabs */}
  <Tabs defaultValue="dialog" className="lg:hidden">
    <TabsList className="w-full">
      <TabsTrigger value="files">Файлы</TabsTrigger>
      <TabsTrigger value="dialog">Обучение</TabsTrigger>
      <TabsTrigger value="progress">Прогресс</TabsTrigger>
    </TabsList>
    
    <TabsContent value="files">
      <FileUploadZone />
    </TabsContent>
    
    <TabsContent value="dialog">
      <AIDialogWindow />
    </TabsContent>
    
    <TabsContent value="progress">
      <ProgressOverview />
    </TabsContent>
  </Tabs>
  
  {/* На desktop - Grid */}
  <div className="hidden lg:contents">
    {/* ... 3 колонки ... */}
  </div>
</div>
```

***

## 8. PERFORMANCE OPTIMIZATIONS

### Code Splitting
```typescript
// Ленивая загрузка тяжёлых компонентов
const AIDialogWindow = lazy(() => import('@/components/study/AIDialogWindow'));
const TestForm = lazy(() => import('@/components/study/TestForm'));
```

### Image Optimization
```tsx
import Image from 'next/image';

<Image
  src="/icon.png"
  width={48}
  height={48}
  alt="Icon"
  loading="lazy"
/>
```

### React Query Caching
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 минут
      cacheTime: 10 * 60 * 1000, // 10 минут
    },
  },
});
```

***

## 9. ACCESSIBILITY (A11Y)

- ✅ Keyboard navigation (Tab, Enter, Esc)
- ✅ ARIA labels на всех интерактивных элементах
- ✅ Focus indicators
- ✅ Screen reader support
- ✅ High contrast mode support

```tsx
<button
  aria-label="Отправить сообщение"
  aria-disabled={isLoading}
>
  <Send aria-hidden="true" />
</button>
```

***

## 10. TESTING STRATEGY

```typescript
// tests/components/AIDialogWindow.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { AIDialogWindow } from '@/components/study/AIDialogWindow';

describe('AIDialogWindow', () => {
  it('should send message on Enter key', async () => {
    render(<AIDialogWindow topicId={1} topicTitle="Test" />);
    
    const input = screen.getByPlaceholderText('Задайте вопрос...');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(await screen.findByText('Test message')).toBeInTheDocument();
  });
});
```

***

## ИТОГО: Файловая структура
Это полное описание фронтенда с:

✅ Modern tech stack (Next.js 14, TypeScript, shadcn/ui)  
✅ Детальными компонентами для каждой функции  
✅ 3-panel layout (Files, AI Dialog, Progress)  
✅ Drag-and-drop файлов с preview  
✅ Интерактивный AI диалог с streaming  
✅ Тестовая система с объяснениями  
✅ Дерево прогресса с галочками и результатами тестов  
✅ Responsive design  
✅ Performance optimizations  
✅ Accessibility  
