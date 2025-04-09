import { EmbeddingProvider } from './base';
export class OllamaEmbedding extends EmbeddingProvider {
    async generateEmbedding(text) {
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
    async generateEmbeddings(texts) {
        return Promise.all(texts.map(text => this.generateEmbedding(text)));
    }
}
