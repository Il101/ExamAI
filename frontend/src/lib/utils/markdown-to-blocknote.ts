import { Block } from '@blocknote/core';

/**
 * Converts Markdown string to BlockNote JSON format
 * Preserves pedagogical structure and formatting including bold, italic, code
 */
export async function markdownToBlockNote(markdown: string): Promise<Block[]> {
    if (!markdown || markdown.trim() === '') {
        return [];
    }

    try {
        const lines = markdown.split('\n');
        const blocks: any[] = [];
        let codeBlock: string[] = [];
        let inCodeBlock = false;
        let codeLanguage = 'plaintext';

        for (const line of lines) {
            // Code block detection
            if (line.trim().startsWith('```')) {
                if (!inCodeBlock) {
                    inCodeBlock = true;
                    codeBlock = [];
                    codeLanguage = line.trim().slice(3).trim() || 'plaintext';
                } else {
                    inCodeBlock = false;
                    blocks.push({
                        type: 'codeBlock',
                        props: { language: codeLanguage },
                        content: [{ type: 'text', text: codeBlock.join('\n'), styles: {} }],
                    });
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
                    content: parseInlineFormatting(headingMatch[2]),
                });
                continue;
            }

            // List item detection
            const listMatch = line.match(/^[-*]\s+(.+)/);
            if (listMatch) {
                blocks.push({
                    type: 'bulletListItem',
                    content: parseInlineFormatting(listMatch[1]),
                });
                continue;
            }

            const numberedListMatch = line.match(/^\d+\.\s+(.+)/);
            if (numberedListMatch) {
                blocks.push({
                    type: 'numberedListItem',
                    content: parseInlineFormatting(numberedListMatch[1]),
                });
                continue;
            }

            // Horizontal rule
            if (line.trim() === '---' || line.trim() === '***') {
                blocks.push({
                    type: 'paragraph',
                    content: [{ type: 'text', text: '---', styles: {} }],
                });
                continue;
            }

            // Empty line - skip
            if (line.trim() === '') {
                continue;
            }

            // Default: paragraph with inline formatting
            blocks.push({
                type: 'paragraph',
                content: parseInlineFormatting(line),
            });
        }

        return blocks.length > 0 ? blocks : [];
    } catch (error) {
        console.error('Error converting markdown to BlockNote:', error);
        return [];
    }
}

/**
 * Parse inline formatting (bold, italic, code, strikethrough)
 */
function parseInlineFormatting(text: string): any[] {
    const content: any[] = [];
    let currentText = '';
    let i = 0;

    while (i < text.length) {
        // Bold with ** or __
        if ((text[i] === '*' && text[i + 1] === '*') || (text[i] === '_' && text[i + 1] === '_')) {
            if (currentText) {
                content.push({ type: 'text', text: currentText, styles: {} });
                currentText = '';
            }

            const delimiter = text.slice(i, i + 2);
            i += 2;
            let boldText = '';
            let foundEnd = false;

            while (i < text.length - 1) {
                if (text.slice(i, i + 2) === delimiter) {
                    foundEnd = true;
                    i += 2;
                    break;
                }
                boldText += text[i];
                i++;
            }

            if (foundEnd && boldText) {
                content.push({ type: 'text', text: boldText, styles: { bold: true } });
            } else {
                currentText += delimiter + boldText;
            }
            continue;
        }

        // Italic with * or _
        if (text[i] === '*' || text[i] === '_') {
            if (currentText) {
                content.push({ type: 'text', text: currentText, styles: {} });
                currentText = '';
            }

            const delimiter = text[i];
            i++;
            let italicText = '';
            let foundEnd = false;

            while (i < text.length) {
                if (text[i] === delimiter && (i === text.length - 1 || text[i + 1] !== delimiter)) {
                    foundEnd = true;
                    i++;
                    break;
                }
                italicText += text[i];
                i++;
            }

            if (foundEnd && italicText) {
                content.push({ type: 'text', text: italicText, styles: { italic: true } });
            } else {
                currentText += delimiter + italicText;
            }
            continue;
        }

        // Inline code with `
        if (text[i] === '`') {
            if (currentText) {
                content.push({ type: 'text', text: currentText, styles: {} });
                currentText = '';
            }

            i++;
            let codeText = '';
            let foundEnd = false;

            while (i < text.length) {
                if (text[i] === '`') {
                    foundEnd = true;
                    i++;
                    break;
                }
                codeText += text[i];
                i++;
            }

            if (foundEnd) {
                content.push({ type: 'text', text: codeText, styles: { code: true } });
            } else {
                currentText += '`' + codeText;
            }
            continue;
        }

        // Strikethrough with ~~
        if (text[i] === '~' && text[i + 1] === '~') {
            if (currentText) {
                content.push({ type: 'text', text: currentText, styles: {} });
                currentText = '';
            }

            i += 2;
            let strikeText = '';
            let foundEnd = false;

            while (i < text.length - 1) {
                if (text[i] === '~' && text[i + 1] === '~') {
                    foundEnd = true;
                    i += 2;
                    break;
                }
                strikeText += text[i];
                i++;
            }

            if (foundEnd && strikeText) {
                content.push({ type: 'text', text: strikeText, styles: { strikethrough: true } });
            } else {
                currentText += '~~' + strikeText;
            }
            continue;
        }

        // Regular character
        currentText += text[i];
        i++;
    }

    // Add remaining text
    if (currentText) {
        content.push({ type: 'text', text: currentText, styles: {} });
    }

    return content.length > 0 ? content : [{ type: 'text', text: '', styles: {} }];
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
    // Skip MCQ blocks when converting to Markdown
    if (block.type === 'mcq') {
        return '';
    }

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
 * Extract text content from inline content array with formatting
 */
function extractTextContent(content: any[]): string {
    if (!Array.isArray(content)) return '';

    return content
        .map((item) => {
            if (item.type === 'text') {
                let text = item.text || '';
                const styles = item.styles || {};

                // Apply formatting in correct order
                if (styles.code) return `\`${text}\``;
                if (styles.bold && styles.italic) return `***${text}***`;
                if (styles.bold) return `**${text}**`;
                if (styles.italic) return `*${text}*`;
                if (styles.strikethrough) return `~~${text}~~`;

                return text;
            }
            return '';
        })
        .join('');
}
