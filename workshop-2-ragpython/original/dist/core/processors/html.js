import { DocumentProcessor } from './base';
import { ProcessingError } from '../../utils/errors';
import * as cheerio from 'cheerio';
export class HTMLProcessor extends DocumentProcessor {
    constructor() {
        super(...arguments);
        this.EXCLUDE_SELECTORS = [
            'script', 'style', 'noscript', 'iframe', 'nav', 'footer', 'header',
            '.nav', '.footer', '.header', '.sidebar', '.advertisement', '.ad',
            '[role="navigation"]', '[role="banner"]', '[role="complementary"]'
        ];
        this.MAIN_CONTENT_SELECTORS = [
            'article', 'main', '.content', '.post', '.article', '.entry',
            '[role="main"]', '[role="article"]'
        ];
    }
    async processContent(content) {
        this.metrics.startOperation('html_processing');
        try {
            const $ = cheerio.load(content);
            const cleanContent = this.extractContent($);
            const textChunks = await this.chunkContent(cleanContent);
            const chunks = textChunks.map((chunk, index) => this.createChunk(chunk, {
                chunkIndex: index,
                totalChunks: textChunks.length,
                htmlInfo: {
                    title: this.extractTitle({ $, path: '', content }),
                    metadata: this.extractMetadata($),
                    originalSize: content.length,
                    processedSize: cleanContent.length
                }
            }));
            this.metrics.endOperation('html_processing');
            return chunks;
        }
        catch (error) {
            this.metrics.endOperation('html_processing');
            throw new ProcessingError('Failed to process HTML', { cause: error });
        }
    }
    canProcess(input) {
        return input.mimeType?.includes('html') || false;
    }
    extractContent($) {
        this.EXCLUDE_SELECTORS.forEach(selector => {
            $(selector).remove();
        });
        let mainContent = '';
        for (const selector of this.MAIN_CONTENT_SELECTORS) {
            const element = $(selector);
            if (element.length > 0) {
                mainContent = element.text();
                break;
            }
        }
        if (!mainContent) {
            mainContent = $('body').text();
        }
        return this.cleanupText(mainContent);
    }
    extractMetadata($) {
        const metadata = {};
        $('meta').each((_, element) => {
            const name = $(element).attr('name') ||
                $(element).attr('property') ||
                $(element).attr('http-equiv');
            const content = $(element).attr('content');
            if (name && content) {
                metadata[name] = content;
            }
        });
        $('meta[property^="og:"]').each((_, element) => {
            const property = $(element).attr('property');
            const content = $(element).attr('content');
            if (property && content) {
                metadata[property] = content;
            }
        });
        return metadata;
    }
    cleanupText(text) {
        return text
            .replace(/\s+/g, ' ')
            .replace(/[\r\n]+/g, '\n')
            .replace(/\n\s+/g, '\n')
            .replace(/\s+\n/g, '\n')
            .replace(/\n{3,}/g, '\n\n')
            .trim();
    }
    extractTitle(input) {
        if (input.$) {
            const metaTitle = input.$('meta[property="og:title"]').attr('content') ||
                input.$('meta[name="twitter:title"]').attr('content');
            if (metaTitle)
                return metaTitle;
            const titleTag = input.$('title').text().trim();
            if (titleTag)
                return titleTag;
            const h1 = input.$('h1').first().text().trim();
            if (h1)
                return h1;
        }
        if (input.path) {
            return input.path.split('/').pop()?.replace(/\.[^/.]+$/, '') || 'Untitled';
        }
        return 'Untitled HTML Document';
    }
}
