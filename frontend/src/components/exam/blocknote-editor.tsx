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
            <BlockNoteView
                editor={editor}
                editable={editable}
                theme={theme === 'dark' ? 'dark' : 'light'}
                data-theming-css-variables-demo
            />
            {isSaving && (
                <div className="text-xs text-muted-foreground mt-2">
                    Saving...
                </div>
            )}
        </div>
    );
}
