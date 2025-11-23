'use client';

import { BookOpen, CheckCircle2, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface TopicOutlineProps {
    outline: {
        subject: string;
        total_topics: number;
        outline: Array<{
            topic: string;
            subtopics: string[];
        }>;
    };
}

export default function TopicOutline({ outline }: TopicOutlineProps) {
    const [expandedTopics, setExpandedTopics] = useState<Set<number>>(new Set([0]));

    const toggleTopic = (index: number) => {
        const newExpanded = new Set(expandedTopics);
        if (newExpanded.has(index)) {
            newExpanded.delete(index);
        } else {
            newExpanded.add(index);
        }
        setExpandedTopics(newExpanded);
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="text-center space-y-2">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-success/10 backdrop-blur-sm">
                    <CheckCircle2 className="w-5 h-5 text-success" />
                    <span className="text-sm font-medium text-success">Analysis Complete!</span>
                </div>
                <h3 className="text-2xl font-bold text-foreground">
                    {outline.subject}
                </h3>
                <p className="text-sm text-muted-foreground">
                    {outline.total_topics} topics • Ready to learn
                </p>
            </div>

            {/* Topic List */}
            <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                {outline.outline.map((item, index) => {
                    const isExpanded = expandedTopics.has(index);

                    return (
                        <Card
                            key={index}
                            className="border-2 border-border hover:border-primary/50 transition-all duration-300 hover-lift"
                        >
                            <CardContent className="p-4">
                                {/* Topic Header */}
                                <button
                                    onClick={() => toggleTopic(index)}
                                    className="w-full flex items-center gap-3 text-left group"
                                >
                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-brand flex items-center justify-center text-primary-foreground font-bold text-sm shadow-glow">
                                        {index + 1}
                                    </div>

                                    <div className="flex-1">
                                        <h4 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                                            {item.topic}
                                        </h4>
                                        <p className="text-xs text-muted-foreground">
                                            {item.subtopics.length} subtopics
                                        </p>
                                    </div>

                                    <div className="flex-shrink-0">
                                        {isExpanded ? (
                                            <ChevronDown className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                                        ) : (
                                            <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                                        )}
                                    </div>
                                </button>

                                {/* Subtopics */}
                                {isExpanded && (
                                    <div className="mt-4 ml-11 space-y-2 animate-fade-in">
                                        {item.subtopics.map((subtopic, subIndex) => (
                                            <div
                                                key={subIndex}
                                                className="flex items-start gap-2 text-sm"
                                            >
                                                <BookOpen className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                                                <span className="text-muted-foreground">{subtopic}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    );
                })}
            </div>
        </div>
    );
}
