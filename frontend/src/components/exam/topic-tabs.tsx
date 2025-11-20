'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TopicContent } from './topic-content';

interface Topic {
    id: string;
    title: string;
    notes: string;
    order: number;
}

interface TopicTabsProps {
    topics: Topic[];
}

export function TopicTabs({ topics }: TopicTabsProps) {
    if (topics.length === 0) {
        return (
            <div className="text-center py-12 text-muted-foreground">
                <p>No topics available yet.</p>
                <p className="text-sm mt-2">Topics will appear here once the exam is generated.</p>
            </div>
        );
    }

    return (
        <Tabs defaultValue={topics[0]?.id} className="w-full">
            <TabsList className="w-full justify-start overflow-x-auto flex-wrap h-auto">
                {topics.map((topic, index) => (
                    <TabsTrigger
                        key={topic.id}
                        value={topic.id}
                        className="whitespace-nowrap"
                    >
                        {index + 1}. {topic.title}
                    </TabsTrigger>
                ))}
            </TabsList>

            {topics.map((topic) => (
                <TabsContent key={topic.id} value={topic.id}>
                    <TopicContent title={topic.title} notes={topic.notes} />
                </TabsContent>
            ))}
        </Tabs>
    );
}
