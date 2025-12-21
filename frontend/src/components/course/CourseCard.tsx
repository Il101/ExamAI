import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Folder, Book, Brain, Clock, ChevronRight } from 'lucide-react';
import { Course } from '@/lib/api/courses';

interface CourseCardProps {
    course: Course;
    onClick?: (courseId: string) => void;
}

export function CourseCard({ course, onClick }: CourseCardProps) {
    const stats = course.stats || {
        exam_count: 0,
        topic_count: 0,
        completed_topics: 0,
        due_flashcards_count: 0,
        total_actual_study_minutes: 0,
        total_planned_study_minutes: 0,
        average_difficulty: 0,
    };

    const progress = stats.topic_count > 0 ? (stats.completed_topics / stats.topic_count) * 100 : 0;

    const formatMinutes = (mins: number) => {
        if (mins <= 0) return '0m';
        if (mins < 60) return `${mins}m`;
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        return m > 0 ? `${h}h ${m}m` : `${h}h`;
    };

    return (
        <Card
            className="group hover:border-primary/50 transition-all duration-300 overflow-hidden bg-card/50 backdrop-blur-sm border-border/40 cursor-pointer"
            onClick={() => onClick?.(course.id)}
        >
            <CardHeader className="pb-3 px-5 pt-5">
                <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            <Folder className="h-4 w-4 text-primary" />
                            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Course Folder</span>
                        </div>
                        <h3 className="text-lg font-bold text-foreground leading-tight group-hover:text-primary transition-colors line-clamp-1">
                            {course.title}
                        </h3>
                        <p className="text-sm text-muted-foreground mt-0.5 font-medium line-clamp-1">
                            {course.subject}
                        </p>
                    </div>
                    <Badge variant="secondary" className="bg-primary/10 text-primary border-none font-bold px-2.5 py-0.5 shrink-0">
                        {stats.exam_count} {stats.exam_count === 1 ? 'Exam' : 'Exams'}
                    </Badge>
                </div>
            </CardHeader>

            <CardContent className="px-5 pb-5 space-y-5">
                <div className="space-y-4">
                    {/* Progress */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs font-semibold">
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <Book className="h-3.5 w-3.5" />
                                <span>Overall Progress</span>
                            </div>
                            <span className="text-foreground">{stats.completed_topics}/{stats.topic_count}</span>
                        </div>
                        <Progress value={progress} className="h-1.5 bg-muted/30" />
                    </div>

                    <div className="grid grid-cols-2 gap-4 pt-1 border-t border-border/20">
                        {/* Study Time */}
                        <div className="space-y-1.5">
                            <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-tight">
                                <Clock className="h-3 w-3" />
                                <span>Study Time</span>
                            </div>
                            <div className="flex items-baseline gap-1">
                                <span className="text-sm font-bold text-foreground">
                                    {formatMinutes(stats.total_actual_study_minutes)}
                                </span>
                                <span className="text-[10px] text-muted-foreground font-medium">
                                    / {formatMinutes(stats.total_planned_study_minutes)}
                                </span>
                            </div>
                        </div>

                        {/* Due Flashcards */}
                        <div className="space-y-1.5">
                            <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-tight">
                                <Brain className="h-3 w-3" />
                                <span>Review</span>
                            </div>
                            <div>
                                {stats.due_flashcards_count > 0 ? (
                                    <span className="text-sm font-bold text-orange-500">
                                        ⚡ {stats.due_flashcards_count} due
                                    </span>
                                ) : (
                                    <span className="text-sm font-medium text-emerald-500">Ready</span>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Average Difficulty */}
                    <div className="flex items-center justify-between pt-1">
                        <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
                            <Brain className="h-3.5 w-3.5" />
                            <span>Avg. Difficulty</span>
                        </div>
                        <div className="flex gap-1">
                            {[1, 2, 3, 4, 5].map((dot) => {
                                const isActive = dot <= Math.round(stats.average_difficulty);
                                return (
                                    <div
                                        key={dot}
                                        className={`h-1.5 w-1.5 rounded-full transition-colors ${isActive
                                            ? 'bg-primary shadow-[0_0_5px_rgba(var(--primary),0.5)]'
                                            : 'bg-muted/40'
                                            }`}
                                    />
                                );
                            })}
                        </div>
                    </div>
                </div>

                <div className="pt-2 flex items-center justify-between border-t border-border/30">
                    <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider translate-y-0.5">
                        View details
                    </span>
                    <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors group-hover:translate-x-0.5 transition-transform" />
                </div>
            </CardContent>
        </Card>
    );
}
