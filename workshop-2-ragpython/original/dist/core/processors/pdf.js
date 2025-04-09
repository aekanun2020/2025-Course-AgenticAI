import { DocumentProcessor } from './base';
import { ProcessingError } from '../../utils/errors';
import * as pdfjsLib from 'pdfjs-dist';
export class PDFProcessor extends DocumentProcessor {
    constructor(...args) {
        super(...args);
        this.pdfjs = pdfjsLib;
    }
    async processContent(content) {
        this.metrics.startOperation('pdf_processing');
        try {
            const pdfData = Buffer.isBuffer(content) ?
                content :
                Buffer.from(content, 'base64');
            const pdf = await this.pdfjs.getDocument({
                data: pdfData,
                useWorkerFetch: false,
                isEvalSupported: false,
                useSystemFonts: true
            }).promise;
            const numPages = pdf.numPages;
            this.logger.info(`Processing PDF with ${numPages} pages`);
            const chunks = [];
            for (let pageNum = 1; pageNum <= numPages; pageNum++) {
                try {
                    this.logger.debug(`Processing page ${pageNum}/${numPages}`);
                    const page = await pdf.getPage(pageNum);
                    const textContent = await page.getTextContent();
                    const text = textContent.items
                        .map(item => 'str' in item ? item.str : '')
                        .join(' ');
                    const textChunks = await this.chunkContent(text);
                    chunks.push(...textChunks.map((chunk, index) => this.createChunk(chunk, {
                        pageNumber: pageNum,
                        chunkIndex: index,
                        totalChunks: textChunks.length
                    })));
                    if (process.memoryUsage().heapUsed > this.options.maxMemoryUsage) {
                        this.logger.debug('Memory threshold reached, triggering GC');
                        global.gc?.();
                    }
                }
                catch (error) {
                    this.logger.error(`Error processing page ${pageNum}:`, error);
                    continue;
                }
            }
            this.metrics.endOperation('pdf_processing');
            return chunks;
        }
        catch (error) {
            this.metrics.endOperation('pdf_processing');
            throw new ProcessingError('Failed to process PDF', { cause: error });
        }
    }
    canProcess(input) {
        return input.mimeType === 'application/pdf';
    }
    extractTitle(input) {
        if (input.path) {
            return input.path.split('/').pop()?.replace(/\.pdf$/i, '') || 'Untitled';
        }
        return 'Untitled PDF Document';
    }
}
