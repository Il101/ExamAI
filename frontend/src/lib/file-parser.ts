import * as pdfjsLib from 'pdfjs-dist';
import mammoth from 'mammoth';

// Set worker source for PDF.js
// Note: This needs to match the version installed.
// In Next.js, we might need to copy the worker to public or use a CDN.
// For simplicity, we'll try using a CDN for the worker to avoid build config complexity in this MVP.
// If that fails, we might need to configure webpack.
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const MAX_PAGES = 500;

export async function parseFile(
    file: File,
    onProgress?: (progress: number) => void
): Promise<string> {
    if (file.size > MAX_FILE_SIZE) {
        throw new Error(`File size exceeds limit of 50MB`);
    }

    const fileType = file.type;
    const fileName = file.name.toLowerCase();

    if (fileType === 'application/pdf' || fileName.endsWith('.pdf')) {
        return parsePDF(file, onProgress);
    } else if (
        fileType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
        fileName.endsWith('.docx')
    ) {
        onProgress?.(50);
        const text = await parseDOCX(file);
        onProgress?.(100);
        return text;
    } else if (fileType === 'text/plain' || fileName.endsWith('.txt')) {
        onProgress?.(50);
        const text = await parseText(file);
        onProgress?.(100);
        return text;
    } else {
        throw new Error(`Unsupported file type: ${fileType}`);
    }
}

async function parseText(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsText(file);
    });
}

async function parsePDF(file: File, onProgress?: (progress: number) => void): Promise<string> {
    try {
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

        if (pdf.numPages > MAX_PAGES) {
            throw new Error(`PDF exceeds page limit of ${MAX_PAGES} pages`);
        }

        let fullText = '';

        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const textContent = await page.getTextContent();
            const pageText = textContent.items
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                .map((item: any) => item.str)
                .join(' ');
            fullText += pageText + '\n\n';

            if (onProgress) {
                onProgress(Math.round((i / pdf.numPages) * 100));
            }
        }

        return fullText;
    } catch (error) {
        console.error('Error parsing PDF:', error);
        if (error instanceof Error) throw error;
        throw new Error('Failed to parse PDF file');
    }
}

async function parseDOCX(file: File): Promise<string> {
    try {
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        return result.value;
    } catch (error) {
        console.error('Error parsing DOCX:', error);
        throw new Error('Failed to parse DOCX file');
    }
}
