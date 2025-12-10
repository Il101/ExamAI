import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FileText, Trash2, Play } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';
import { Exam } from '@/lib/api/exams';

interface ExamCardProps {
  exam: Exam;
  onDelete?: () => void;
}

export function ExamCard({ exam, onDelete }: ExamCardProps) {
  const statusColors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-800 hover:bg-gray-100',
    generating: 'bg-blue-100 text-blue-800 hover:bg-blue-100',
    ready: 'bg-green-100 text-green-800 hover:bg-green-100',
    failed: 'bg-red-100 text-red-800 hover:bg-red-100',
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg font-semibold">{exam.title}</CardTitle>
            <p className="text-sm text-gray-500 mt-1 line-clamp-1">{exam.description || "No description"}</p>
          </div>
          <Badge className={statusColors[exam.status] || 'bg-gray-100'}>
            {exam.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between mt-4">
          <div className="text-xs text-gray-500">
            <p>Created {formatDistanceToNow(new Date(exam.created_at), { addSuffix: true })}</p>
          </div>
          <div className="flex gap-2">
            {exam.status === 'ready' && (
              <Link href={`/dashboard/exams/${exam.id}`}>
                <Button size="sm" variant="outline">
                  <FileText className="h-3 w-3 mr-1" />
                  View
                </Button>
              </Link>
            )}
            {/* Add support for planned/generating status */}
            {(exam.status === 'planned' || exam.status === 'generating') && (
              <Link href={`/dashboard/exams/${exam.id}`}>
                <Button size="sm" variant="default" className={exam.status === 'generating' ? 'animate-pulse' : ''}>
                  <Play className="h-3 w-3 mr-1" />
                  {exam.status === 'generating' ? 'Generating...' : 'Continue'}
                </Button>
              </Link>
            )}
            {onDelete && (
              <Button size="sm" variant="ghost" className="text-red-500 hover:text-red-600 hover:bg-red-50" onClick={onDelete}>
                <Trash2 className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
