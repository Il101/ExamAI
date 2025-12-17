import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Book, Brain, Play, Trash2, GraduationCap } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Exam } from '@/lib/api/exams';

interface ExamCardProps {
  exam: Exam;
  totalTopics?: number;
  completedTopics?: number;
  dueFlashcards?: number;
  onDelete?: () => void;
  onPressReview?: (examId: string) => void;
  onPressLearn?: (examId: string) => void;
}

export function ExamCard({
  exam,
  onDelete,
  totalTopics = 0,
  completedTopics = 0,
  dueFlashcards = 0,
  onPressReview,
  onPressLearn
}: ExamCardProps) {
  const router = useRouter();

  const statusColors: Record<string, string> = {
    draft: 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300',
    generating: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    ready: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  };

  const progress = totalTopics > 0 ? (completedTopics / totalTopics) * 100 : 0;

  return (
    <Card
      className="group hover:border-primary/50 transition-all duration-300 overflow-hidden bg-card/50 backdrop-blur-sm border-border/40"
    >
      <CardHeader className="pb-3 px-5 pt-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-bold text-foreground leading-tight group-hover:text-primary transition-colors line-clamp-1">
              {exam.title}
            </h3>
            {exam.subject && (
              <p className="text-sm text-muted-foreground mt-0.5 font-medium line-clamp-1">
                {exam.subject}
              </p>
            )}
          </div>
          <Badge variant="secondary" className={`${statusColors[exam.status] || ''} border-none font-semibold px-2.5 py-0.5 shrink-0`}>
            {exam.status === 'generating' ? (
              <span className="flex items-center gap-1.5">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                </span>
                Generating
              </span>
            ) : exam.status.charAt(0).toUpperCase() + exam.status.slice(1)}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="px-5 pb-5 space-y-5">
        {/* Stats Section */}
        <div className="space-y-4">
          {/* Topics Progress */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Book className="h-3.5 w-3.5" />
                <span>Topics Progress</span>
              </div>
              <span className="text-foreground">{completedTopics}/{totalTopics}</span>
            </div>
            <Progress value={progress} className="h-1.5 bg-muted/30" />
          </div>

          {/* Flashcards Due */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
              <Brain className="h-3.5 w-3.5" />
              <span>Review Session</span>
            </div>
            {dueFlashcards > 0 ? (
              <Badge variant="outline" className="text-orange-500 border-orange-500/20 bg-orange-500/5 font-bold">
                ⚡ {dueFlashcards} due
              </Badge>
            ) : (
              <span className="text-xs font-medium text-emerald-500">All caught up</span>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 pt-2">
          <Button
            className="flex-1 h-10 font-bold bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm shadow-primary/20"
            disabled={exam.status !== 'ready'}
            onClick={(e) => {
              e.stopPropagation();
              onPressReview?.(exam.id);
            }}
          >
            <Play className="h-4 w-4 mr-2 fill-current" />
            Train {dueFlashcards > 0 ? `(${dueFlashcards})` : ''}
          </Button>

          <Button
            variant="outline"
            className="flex-1 h-10 font-bold border-border/60 hover:border-primary/40 hover:bg-primary/5 text-foreground transition-colors"
            disabled={exam.status !== 'ready'}
            onClick={(e) => {
              e.stopPropagation();
              onPressLearn?.(exam.id);
            }}
          >
            <GraduationCap className="h-4 w-4 mr-2" />
            Learn
          </Button>

          {onDelete && (
            <Button
              size="icon"
              variant="ghost"
              className="h-10 w-10 shrink-0 text-muted-foreground hover:text-red-500 hover:bg-red-500/10"
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Meta Info */}
        <div className="pt-2 flex items-center justify-between border-t border-border/30">
          <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
            Created {formatDistanceToNow(new Date(exam.created_at), { addSuffix: true })}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
