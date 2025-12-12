'use client';

import { useEffect, useMemo, useState } from 'react';
import { useCreateBlockNote } from '@blocknote/react';
import { BlockNoteView } from '@blocknote/shadcn';
import { BlockNoteSchema, defaultBlockSpecs, Block } from '@blocknote/core';
import { MCQBlock } from './mcq-block';
import { useTheme } from 'next-themes';
import '@blocknote/shadcn/style.css';
import '@blocknote/core/fonts/inter.css';

interface BlockNoteEditorProps {
    topicId: string;
    initialContent: Block[];
    editable?: boolean;
    onChange?: (blocks: Block[]) => void;
    onSave?: (blocks: Block[]) => Promise<void>;
}

/**
 * BlockNote editor wrapper component
 * Supports both read-only and editable modes
 */
export function BlockNoteEditor({
    topicId,
    initialContent,
    editable = false,
    onChange,
    onSave,
}: BlockNoteEditorProps) {
    const { theme } = useTheme();
    const [isSaving, setIsSaving] = useState(false);

    // Create custom schema with MCQ block
    const schema = BlockNoteSchema.create({
        blockSpecs: {
            ...defaultBlockSpecs,
            mcq: MCQBlock(),  // Call the function to get the BlockSpec
        },
    });

    // Create editor instance
    const editor = useCreateBlockNote({
        schema,
        initialContent: initialContent.length > 0 ? initialContent : undefined,
    });

    // Handle content changes with debounce
    useEffect(() => {
        if (!editable || !onChange) return;

        let timeoutId: NodeJS.Timeout;

        const handleChange = () => {
            const blocks = editor.document;
            timeoutId = setTimeout(() => {
                onChange(blocks as Block[]);
            }, 500); // Debounce 500ms
        };

        // Listen to editor changes
        const unsubscribe = editor.onChange(handleChange);

        return () => {
            clearTimeout(timeoutId);
            unsubscribe();
        };
    }, [editor, editable, onChange]);

    // Auto-save effect
    useEffect(() => {
        if (!editable || !onSave) return;

        const autoSaveInterval = setInterval(async () => {
            const blocks = editor.document as Block[];
            if (blocks.length > 0 && !isSaving) {
                try {
                    setIsSaving(true);
                    await onSave(blocks);
                } catch (error) {
                    console.error('Auto-save failed:', error);
                } finally {
                    setIsSaving(false);
                }
            }
        }, 30000); // Auto-save every 30 seconds

        return () => clearInterval(autoSaveInterval);
    }, [editor, editable, onSave, isSaving]);

    return (
        <div className="blocknote-wrapper">
            <style jsx global>{`
                /* Dark theme support for BlockNote */
                .blocknote-wrapper .bn-container[data-theme="dark"] {
                    --bn-colors-editor-background: hsl(var(--background));
                    --bn-colors-editor-text: hsl(var(--foreground));
                    --bn-colors-menu-background: hsl(var(--popover));
                    --bn-colors-menu-text: hsl(var(--popover-foreground));
                    --bn-colors-tooltip-background: hsl(var(--popover));
                    --bn-colors-tooltip-text: hsl(var(--popover-foreground));
                    --bn-colors-hovered-background: hsl(var(--accent));
                    --bn-colors-hovered-text: hsl(var(--accent-foreground));
                    --bn-colors-selected-background: hsl(var(--accent));
                    --bn-colors-selected-text: hsl(var(--accent-foreground));
                    --bn-colors-disabled-background: hsl(var(--muted));
                    --bn-colors-disabled-text: hsl(var(--muted-foreground));
                    --bn-colors-shadow: hsl(var(--border));
                    --bn-colors-border: hsl(var(--border));
                    --bn-colors-side-menu: hsl(var(--muted-foreground));
                    --bn-colors-highlights-gray-background: hsl(var(--muted));
                    --bn-colors-highlights-gray-text: hsl(var(--muted-foreground));
                    --bn-colors-highlights-brown-background: hsl(30 60% 50% / 0.2);
                    --bn-colors-highlights-brown-text: hsl(30 60% 70%);
                    --bn-colors-highlights-red-background: hsl(0 70% 50% / 0.2);
                    --bn-colors-highlights-red-text: hsl(0 70% 70%);
                    --bn-colors-highlights-orange-background: hsl(25 80% 50% / 0.2);
                    --bn-colors-highlights-orange-text: hsl(25 80% 70%);
                    --bn-colors-highlights-yellow-background: hsl(50 80% 50% / 0.2);
                    --bn-colors-highlights-yellow-text: hsl(50 80% 70%);
                    --bn-colors-highlights-green-background: hsl(120 50% 50% / 0.2);
                    --bn-colors-highlights-green-text: hsl(120 50% 70%);
                    --bn-colors-highlights-blue-background: hsl(210 70% 50% / 0.2);
                    --bn-colors-highlights-blue-text: hsl(210 70% 70%);
                    --bn-colors-highlights-purple-background: hsl(270 60% 50% / 0.2);
                    --bn-colors-highlights-purple-text: hsl(270 60% 70%);
                    --bn-colors-highlights-pink-background: hsl(330 70% 50% / 0.2);
                    --bn-colors-highlights-pink-text: hsl(330 70% 70%);
                }

                /* Light theme support */
                .blocknote-wrapper .bn-container[data-theme="light"] {
                    --bn-colors-editor-background: hsl(var(--background));
                    --bn-colors-editor-text: hsl(var(--foreground));
                    --bn-colors-menu-background: hsl(var(--popover));
                    --bn-colors-menu-text: hsl(var(--popover-foreground));
                }

                /* Improve typography */
                .blocknote-wrapper .bn-block-content {
                    line-height: 1.8;
                    font-size: 1rem;
                }

                /* Mobile-optimized text size for better readability */
                @media (max-width: 640px) {
                    .blocknote-wrapper .bn-block-content {
                        font-size: 1.0625rem;
                        line-height: 1.75;
                    }
                    
                    .blocknote-wrapper .bn-editor {
                        padding-left: 0.25rem;
                        padding-right: 0.25rem;
                    }
                    
                    /* Remove BlockNote side handles on mobile to save space */
                    .blocknote-wrapper .bn-side-menu {
                        display: none;
                    }
                }

                .blocknote-wrapper .bn-block-content h1 {
                    font-size: 1.75em;
                    font-weight: 700;
                    margin-top: 1em;
                    margin-bottom: 0.5em;
                }

                @media (min-width: 640px) {
                    .blocknote-wrapper .bn-block-content h1 {
                        font-size: 2em;
                    }
                }

                .blocknote-wrapper .bn-block-content h2 {
                    font-size: 1.35em;
                    font-weight: 600;
                    margin-top: 0.8em;
                    margin-bottom: 0.4em;
                }

                @media (min-width: 640px) {
                    .blocknote-wrapper .bn-block-content h2 {
                        font-size: 1.5em;
                    }
                }

                .blocknote-wrapper .bn-block-content h3 {
                    font-size: 1.15em;
                    font-weight: 600;
                    margin-top: 0.6em;
                    margin-bottom: 0.3em;
                }

                @media (min-width: 640px) {
                    .blocknote-wrapper .bn-block-content h3 {
                        font-size: 1.25em;
                    }
                }

                .blocknote-wrapper .bn-block-content code {
                    background: hsl(var(--muted));
                    padding: 0.2em 0.4em;
                    border-radius: 0.25rem;
                    font-size: 0.85em;
                    word-break: break-word;
                }

                .blocknote-wrapper .bn-block-content pre {
                    background: hsl(var(--muted));
                    border: 1px solid hsl(var(--border));
                    border-radius: 0.5rem;
                    padding: 0.75em;
                    overflow-x: auto;
                    font-size: 0.875em;
                }

                @media (min-width: 640px) {
                    .blocknote-wrapper .bn-block-content pre {
                        padding: 1em;
                    }
                }

                /* Better list styling for mobile */
                .blocknote-wrapper .bn-block-content ul,
                .blocknote-wrapper .bn-block-content ol {
                    padding-left: 1.25em;
                }

                @media (min-width: 640px) {
                    .blocknote-wrapper .bn-block-content ul,
                    .blocknote-wrapper .bn-block-content ol {
                        padding-left: 1.5em;
                    }
                }

                /* Improve paragraph spacing for readability */
                .blocknote-wrapper .bn-block-outer {
                    margin-bottom: 0.25em;
                }
            `}</style>
            <BlockNoteView
                editor={editor}
                editable={editable}
                theme={theme === 'dark' ? 'dark' : 'light'}
            />
            {isSaving && (
                <div className="text-xs text-muted-foreground mt-2">
                    Saving...
                </div>
            )}
        </div>
    );
}
