import { Ollama } from 'ollama';
import OpenAI from 'openai';
import { McpError, ErrorCode } from '@modelcontextprotocol/sdk/types.js';
export class OllamaProvider {
    constructor(model = 'nomic-embed-text') {
        this.model = model;
        const baseUrl = process.env.OLLAMA_URL || 'http://localhost:11434';
        this.client = new Ollama({ host: baseUrl });
        console.error('Initializing Ollama provider with URL:', baseUrl);
    }
    async generateEmbeddings(text) {
        try {
            console.error('Generating Ollama embeddings for text:', text.substring(0, 50) + '...');
            const response = await this.client.embeddings({
                model: this.model,
                prompt: text
            });
            console.error('Successfully generated Ollama embeddings with size:', response.embedding.length);
            return response.embedding;
        }
        catch (error) {
            console.error('Ollama embedding error:', error);
            throw new McpError(ErrorCode.InternalError, `Failed to generate embeddings with Ollama: ${error}`);
        }
    }
    getVectorSize() {
        // nomic-embed-text produces 768-dimensional vectors
        return 768;
    }
}
export class OpenAIProvider {
    constructor(apiKey, model = 'text-embedding-3-small') {
        this.client = new OpenAI({ apiKey });
        this.model = model;
    }
    async generateEmbeddings(text) {
        try {
            console.error('Generating OpenAI embeddings for text:', text.substring(0, 50) + '...');
            const response = await this.client.embeddings.create({
                model: this.model,
                input: text,
            });
            const embedding = response.data[0].embedding;
            console.error('Successfully generated OpenAI embeddings with size:', embedding.length);
            return embedding;
        }
        catch (error) {
            console.error('OpenAI embedding error:', error);
            throw new McpError(ErrorCode.InternalError, `Failed to generate embeddings with OpenAI: ${error}`);
        }
    }
    getVectorSize() {
        // text-embedding-3-small produces 1536-dimensional vectors
        return 1536;
    }
}
export class EmbeddingService {
    constructor(provider) {
        this.provider = provider;
    }
    async generateEmbeddings(text) {
        return this.provider.generateEmbeddings(text);
    }
    getVectorSize() {
        return this.provider.getVectorSize();
    }
    static createFromConfig(config) {
        switch (config.provider) {
            case 'ollama':
                return new EmbeddingService(new OllamaProvider(config.model));
            case 'openai':
                if (!config.apiKey) {
                    throw new McpError(ErrorCode.InvalidParams, 'OpenAI API key is required');
                }
                return new EmbeddingService(new OpenAIProvider(config.apiKey, config.model));
            default:
                throw new McpError(ErrorCode.InvalidParams, `Unknown embedding provider: ${config.provider}`);
        }
    }
}
