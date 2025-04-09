export class ConfigManager {
    constructor() {
        this.config = new Map();
        // Load environment variables
        this.config.set('QDRANT_URL', process.env.QDRANT_URL || 'http://localhost:6333');
        this.config.set('EMBEDDING_PROVIDER', process.env.EMBEDDING_PROVIDER || 'ollama');
        this.config.set('OLLAMA_URL', process.env.OLLAMA_URL || 'http://localhost:11434');
        this.config.set('MAX_FILE_SIZE', process.env.MAX_FILE_SIZE || '10485760'); // 10MB
        this.config.set('MAX_CHUNK_SIZE', process.env.MAX_CHUNK_SIZE || '1000');
        this.config.set('MAX_MEMORY_USAGE', process.env.MAX_MEMORY_USAGE || '536870912'); // 512MB
        this.config.set('COLLECTION_NAME', process.env.COLLECTION_NAME || 'documentation');
        this.config.set('MAX_BATCH_SIZE', process.env.MAX_BATCH_SIZE || '100');
        this.config.set('EMBEDDING_MODEL', process.env.EMBEDDING_MODEL || 'nomic-embed-text');
        this.config.set('EMBEDDING_MAX_RETRIES', process.env.EMBEDDING_MAX_RETRIES || '3');
        this.config.set('BACKUP_DIR', process.env.BACKUP_DIR || './backup');
    }
    static getInstance() {
        if (!ConfigManager.instance) {
            ConfigManager.instance = new ConfigManager();
        }
        return ConfigManager.instance;
    }
    get(key) {
        const value = this.config.get(key);
        if (value === undefined) {
            throw new Error(`Configuration key not found: ${key}`);
        }
        return value;
    }
    set(key, value) {
        this.config.set(key, value);
    }
}
