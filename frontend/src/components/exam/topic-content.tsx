'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface TopicContentProps {
    title: string;
    notes: string;
}

export function TopicContent({ title, notes }: TopicContentProps) {
    return (
        <div className="py-6">
            <h2 className="text-2xl font-bold mb-6">{title}</h2>

            <div className="prose prose-slate dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {notes}
                </ReactMarkdown>
            </div>
        </div>
    );
}
