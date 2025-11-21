'use client';

import { useAuth } from '@/lib/hooks/use-auth';
import { useAnalytics } from '@/lib/hooks/use-analytics';
import { useExams } from '@/lib/hooks/use-exams';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BookOpen, Brain, TrendingUp, Clock, Plus, BarChart3 } from 'lucide-react';
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
      {/* Welcome Section with Progress */}
      <div className="grid gap-6 md:grid-cols-2 items-start">
        <div className="flex flex-col">
          <h1 className="text-3xl font-bold text-foreground">
            Welcome back, {user?.full_name?.split(' ')[0] || 'there'}!
          </h1>
          <p className="mt-2 text-muted-foreground">
            Here&apos;s what&apos;s happening with your studies today.
          </p>
        </div>

        {/* Study Progress - moved to right side of welcome */}
        <Card className="p-4 border-border bg-card/50 backdrop-blur-xl">
          <h2 className="text-base font-semibold mb-3 text-foreground">Study Progress</h2>
          {isLoadingStats ? (
            <div className="animate-pulse space-y-2">
              <div className="h-3 bg-muted rounded" />
              <div className="h-2 bg-muted rounded w-4/5" />
            </div>
          ) : (
            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-muted-foreground">Longest Streak</span>
                  <span className="font-medium text-foreground">{stats?.longest_streak || 0} days</span>
                </div>
                <div className="w-full bg-muted rounded-full h-1.5">
                  <div
                    className="bg-primary h-1.5 rounded-full transition-all"
                    style={{
                      width: `${Math.min(100, ((stats?.current_streak || 0) / (stats?.longest_streak || 1)) * 100)}%`
                    }}
                  />
                </div>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card className="p-6 border-border bg-card/50 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Exams</p>
              <p className="text-3xl font-bold text-foreground">
                {isLoadingExams ? '...' : exams?.length || 0}
              </p>
            </div>
            <div className="h-12 w-12 rounded-full bg-blue-500/20 flex items-center justify-center">
              <BookOpen className="h-6 w-6 text-blue-400" />
            </div>
          </div>
        </Card>

        <Card className="p-6 border-border bg-card/50 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Cards Learned</p>
              <p className="text-3xl font-bold text-foreground">
                {isLoadingStats ? '...' : stats?.total_cards_learned || 0}
              </p>
            </div>
            <div className="h-12 w-12 rounded-full bg-green-500/20 flex items-center justify-center">
              <Brain className="h-6 w-6 text-green-400" />
            </div>
          </div>
        </Card>

        <Card className="p-6 border-border bg-card/50 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Current Streak</p>
              <p className="text-3xl font-bold text-foreground">
                {isLoadingStats ? '...' : stats?.current_streak || 0}
              </p>
              <p className="text-xs text-muted-foreground mt-1">days</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-orange-500/20 flex items-center justify-center">
              <TrendingUp className="h-6 w-6 text-orange-400" />
            </div>
          </div>
        </Card>

        <Card className="p-6 border-border bg-card/50 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Study Time</p>
              <p className="text-3xl font-bold text-foreground">
                {isLoadingStats ? '...' : stats?.total_minutes_studied || 0}
              </p>
              <p className="text-xs text-muted-foreground mt-1">minutes</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-purple-500/20 flex items-center justify-center">
              <Clock className="h-6 w-6 text-purple-400" />
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions - Key Feature */}
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-6">Quick Actions</h2>
        <div className="grid gap-6 md:grid-cols-3">
          <Link href="/dashboard/exams/new">
            <Card className="p-8 border-border bg-gradient-to-br from-blue-500/10 to-blue-600/5 backdrop-blur-xl hover:from-blue-500/20 hover:to-blue-600/10 transition-all duration-300 cursor-pointer group hover:shadow-lg hover:shadow-blue-500/20 hover:scale-[1.02]">
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="h-16 w-16 rounded-full bg-blue-500/20 flex items-center justify-center group-hover:bg-blue-500/30 transition-colors">
                  <BookOpen className="h-8 w-8 text-blue-400 group-hover:text-blue-300" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">Create New Exam</h3>
                  <p className="text-sm text-muted-foreground">
                    Create and organize your study materials
                  </p>
                </div>
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/study">
            <Card className="p-8 border-border bg-gradient-to-br from-green-500/10 to-green-600/5 backdrop-blur-xl hover:from-green-500/20 hover:to-green-600/10 transition-all duration-300 cursor-pointer group hover:shadow-lg hover:shadow-green-500/20 hover:scale-[1.02]">
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="h-16 w-16 rounded-full bg-green-500/20 flex items-center justify-center group-hover:bg-green-500/30 transition-colors">
                  <Brain className="h-8 w-8 text-green-400 group-hover:text-green-300" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">Start Study Session</h3>
                  <p className="text-sm text-muted-foreground">
                    Begin learning with spaced repetition
                  </p>
                </div>
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/analytics">
            <Card className="p-8 border-border bg-gradient-to-br from-purple-500/10 to-purple-600/5 backdrop-blur-xl hover:from-purple-500/20 hover:to-purple-600/10 transition-all duration-300 cursor-pointer group hover:shadow-lg hover:shadow-purple-500/20 hover:scale-[1.02]">
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="h-16 w-16 rounded-full bg-purple-500/20 flex items-center justify-center group-hover:bg-purple-500/30 transition-colors">
                  <BarChart3 className="h-8 w-8 text-purple-400 group-hover:text-purple-300" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">View Analytics</h3>
                  <p className="text-sm text-muted-foreground">
                    Track your progress and performance
                  </p>
                </div>
              </div>
            </Card>
          </Link>
        </div>
      </div>

      {/* Recent Exams */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-foreground">Recent Exams</h2>
          <Link href="/dashboard/exams">
            <Button variant="outline" className="border-white/10 hover:bg-white/5">View All</Button>
          </Link>
        </div>

        {isLoadingExams ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="p-6 animate-pulse border-white/10 bg-card/50">
                <div className="h-6 bg-white/10 rounded mb-4" />
                <div className="h-4 bg-white/10 rounded w-2/3" />
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
          <Card className="p-12 text-center border-white/10 bg-card/50 backdrop-blur-xl">
            <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              No exams yet
            </h3>
            <p className="text-muted-foreground mb-6">
              Get started by creating your first exam
            </p>
            <Link href="/dashboard/exams/new">
              <Button variant="glow">
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
