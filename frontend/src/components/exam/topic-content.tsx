'use client';

import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AiTutorChat } from './ai-tutor-chat';
import { CodeBlock } from './code-block';
import { TableOfContents } from './table-of-contents';

interface TopicContentProps {
    topicId: string;
    title: string;
    notes: string;
}

export function TopicContent({ topicId, title, notes }: TopicContentProps) {
    // Generate heading IDs for TOC navigation
    let headingIndex = 0;

    return (
        <div className="py-6">
            <h1 className="text-3xl font-bold mb-8">{title}</h1>

            <div className="grid grid-cols-1 lg:grid-cols-[1fr_250px] gap-8">
                {/* Main Content */}
                <div className="prose prose-slate dark:prose-invert max-w-none prose-headings:scroll-mt-20">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            // Add IDs to headings for TOC navigation
                            h1: ({ children }) => {
                                const id = `heading-${headingIndex++}`;
                                return <h1 id={id}>{children}</h1>;
                            },
                            h2: ({ children }) => {
                                const id = `heading-${headingIndex++}`;
                                return <h2 id={id}>{children}</h2>;
                            },
                            h3: ({ children }) => {
                                const id = `heading-${headingIndex++}`;
                                return <h3 id={id}>{children}</h3>;
                            },
                            // Code blocks with syntax highlighting and copy button
                            code({ node, inline, className, children, ...props }: any) {
                                const match = /language-(\w+)/.exec(className || '');
                                const code = String(children).replace(/\n$/, '');

                                return !inline && match ? (
                                    <CodeBlock language={match[1]} code={code} />
                                ) : (
                                    <code className={className} {...props}>
                                        {children}
                                    </code>
                                );
                            },
                        }}
                    >
                        {notes}
                    </ReactMarkdown>
                </div>

                {/* Table of Contents - Desktop only */}
                <aside className="hidden lg:block">
                    <TableOfContents content={notes} />
                </aside>
            </div>

            {/* AI Tutor Chat */}
            <div className="mt-12 border-t pt-8">
                <h3 className="text-xl font-semibold mb-4">💬 Ask AI Tutor</h3>
                <AiTutorChat topicId={topicId} />
            </div>
        </div>
    );
}
