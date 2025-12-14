'use client';

import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { useAuth } from '@/lib/hooks/use-auth';
import Link from 'next/link';

const registerSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'Password must include any non-alphanumeric character (e.g. !@#$%^&*()-_=+)'),
  confirmPassword: z.string(),
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type RegisterFormData = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const { register: registerUser, isRegistering } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const passwordValue = form.watch('password', '');
  const passwordChecklist = [
    { label: 'At least 8 characters', valid: passwordValue.length >= 8 },
    { label: 'Uppercase letter', valid: /[A-Z]/.test(passwordValue) },
    { label: 'Lowercase letter', valid: /[a-z]/.test(passwordValue) },
    { label: 'Number', valid: /[0-9]/.test(passwordValue) },
    { label: 'Any symbol (e.g. !@#$%^&*()-_=+)', valid: /[^A-Za-z0-9]/.test(passwordValue) },
  ];

  const onSubmit = (data: RegisterFormData) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { confirmPassword: _, ...registerData } = data;
    setServerError(null);
    registerUser(registerData).catch((error: unknown) => {
      const message = error instanceof Error && 'response' in error
        ? (error as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
        : 'Registration failed';
      setServerError(message || 'Registration failed');
    });
  };

  return (
    <Card className="w-full p-8 shadow-2xl border-white/10 bg-card/50 backdrop-blur-xl">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold mb-2 text-foreground">Create account</h1>
        <p className="text-muted-foreground">Start your learning journey with ExamAI Pro</p>
      </div>

      {serverError && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <p className="font-medium">{serverError}</p>
          {serverError.toLowerCase().includes('already registered') && (
            <div className="mt-2 flex gap-2">
              <Link href="/login" className="text-primary hover:underline">Go to login</Link>
              <span className="text-gray-400">•</span>
              <Link href="/forgot-password" className="text-primary hover:underline">Reset password</Link>
            </div>
          )}
        </div>
      )}

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="full_name">Full Name</Label>
          <Input
            id="full_name"
            type="text"
            placeholder="John Doe"
            {...form.register('full_name')}
            disabled={isRegistering}
          />
          {form.formState.errors.full_name && (
            <p className="text-sm text-red-500 mt-1">
              {form.formState.errors.full_name.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            {...form.register('email')}
            disabled={isRegistering}
          />
          {form.formState.errors.email && (
            <p className="text-sm text-red-500 mt-1">
              {form.formState.errors.email.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            placeholder="••••••••"
            {...form.register('password')}
            disabled={isRegistering}
          />
          {form.formState.errors.password && (
            <p className="text-sm text-red-500 mt-1">
              {form.formState.errors.password.message}
            </p>
          )}
          <div className="mt-2 space-y-1 text-xs text-muted-foreground">
            {passwordChecklist.map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <span className={item.valid ? 'text-green-600' : 'text-gray-400'}>
                  {item.valid ? '✓' : '•'}
                </span>
                <span className={item.valid ? 'text-green-700' : undefined}>{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label htmlFor="confirmPassword">Confirm Password</Label>
          <Input
            id="confirmPassword"
            type="password"
            placeholder="••••••••"
            {...form.register('confirmPassword')}
            disabled={isRegistering}
          />
          {form.formState.errors.confirmPassword && (
            <p className="text-sm text-red-500 mt-1">
              {form.formState.errors.confirmPassword.message}
            </p>
          )}
        </div>

        <Button
          type="submit"
          className="w-full"
          variant="glow"
          disabled={isRegistering}
        >
          {isRegistering ? 'Creating account...' : 'Create account'}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground mt-6">
        Already have an account?{' '}
        <Link href="/login" className="text-primary hover:text-accent hover:underline font-medium transition-colors">
          Sign in
        </Link>
      </p>
    </Card>
  );
}
