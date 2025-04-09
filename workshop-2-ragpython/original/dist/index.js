#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ErrorCode, ListToolsRequestSchema, McpError, } from '@modelcontextprotocol/sdk/types.js';
import { QdrantClient } from '@qdrant/js-client-rest';
import { chromium } from 'playwright';
import * as cheerio from 'cheerio';
import axios from 'axios';
import crypto from 'crypto';
import { getDocument } from 'pdfjs-dist';
import { EmbeddingService } from './embeddings.js';
import fs from 'fs/promises';
import path from 'path';
// Environment variables for configuration
const OLLAMA_URL = process.env.OLLAMA_URL || 'http://localhost:11434';
const QDRANT_URL = process.env.QDRANT_URL || 'http://127.0.0.1:6333';
const COLLECTION_NAME = 'documentation';
const EMBEDDING_PROVIDER = process.env.EMBEDDING_PROVIDER || 'ollama';
const EMBEDDING_MODEL = process.env.EMBEDDING_MODEL;
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
// Log configuration on startup
console.error('Configuration:');
console.error(`QDRANT_URL: ${QDRANT_URL}`);
console.error(`OLLAMA_URL: ${OLLAMA_URL}`);
console.error(`EMBEDDING_PROVIDER: ${EMBEDDING_PROVIDER}`);
class RagDocsServer {
    constructor() {
        this.server = new Server({
            name: 'mcp-ragdocs',
            version: '0.1.0',
        }, {
            capabilities: {
                tools: {},
            },
        });
        // Error handling
        this.server.onerror = (error) => console.error('[MCP Error]', error);
        process.on('SIGINT', async () => {
            await this.cleanup();
            process.exit(0);
        });
    }
    async init() {
        // 1. Initialize Qdrant client
        this.qdrantClient = new QdrantClient({
            url: QDRANT_URL
        });
        // 2. Test connection
        try {
            const response = await this.qdrantClient.getCollections();
            console.error('Successfully connected to Qdrant:', response);
        }
        catch (error) {
            console.error('Failed to connect to Qdrant:', error);
            throw new McpError(ErrorCode.InternalError, 'Failed to establish initial connection to Qdrant server');
        }
        // 3. Initialize embedding service from environment configuration
        this.embeddingService = EmbeddingService.createFromConfig({
            provider: EMBEDDING_PROVIDER,
            model: EMBEDDING_MODEL,
            apiKey: OPENAI_API_KEY
        });
        // 4. Initialize collection if needed
        await this.initCollection();
        // 5. Setup tool handlers
        this.setupToolHandlers();
    }
    async initCollection() {
        const requiredVectorSize = this.embeddingService.getVectorSize();
        try {
            const collections = await this.qdrantClient.getCollections();
            const collection = collections.collections.find(c => c.name === COLLECTION_NAME);
            if (!collection) {
                console.error(`Creating new collection with vector size ${requiredVectorSize}`);
                await this.qdrantClient.createCollection(COLLECTION_NAME, {
                    vectors: {
                        size: requiredVectorSize,
                        distance: 'Cosine',
                    },
                });
                console.error('Collection created successfully');
                return;
            }
            // Check vector size if collection exists
            const collectionInfo = await this.qdrantClient.getCollection(COLLECTION_NAME);
            const currentVectorSize = collectionInfo.config?.params?.vectors?.size;
            if (!currentVectorSize || currentVectorSize !== requiredVectorSize) {
                console.error(`Vector size mismatch or not found. Recreating collection...`);
                await this.recreateCollection(requiredVectorSize);
            }
        }
        catch (error) {
            throw new McpError(ErrorCode.InternalError, `Failed to initialize collection: ${error}`);
        }
    }
    async recreateCollection(vectorSize) {
        try {
            // Delete existing collection if any
            try {
                await this.qdrantClient.deleteCollection(COLLECTION_NAME);
            }
            catch (error) {
                // Ignore if collection doesn't exist
            }
            // Create new collection
            await this.qdrantClient.createCollection(COLLECTION_NAME, {
                vectors: {
                    size: vectorSize,
                    distance: 'Cosine',
                },
            });
            console.error(`Collection recreated with vector size ${vectorSize}`);
        }
        catch (error) {
            throw new McpError(ErrorCode.InternalError, `Failed to recreate collection: ${error}`);
        }
    }
    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
        await this.server.close();
    }
    async processFile(filePath) {
        const fileExt = path.extname(filePath).toLowerCase().substring(1);
        if (!fileExt) {
            console.error(`No file extension found for: ${filePath}`);
            return [];
        }
        if (fileExt === 'pdf') {
            const buffer = await fs.readFile(filePath);
            const uint8Array = new Uint8Array(buffer);
            const pdf = await getDocument({ data: uint8Array }).promise;
            const chunks = [];
            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const content = await page.getTextContent();
                const text = content.items
                    .map((item) => item.str)
                    .join(' ')
                    .trim();
                // Split into chunks
                const words = text.split(/\s+/);
                let currentChunk = [];
                for (const word of words) {
                    currentChunk.push(word);
                    if (currentChunk.join(' ').length > 1000) {
                        chunks.push({
                            text: currentChunk.join(' '),
                            source: filePath,
                            title: `PDF: ${path.basename(filePath)} (Page ${i})`,
                            timestamp: new Date().toISOString(),
                        });
                        currentChunk = [];
                    }
                }
                if (currentChunk.length > 0) {
                    chunks.push({
                        text: currentChunk.join(' '),
                        source: filePath,
                        title: `PDF: ${path.basename(filePath)} (Page ${i})`,
                        timestamp: new Date().toISOString(),
                    });
                }
            }
            return chunks;
        }
        else if (['txt', 'md', 'js', 'ts', 'py', 'java', 'c', 'cpp', 'h', 'hpp'].includes(fileExt)) {
            const content = await fs.readFile(filePath, 'utf-8');
            const chunks = [];
            const words = content.split(/\s+/);
            let currentChunk = [];
            for (const word of words) {
                currentChunk.push(word);
                if (currentChunk.join(' ').length > 1000) {
                    chunks.push({
                        text: currentChunk.join(' '),
                        source: filePath,
                        title: `File: ${path.basename(filePath)}`,
                        timestamp: new Date().toISOString(),
                    });
                    currentChunk = [];
                }
            }
            if (currentChunk.length > 0) {
                chunks.push({
                    text: currentChunk.join(' '),
                    source: filePath,
                    title: `File: ${path.basename(filePath)}`,
                    timestamp: new Date().toISOString(),
                });
            }
            return chunks;
        }
        return [];
    }
    async processDirectory(dirPath) {
        const stats = { processed: 0, failed: 0 };
        try {
            const files = await fs.readdir(dirPath, { withFileTypes: true });
            for (const file of files) {
                const fullPath = path.join(dirPath, file.name);
                if (file.isDirectory()) {
                    const subStats = await this.processDirectory(fullPath);
                    stats.processed += subStats.processed;
                    stats.failed += subStats.failed;
                    continue;
                }
                try {
                    const chunks = await this.processFile(fullPath);
                    for (const chunk of chunks) {
                        const embedding = await this.embeddingService.generateEmbeddings(chunk.text);
                        // Initialize collection before upserting
                        await this.initCollection();
                        await this.qdrantClient.upsert(COLLECTION_NAME, {
                            wait: true,
                            points: [
                                {
                                    id: crypto.randomBytes(16).toString('hex'),
                                    vector: embedding,
                                    payload: {
                                        ...chunk,
                                        _type: 'DocumentChunk',
                                    },
                                },
                            ],
                        });
                    }
                    stats.processed++;
                }
                catch (error) {
                    console.error(`Failed to process file ${fullPath}:`, error);
                    stats.failed++;
                }
            }
        }
        catch (error) {
            console.error(`Failed to read directory ${dirPath}:`, error);
            throw new McpError(ErrorCode.InternalError, `Failed to read directory: ${error}`);
        }
        return stats;
    }
    setupToolHandlers() {
        this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
            tools: [
                {
                    name: 'add_documentation',
                    description: 'Add documentation from a URL to the RAG database',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            url: {
                                type: 'string',
                                description: 'URL of the documentation to fetch',
                            },
                        },
                        required: ['url'],
                    },
                },
                {
                    name: 'search_documentation',
                    description: 'Search through stored documentation',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            query: {
                                type: 'string',
                                description: 'Search query',
                            },
                            limit: {
                                type: 'number',
                                description: 'Maximum number of results to return',
                                default: 5,
                            },
                        },
                        required: ['query'],
                    },
                },
                {
                    name: 'list_sources',
                    description: 'List all documentation sources currently stored',
                    inputSchema: {
                        type: 'object',
                        properties: {},
                    },
                },
                {
                    name: 'add_directory',
                    description: 'Add all supported files from a directory to the RAG database',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            path: {
                                type: 'string',
                                description: 'Path to the directory containing documents',
                            },
                        },
                        required: ['path'],
                    },
                },
            ],
        }));
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            // Initialize collection before handling any request
            await this.initCollection();
            switch (request.params.name) {
                case 'add_directory':
                    return this.handleAddDirectory(request.params.arguments);
                case 'add_documentation':
                    return this.handleAddDocumentation(request.params.arguments);
                case 'search_documentation':
                    return this.handleSearchDocumentation(request.params.arguments);
                case 'list_sources':
                    return this.handleListSources();
                default:
                    throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
            }
        });
    }
    async handleAddDirectory(args) {
        if (!args.path || typeof args.path !== 'string') {
            throw new McpError(ErrorCode.InvalidParams, 'Directory path is required');
        }
        try {
            // Check if directory exists
            const stats = await fs.stat(args.path);
            if (!stats.isDirectory()) {
                throw new McpError(ErrorCode.InvalidParams, 'Path must be a directory');
            }
            const result = await this.processDirectory(args.path);
            return {
                content: [
                    {
                        type: 'text',
                        text: `Successfully processed ${result.processed} files, failed to process ${result.failed} files from ${args.path}`,
                    },
                ],
            };
        }
        catch (error) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `Failed to process directory: ${error}`,
                    },
                ],
                isError: true,
            };
        }
    }
    async handleAddDocumentation(args) {
        if (!args.url || typeof args.url !== 'string') {
            throw new McpError(ErrorCode.InvalidParams, 'URL is required');
        }
        try {
            const chunks = await this.fetchAndProcessUrl(args.url);
            let processedChunks = 0;
            for (const chunk of chunks) {
                const embedding = await this.embeddingService.generateEmbeddings(chunk.text);
                await this.qdrantClient.upsert(COLLECTION_NAME, {
                    wait: true,
                    points: [
                        {
                            id: crypto.randomBytes(16).toString('hex'),
                            vector: embedding,
                            payload: {
                                ...chunk,
                                _type: 'DocumentChunk',
                            },
                        },
                    ],
                });
                processedChunks++;
            }
            return {
                content: [
                    {
                        type: 'text',
                        text: `Successfully added ${processedChunks} chunks from ${args.url}`,
                    },
                ],
            };
        }
        catch (error) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `Failed to add documentation: ${error}`,
                    },
                ],
                isError: true,
            };
        }
    }
    async handleSearchDocumentation(args) {
        if (!args.query || typeof args.query !== 'string') {
            throw new McpError(ErrorCode.InvalidParams, 'Query is required');
        }
        try {
            const embedding = await this.embeddingService.generateEmbeddings(args.query);
            const results = await this.qdrantClient.search(COLLECTION_NAME, {
                vector: embedding,
                limit: args.limit || 5,
                with_payload: true,
            });
            const formatted = results.map(result => {
                const payload = result.payload;
                return `[${payload.title}](${payload.url || payload.source})\nScore: ${result.score}\n${payload.text}\n`;
            }).join('\n---\n');
            return {
                content: [
                    {
                        type: 'text',
                        text: formatted || 'No results found',
                    },
                ],
            };
        }
        catch (error) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `Search failed: ${error}`,
                    },
                ],
                isError: true,
            };
        }
    }
    async handleListSources() {
        try {
            const scroll = await this.qdrantClient.scroll(COLLECTION_NAME, {
                with_payload: true,
            });
            const sources = new Set();
            for (const point of scroll.points) {
                const payload = point.payload;
                if (payload?.url) {
                    sources.add(`${payload.title} (${payload.url})`);
                }
                else if (payload?.source) {
                    sources.add(`${payload.title} (${payload.source})`);
                }
            }
            return {
                content: [
                    {
                        type: 'text',
                        text: Array.from(sources).join('\n') || 'No documentation sources found.',
                    },
                ],
            };
        }
        catch (error) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `Failed to list sources: ${error}`,
                    },
                ],
                isError: true,
            };
        }
    }
    async fetchAndProcessUrl(url) {
        // Check if PDF
        const response = await axios.head(url);
        const contentType = response.headers['content-type'];
        if (contentType?.includes('application/pdf')) {
            // Handle PDF
            const response = await axios.get(url, { responseType: 'arraybuffer' });
            const uint8Array = new Uint8Array(response.data);
            const pdf = await getDocument({ data: uint8Array }).promise;
            const chunks = [];
            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const content = await page.getTextContent();
                const text = content.items
                    .map((item) => item.str)
                    .join(' ')
                    .trim();
                // Split into chunks
                const words = text.split(/\s+/);
                let currentChunk = [];
                for (const word of words) {
                    currentChunk.push(word);
                    if (currentChunk.join(' ').length > 1000) {
                        chunks.push({
                            text: currentChunk.join(' '),
                            url,
                            title: `PDF: ${url} (Page ${i})`,
                            timestamp: new Date().toISOString(),
                        });
                        currentChunk = [];
                    }
                }
                if (currentChunk.length > 0) {
                    chunks.push({
                        text: currentChunk.join(' '),
                        url,
                        title: `PDF: ${url} (Page ${i})`,
                        timestamp: new Date().toISOString(),
                    });
                }
            }
            return chunks;
        }
        // Handle HTML
        if (!this.browser) {
            this.browser = await chromium.launch();
        }
        const page = await this.browser.newPage();
        try {
            await page.goto(url, { waitUntil: 'networkidle' });
            const content = await page.content();
            // Parse content
            const $ = cheerio.load(content);
            // Remove unnecessary elements
            $('script').remove();
            $('style').remove();
            $('nav').remove();
            $('footer').remove();
            // Get main content
            const text = $('body').text();
            const title = $('title').text() || url;
            // Split into chunks
            const chunks = [];
            const words = text.split(/\s+/);
            let currentChunk = [];
            for (const word of words) {
                currentChunk.push(word);
                if (currentChunk.join(' ').length > 1000) {
                    chunks.push({
                        text: currentChunk.join(' '),
                        url,
                        title,
                        timestamp: new Date().toISOString(),
                    });
                    currentChunk = [];
                }
            }
            if (currentChunk.length > 0) {
                chunks.push({
                    text: currentChunk.join(' '),
                    url,
                    title,
                    timestamp: new Date().toISOString(),
                });
            }
            return chunks;
        }
        finally {
            await page.close();
        }
    }
    async run() {
        try {
            await this.init();
            const transport = new StdioServerTransport();
            await this.server.connect(transport);
            console.error('RAG Docs MCP server running on stdio');
        }
        catch (error) {
            console.error('Failed to initialize server:', error);
            process.exit(1);
        }
    }
}
const server = new RagDocsServer();
server.run().catch(console.error);
