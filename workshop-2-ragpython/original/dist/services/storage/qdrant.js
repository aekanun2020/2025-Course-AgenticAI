export class QdrantService {
    constructor(url, collectionName, logger) {
        this.url = url;
        this.collectionName = collectionName;
        this.logger = logger;
    }
    async initialize() {
        try {
            // Check if collection exists
            const response = await this.fetchQdrant(`/collections/${this.collectionName}`);
            if (!response.ok && response.status === 404) {
                // Create collection if it doesn't exist
                await this.createCollection();
            }
            else if (!response.ok) {
                throw new Error(`Failed to check collection: ${response.statusText}`);
            }
        }
        catch (error) {
            this.logger.error('Failed to initialize Qdrant:', error);
            throw error;
        }
    }
    async addDocuments(embeddings, chunks) {
        try {
            if (embeddings.length !== chunks.length) {
                throw new Error('Number of embeddings must match number of chunks');
            }
            const points = embeddings.map((embedding, i) => ({
                id: crypto.randomUUID(),
                vector: embedding,
                payload: {
                    content: chunks[i].content,
                    metadata: chunks[i].metadata
                }
            }));
            // Split into batches of 100
            for (let i = 0; i < points.length; i += 100) {
                const batch = points.slice(i, i + 100);
                await this.upsertPoints(batch);
            }
        }
        catch (error) {
            this.logger.error('Failed to add documents:', error);
            throw error;
        }
    }
    async search(query, limit, vector) {
        try {
            const response = await this.fetchQdrant(`/collections/${this.collectionName}/points/search`, {
                method: 'POST',
                body: JSON.stringify({
                    vector,
                    limit,
                    with_payload: true
                })
            });
            if (!response.ok) {
                throw new Error(`Search failed: ${response.statusText}`);
            }
            const data = await response.json();
            return data.result;
        }
        catch (error) {
            this.logger.error('Search failed:', error);
            throw error;
        }
    }
    async listSources() {
        try {
            const response = await this.fetchQdrant(`/collections/${this.collectionName}/points/scroll`, {
                method: 'POST',
                body: JSON.stringify({
                    limit: 1000,
                    with_payload: true,
                    with_vector: false
                })
            });
            if (!response.ok) {
                throw new Error(`Failed to list sources: ${response.statusText}`);
            }
            const data = await response.json();
            const sources = new Set();
            for (const point of data.result.points) {
                const { metadata } = point.payload;
                if (metadata?.source) {
                    sources.add(metadata.source);
                }
            }
            return Array.from(sources);
        }
        catch (error) {
            this.logger.error('Failed to list sources:', error);
            throw error;
        }
    }
    async createBackup(path) {
        try {
            const response = await this.fetchQdrant('/collections/backup', {
                method: 'POST',
                body: JSON.stringify({
                    collection_name: this.collectionName,
                    path
                })
            });
            if (!response.ok) {
                throw new Error(`Backup failed: ${response.statusText}`);
            }
        }
        catch (error) {
            this.logger.error('Backup failed:', error);
            throw error;
        }
    }
    async createCollection() {
        const response = await this.fetchQdrant('/collections', {
            method: 'PUT',
            body: JSON.stringify({
                name: this.collectionName,
                vectors: {
                    size: 768,
                    distance: 'Cosine'
                }
            })
        });
        if (!response.ok) {
            throw new Error(`Failed to create collection: ${response.statusText}`);
        }
    }
    async upsertPoints(points) {
        const response = await this.fetchQdrant(`/collections/${this.collectionName}/points`, {
            method: 'PUT',
            body: JSON.stringify({
                points
            })
        });
        if (!response.ok) {
            throw new Error(`Failed to upsert points: ${response.statusText}`);
        }
    }
    async fetchQdrant(path, init) {
        const url = new URL(path, this.url);
        return fetch(url.toString(), {
            ...init,
            headers: {
                'Content-Type': 'application/json',
                ...init?.headers
            }
        });
    }
}
