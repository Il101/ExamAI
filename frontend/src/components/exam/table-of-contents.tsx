'use client';

import { useEffect, useState } from 'react';

interface TocItem {
    id: string;
    text: string;
    level: number;
}

interface TableOfContentsProps {
    content: string;
}

export function TableOfContents({ content }: TableOfContentsProps) {
    const [headings, setHeadings] = useState<TocItem[]>([]);
    const [activeId, setActiveId] = useState<string>('');

    useEffect(() => {
        // Extract headings from markdown
        const headingRegex = /^(#{1,3})\s+(.+)$/gm;
        const matches = Array.from(content.matchAll(headingRegex));

        const items: TocItem[] = matches.map((match, index) => {
            const level = match[1].length;
            const text = match[2];
            const id = `heading-${index}`;
            return { id, text, level };
        });

        setHeadings(items);
    }, [content]);

    useEffect(() => {
        // Track scroll position to highlight active heading
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setActiveId(entry.target.id);
                    }
                });
            },
            { rootMargin: '-80px 0px -80% 0px' }
        );

        // Observe all headings
        headings.forEach(({ id }) => {
            const element = document.getElementById(id);
            if (element) observer.observe(element);
        });

        return () => observer.disconnect();
    }, [headings]);

    const scrollToHeading = (id: string) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    if (headings.length === 0) return null;

    return (
        <nav className="sticky top-6 space-y-2">
            <h3 className="font-semibold text-sm text-muted-foreground mb-3">
                Table of Contents
            </h3>
            <ul className="space-y-2 text-sm">
                {headings.map(({ id, text, level }) => (
                    <li
                        key={id}
                        style={{ paddingLeft: `${(level - 1) * 0.75}rem` }}
                    >
                        <button
                            onClick={() => scrollToHeading(id)}
                            className={`text-left hover:text-primary transition-colors ${activeId === id
                                    ? 'text-primary font-medium'
                                    : 'text-muted-foreground'
                                }`}
                        >
                            {text}
                        </button>
                    </li>
                ))}
            </ul>
        </nav>
    );
}
