import { DocumentProcessor } from './base';
import { ProcessingError } from '../../utils/errors';
export class TextProcessor extends DocumentProcessor {
    async processContent(content) {
        this.metrics.startOperation('text_processing');
        try {
            const cleanedContent = this.cleanupText(content);
            const textChunks = await this.chunkContent(cleanedContent);
            const chunks = textChunks.map((chunk, index) => this.createChunk(chunk, {
                chunkIndex: index,
                totalChunks: textChunks.length,
                textInfo: {
                    originalSize: content.length,
                    processedSize: cleanedContent.length
                }
            }));
            this.metrics.endOperation('text_processing');
            return chunks;
        }
        catch (error) {
            this.metrics.endOperation('text_processing');
            throw new ProcessingError('Failed to process text', { cause: error });
        }
    }
    canProcess(input) {
        return input.mimeType?.includes('text') || false;
    }
    cleanupText(text) {
        return text
            .replace(/\r\n/g, '\n')
            .replace(/\t/g, ' ')
            .replace(/ +/g, ' ')
            .replace(/\n{3,}/g, '\n\n')
            .trim();
    }
    extractTitle(input) {
        if (input.path) {
            return input.path.split('/').pop()?.replace(/\.[^/.]+$/, '') || 'Untitled';
        }
        return 'Untitled Text Document';
    }
}
