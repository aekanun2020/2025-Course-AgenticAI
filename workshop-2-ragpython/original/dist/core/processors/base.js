export class BaseProcessor {
    constructor(logger, metrics, options = {}) {
        this.logger = logger;
        this.metrics = metrics;
        this.options = {
            maxChunkSize: 1000,
            overlap: 200,
            ...options
        };
    }
}
export class DocumentProcessor extends BaseProcessor {
    async processDocument(input) {
        try {
            if (!this.canProcess(input)) {
                throw new Error(`Cannot process input type: ${input.mimeType}`);
            }
            let content;
            if (input.content) {
                content = Buffer.isBuffer(input.content) ?
                    input.content.toString('utf-8') :
                    input.content;
            }
            else {
                const buffer = await window.fs.readFile(input.path);
                content = Buffer.isBuffer(buffer) ?
                    buffer.toString('utf-8') :
                    buffer;
            }
            const chunks = await this.processContent(content);
            const title = this.extractTitle(input);
            return {
                chunks: chunks.map(chunk => ({
                    ...chunk,
                    metadata: {
                        ...chunk.metadata,
                        title,
                        source: input.path,
                        timestamp: Date.now()
                    }
                })),
                metadata: {
                    totalSize: content.length,
                    processedFiles: 1,
                    title
                }
            };
        }
        catch (error) {
            this.logger.error('Processing error:', error);
            return {
                chunks: [],
                metadata: {
                    totalSize: 0,
                    processedFiles: 0,
                    errors: [error]
                }
            };
        }
    }
    async validateInput(input) {
        if (!input.path && !input.content) {
            throw new Error('Input must contain either path or content');
        }
    }
    async chunkContent(text) {
        const { maxChunkSize = 1000, overlap = 200 } = this.options;
        const chunks = [];
        let start = 0;
        while (start < text.length) {
            const end = Math.min(start + maxChunkSize, text.length);
            chunks.push(text.slice(start, end));
            start = end - overlap;
        }
        return chunks;
    }
    createChunk(content, metadata = {}) {
        return {
            content,
            metadata: {
                timestamp: Date.now(),
                ...metadata,
                source: metadata.source || ''
            }
        };
    }
}
