'use client';

import { useAuth } from '@/lib/hooks/use-auth';
import { useAnalytics } from '@/lib/hooks/use-analytics';
import { useExams } from '@/lib/hooks/use-exams';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BookOpen, Brain, TrendingUp, Clock, Plus } from 'lucide-react';
import Link from 'next/link';
import { ExamCard } from '@/components/exam/exam-card';
import type { Exam } from '@/lib/api/exams';

export default function DashboardPage() {
  const { user } = useAuth();
  const { stats, isLoading: isLoadingStats } = useAnalytics();
  const { exams, isLoading: isLoadingExams } = useExams();

  const recentExams = exams?.slice(0, 3) || [];

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.full_name?.split(' ')[0] || 'there'}!
        </h1>
        <p className="mt-2 text-gray-600">
          Here&apos;s what&apos;s happening with your studies today.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Exams</p>
              <p className="text-3xl font-bold text-gray-900">
                {isLoadingExams ? '...' : exams?.length || 0}
              </p>
            </div>
            <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
              <BookOpen className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Cards Learned</p>
              <p className="text-3xl font-bold text-gray-900">
                {isLoadingStats ? '...' : stats?.total_cards_learned || 0}
              </p>
            </div>
            <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
              <Brain className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Current Streak</p>
              <p className="text-3xl font-bold text-gray-900">
                {isLoadingStats ? '...' : stats?.current_streak || 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">days</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-orange-100 flex items-center justify-center">
              <TrendingUp className="h-6 w-6 text-orange-600" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Study Time</p>
              <p className="text-3xl font-bold text-gray-900">
                {isLoadingStats ? '...' : stats?.total_minutes_studied || 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">minutes</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-purple-100 flex items-center justify-center">
              <Clock className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link href="/dashboard/exams/new">
              <Button className="w-full justify-start" variant="outline">
                <Plus className="mr-2 h-4 w-4" />
                Create New Exam
              </Button>
            </Link>
            <Link href="/dashboard/study">
              <Button className="w-full justify-start" variant="outline">
                <Brain className="mr-2 h-4 w-4" />
                Start Study Session
              </Button>
            </Link>
            <Link href="/dashboard/analytics">
              <Button className="w-full justify-start" variant="outline">
                <TrendingUp className="mr-2 h-4 w-4" />
                View Analytics
              </Button>
            </Link>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Study Progress</h2>
          {isLoadingStats ? (
            <div className="animate-pulse space-y-3">
              <div className="h-4 bg-gray-200 rounded" />
              <div className="h-4 bg-gray-200 rounded w-5/6" />
              <div className="h-4 bg-gray-200 rounded w-4/6" />
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Longest Streak</span>
                  <span className="font-medium">{stats?.longest_streak || 0} days</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{
                      width: `${Math.min(100, ((stats?.current_streak || 0) / (stats?.longest_streak || 1)) * 100)}%`
                    }}
                  />
                </div>
              </div>
              <div className="pt-4 border-t">
                <p className="text-sm text-gray-600">
                  Keep up the great work! You&apos;re making excellent progress.
                </p>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Recent Exams */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Recent Exams</h2>
          <Link href="/dashboard/exams">
            <Button variant="outline">View All</Button>
          </Link>
        </div>

        {isLoadingExams ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded mb-4" />
                <div className="h-4 bg-gray-200 rounded w-2/3" />
              </Card>
            ))}
          </div>
        ) : recentExams.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {recentExams.map((exam: Exam) => (
              <ExamCard key={exam.id} exam={exam} />
            ))}
          </div>
        ) : (
          <Card className="p-12 text-center">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No exams yet
            </h3>
            <p className="text-gray-600 mb-6">
              Get started by creating your first exam
            </p>
            <Link href="/dashboard/exams/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Exam
              </Button>
            </Link>
          </Card>
        )}
      </div>
    </div>
  );
}
