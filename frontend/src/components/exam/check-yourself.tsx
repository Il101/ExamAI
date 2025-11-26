'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, XCircle, Loader2, AlertCircle, ChevronRight, SkipForward } from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuizOption {
    id: number;
    text: string;
    is_correct: boolean;
}

interface QuizQuestion {
    id: number;
    question: string;
    options: QuizOption[];
    explanation: string;
}

interface QuizData {
    topic_id: string;
    topic_name: string;
    questions: QuizQuestion[];
}

interface CheckYourselfProps {
    topicId: string;
    onComplete: (score: number, total: number) => void;
    onSkip?: () => void;
}

export function CheckYourself({ topicId, onComplete, onSkip }: CheckYourselfProps) {
    const [quizData, setQuizData] = useState<QuizData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [selectedOption, setSelectedOption] = useState<number | null>(null);
    const [isAnswered, setIsAnswered] = useState(false);
    const [answers, setAnswers] = useState<boolean[]>([]);
    const [showResults, setShowResults] = useState(false);

    useEffect(() => {
        loadQuiz();
    }, [topicId]);

    const loadQuiz = async () => {
        try {
            setIsLoading(true);
            setError(null);

            const response = await fetch(`/api/topics/${topicId}/quiz?num_questions=5`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to load quiz');
            }

            const data = await response.json();
            setQuizData(data);
        } catch (err) {
            console.error('Failed to load quiz:', err);
            setError('Failed to load quiz. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleOptionSelect = (optionId: number) => {
        if (isAnswered) return;
        setSelectedOption(optionId);
    };

    const handleSubmitAnswer = () => {
        if (selectedOption === null || !quizData) return;

        const currentQuestion = quizData.questions[currentQuestionIndex];
        const selectedOptionData = currentQuestion.options[selectedOption];
        const isCorrect = selectedOptionData.is_correct;

        setIsAnswered(true);
        setAnswers([...answers, isCorrect]);
    };

    const handleNextQuestion = () => {
        if (!quizData) return;

        if (currentQuestionIndex < quizData.questions.length - 1) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
            setSelectedOption(null);
            setIsAnswered(false);
        } else {
            // Quiz complete
            setShowResults(true);
            const score = answers.filter(a => a).length;
            onComplete(score, quizData.questions.length);
        }
    };

    const handleSkip = () => {
        if (onSkip) {
            onSkip();
        }
    };

    if (isLoading) {
        return (
            <Card className="border-primary/20 bg-primary/5">
                <CardContent className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </CardContent>
            </Card>
        );
    }

    if (error || !quizData) {
        return (
            <Card className="border-destructive/20 bg-destructive/5">
                <CardContent className="py-8 text-center">
                    <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground">{error || 'Quiz not available'}</p>
                </CardContent>
            </Card>
        );
    }

    if (showResults) {
        const score = answers.filter(a => a).length;
        const total = quizData.questions.length;
        const percentage = Math.round((score / total) * 100);

        return (
            <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10">
                <CardHeader>
                    <CardTitle className="text-center">Quiz Complete! 🎉</CardTitle>
                </CardHeader>
                <CardContent className="text-center space-y-4">
                    <div className="text-5xl font-bold text-primary">
                        {score}/{total}
                    </div>
                    <p className="text-lg text-muted-foreground">
                        {percentage >= 80 ? 'Excellent work!' : percentage >= 60 ? 'Good job!' : 'Keep practicing!'}
                    </p>
                    <Progress value={percentage} className="h-2" />
                </CardContent>
            </Card>
        );
    }

    const currentQuestion = quizData.questions[currentQuestionIndex];
    const progress = ((currentQuestionIndex + 1) / quizData.questions.length) * 100;

    return (
        <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-background">
            <CardHeader>
                <div className="flex items-center justify-between mb-2">
                    <Badge variant="secondary">
                        Question {currentQuestionIndex + 1} of {quizData.questions.length}
                    </Badge>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleSkip}
                        className="text-muted-foreground"
                    >
                        <SkipForward className="h-4 w-4 mr-1" />
                        Skip Quiz
                    </Button>
                </div>
                <Progress value={progress} className="h-1 mb-4" />
                <CardTitle className="text-xl">✅ Check Yourself</CardTitle>
                <p className="text-base text-foreground mt-2">{currentQuestion.question}</p>
            </CardHeader>

            <CardContent className="space-y-4">
                {/* Options */}
                <div className="space-y-2">
                    {currentQuestion.options.map((option) => {
                        const isSelected = selectedOption === option.id;
                        const isCorrect = option.is_correct;
                        const showCorrect = isAnswered && isCorrect;
                        const showWrong = isAnswered && isSelected && !isCorrect;

                        return (
                            <button
                                key={option.id}
                                onClick={() => handleOptionSelect(option.id)}
                                disabled={isAnswered}
                                className={cn(
                                    'w-full p-4 text-left rounded-lg border-2 transition-all',
                                    'hover:border-primary/50 hover:bg-accent',
                                    isSelected && !isAnswered && 'border-primary bg-primary/10',
                                    showCorrect && 'border-green-500 bg-green-50 dark:bg-green-950',
                                    showWrong && 'border-red-500 bg-red-50 dark:bg-red-950',
                                    !isSelected && !showCorrect && !showWrong && 'border-border'
                                )}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="flex-1">{option.text}</span>
                                    {showCorrect && <CheckCircle2 className="h-5 w-5 text-green-600" />}
                                    {showWrong && <XCircle className="h-5 w-5 text-red-600" />}
                                </div>
                            </button>
                        );
                    })}
                </div>

                {/* Explanation */}
                {isAnswered && (
                    <div className="p-4 rounded-lg bg-muted border">
                        <p className="text-sm font-medium mb-1">Explanation:</p>
                        <p className="text-sm text-muted-foreground">{currentQuestion.explanation}</p>
                    </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                    {!isAnswered ? (
                        <Button
                            onClick={handleSubmitAnswer}
                            disabled={selectedOption === null}
                            className="w-full"
                            size="lg"
                        >
                            Submit Answer
                        </Button>
                    ) : (
                        <Button
                            onClick={handleNextQuestion}
                            className="w-full"
                            size="lg"
                        >
                            {currentQuestionIndex < quizData.questions.length - 1 ? (
                                <>
                                    Next Question
                                    <ChevronRight className="h-4 w-4 ml-2" />
                                </>
                            ) : (
                                'See Results'
                            )}
                        </Button>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
