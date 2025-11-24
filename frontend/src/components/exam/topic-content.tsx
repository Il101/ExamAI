'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AiTutorChat } from './ai-tutor-chat';

interface TopicContentProps {
    topicId: string;
    title: string;
    notes: string;
}

export function TopicContent({ topicId, title, notes }: TopicContentProps) {
    return (
        <div className="py-6">
            <h2 className="text-2xl font-bold mb-6">{title}</h2>

            <div className="prose prose-slate dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {notes}
                </ReactMarkdown>
            </div>

            {/* AI Tutor Chat */}
            <div className="mt-8 border-t pt-6">
                <h3 className="text-lg font-semibold mb-4">💬 Ask AI Tutor</h3>
                <AiTutorChat topicId={topicId} />
            </div>
        </div>
    );
}

