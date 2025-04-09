export class EmbeddingProvider {
    constructor(provider, model, maxRetries, logger) {
        this.provider = provider;
        this.model = model;
        this.maxRetries = maxRetries;
        this.logger = logger;
    }
}
export class EmbeddingService extends EmbeddingProvider {
    async generateEmbedding(text) {
        let retries = 0;
        while (retries < this.maxRetries) {
            try {
                return this.provider === 'ollama' ?
                    await this.generateOllamaEmbedding(text) :
                    await this.generateOpenAIEmbedding(text);
            }
            catch (error) {
                retries++;
                if (retries >= this.maxRetries)
                    throw error;
                await new Promise(resolve => setTimeout(resolve, 1000 * retries));
            }
        }
        throw new Error('Failed to generate embedding after max retries');
    }
    async generateEmbeddings(texts) {
        return Promise.all(texts.map(text => this.generateEmbedding(text)));
    }
    async generateOllamaEmbedding(text) {
        const response = await fetch('http://localhost:11434/api/embeddings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: this.model, prompt: text })
        });
        if (!response.ok)
            throw new Error(`Ollama API error: ${response.statusText}`);
        const data = await response.json();
        return data.embedding;
    }
    async generateOpenAIEmbedding(text) {
        const openaiKey = process.env.OPENAI_API_KEY;
        if (!openaiKey)
            throw new Error('OpenAI API key not found');
        const response = await fetch('https://api.openai.com/v1/embeddings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${openaiKey}`
            },
            body: JSON.stringify({ model: this.model, input: text })
        });
        if (!response.ok)
            throw new Error(`OpenAI API error: ${response.statusText}`);
        const data = await response.json();
        return data.data[0].embedding;
    }
}
