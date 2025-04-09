export function validateConfig(config) {
    // Validate Server Config
    if (!validateServerConfig(config.server)) {
        return {
            success: false,
            error: 'Invalid server configuration'
        };
    }
    // Validate Database Config
    if (!validateDatabaseConfig(config.database)) {
        return {
            success: false,
            error: 'Invalid database configuration'
        };
    }
    // Validate Embedding Config
    if (!validateEmbeddingConfig(config.embedding)) {
        return {
            success: false,
            error: 'Invalid embedding configuration'
        };
    }
    // Validate Security Config
    if (!validateSecurityConfig(config.security)) {
        return {
            success: false,
            error: 'Invalid security configuration'
        };
    }
    // Validate Processing Config
    if (!validateProcessingConfig(config.processing)) {
        return {
            success: false,
            error: 'Invalid processing configuration'
        };
    }
    return { success: true };
}
function validateServerConfig(config) {
    return (typeof config.port === 'number' &&
        config.port > 0 &&
        config.port < 65536 &&
        typeof config.maxConcurrentRequests === 'number' &&
        config.maxConcurrentRequests > 0 &&
        typeof config.requestTimeout === 'number' &&
        config.requestTimeout > 0);
}
function validateDatabaseConfig(config) {
    return (typeof config.url === 'string' &&
        config.url.length > 0 &&
        typeof config.collection === 'string' &&
        config.collection.length > 0 &&
        typeof config.maxBatchSize === 'number' &&
        config.maxBatchSize > 0 &&
        typeof config.backupDir === 'string');
}
function validateEmbeddingConfig(config) {
    if (!['ollama', 'openai'].includes(config.provider)) {
        return false;
    }
    if (config.provider === 'openai' && !config.apiKey) {
        return false;
    }
    return (typeof config.model === 'string' &&
        config.model.length > 0 &&
        typeof config.maxRetries === 'number' &&
        config.maxRetries > 0);
}
function validateSecurityConfig(config) {
    return (typeof config.rateLimitRequests === 'number' &&
        config.rateLimitRequests > 0 &&
        typeof config.rateLimitWindow === 'number' &&
        config.rateLimitWindow > 0 &&
        typeof config.maxFileSize === 'number' &&
        config.maxFileSize > 0);
}
function validateProcessingConfig(config) {
    return (typeof config.maxChunkSize === 'number' &&
        config.maxChunkSize > 0 &&
        typeof config.maxMemoryUsage === 'number' &&
        config.maxMemoryUsage > 0 &&
        Array.isArray(config.supportedFileTypes) &&
        config.supportedFileTypes.length > 0 &&
        config.supportedFileTypes.every(type => typeof type === 'string'));
}
