import { Block } from '@blocknote/core';

/**
 * Converts Markdown string to BlockNote JSON format
 * Preserves pedagogical structure and formatting
 * 
 * Note: This is a simplified implementation that converts Markdown to plain blocks.
 * For production use, consider using BlockNote's built-in HTML/Markdown parsers.
 */
export async function markdownToBlockNote(markdown: string): Promise<Block[]> {
    if (!markdown || markdown.trim() === '') {
        return [];
    }

    try {
        // Simple conversion: split by lines and convert to paragraphs
        // Headers, lists, and code blocks will be detected and converted
        const lines = markdown.split('\n');
        const blocks: any[] = [];
        let currentBlock: any = null;
        let codeBlock: string[] = [];
        let inCodeBlock = false;

        for (const line of lines) {
            // Code block detection
            if (line.trim().startsWith('```')) {
                if (!inCodeBlock) {
                    inCodeBlock = true;
                    codeBlock = [];
                    const language = line.trim().slice(3).trim() || 'plaintext';
                    currentBlock = {
                        type: 'codeBlock',
                        props: { language },
                        content: [],
                    };
                } else {
                    inCodeBlock = false;
                    currentBlock.content = [{ type: 'text', text: codeBlock.join('\n'), styles: {} }];
                    blocks.push(currentBlock);
                    currentBlock = null;
                }
                continue;
            }

            if (inCodeBlock) {
                codeBlock.push(line);
                continue;
            }

            // Heading detection
            const headingMatch = line.match(/^(#{1,3})\s+(.+)/);
            if (headingMatch) {
                blocks.push({
                    type: 'heading',
                    props: { level: headingMatch[1].length as 1 | 2 | 3 },
                    content: [{ type: 'text', text: headingMatch[2], styles: {} }],
                });
                continue;
            }

            // List item detection
            const listMatch = line.match(/^[-*]\s+(.+)/);
            if (listMatch) {
                blocks.push({
                    type: 'bulletListItem',
                    content: [{ type: 'text', text: listMatch[1], styles: {} }],
                });
                continue;
            }

            const numberedListMatch = line.match(/^\d+\.\s+(.+)/);
            if (numberedListMatch) {
                blocks.push({
                    type: 'numberedListItem',
                    content: [{ type: 'text', text: numberedListMatch[1], styles: {} }],
                });
                continue;
            }

            // Empty line
            if (line.trim() === '') {
                continue;
            }

            // Default: paragraph
            blocks.push({
                type: 'paragraph',
                content: [{ type: 'text', text: line, styles: {} }],
            });
        }

        return blocks.length > 0 ? blocks : [];
    } catch (error) {
        console.error('Error converting markdown to BlockNote:', error);
        return [];
    }
}

/**
 * Convert BlockNote blocks to Markdown string
 * Used when saving edited content
 */
export function blockNoteToMarkdown(blocks: Block[]): string {
    const lines: string[] = [];

    for (const block of blocks) {
        const line = convertBlockToMarkdown(block);
        if (line) {
            lines.push(line);
        }
    }

    return lines.join('\n\n');
}

/**
 * Convert single block to Markdown
 */
function convertBlockToMarkdown(block: any): string {
    const content = extractTextContent(block.content || []);

    switch (block.type) {
        case 'heading':
            const level = block.props?.level || 1;
            return '#'.repeat(level) + ' ' + content;

        case 'paragraph':
            return content;

        case 'bulletListItem':
            return '- ' + content;

        case 'numberedListItem':
            return '1. ' + content;

        case 'codeBlock':
            const lang = block.props?.language || '';
            return '```' + lang + '\n' + content + '\n```';

        default:
            return content;
    }
}

/**
 * Extract text content from inline content array
 */
function extractTextContent(content: any[]): string {
    if (!Array.isArray(content)) return '';

    return content
        .map((item) => {
            if (item.type === 'text') {
                let text = item.text || '';
                const styles = item.styles || {};

                if (styles.bold) text = `**${text}**`;
                if (styles.italic) text = `*${text}*`;
                if (styles.code) text = `\`${text}\``;
                if (styles.strikethrough) text = `~~${text}~~`;

                return text;
            }
            return '';
        })
        .join('');
}
