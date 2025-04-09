export const defaultConfig = {
    server: {
        port: 3000,
        maxConcurrentRequests: 10,
        requestTimeout: 30000 // 30 seconds
    },
    database: {
        url: 'http://localhost:6333',
        collection: 'documentation',
        maxBatchSize: 100,
        backupDir: './backup'
    },
    embedding: {
        provider: 'ollama',
        model: 'nomic-embed-text',
        maxRetries: 3,
        apiKey: undefined
    },
    security: {
        rateLimitRequests: 100,
        rateLimitWindow: 60000, // 1 minute
        maxFileSize: 10 * 1024 * 1024 // 10MB
    },
    processing: {
        maxChunkSize: 1000,
        maxMemoryUsage: 512 * 1024 * 1024, // 512MB
        supportedFileTypes: [
            'pdf',
            'txt',
            'md',
            'js',
            'ts',
            'py',
            'java',
            'c',
            'cpp',
            'h',
            'hpp'
        ],
        maxFileSize: 10 * 1024 * 1024 // 10MB
    }
};
