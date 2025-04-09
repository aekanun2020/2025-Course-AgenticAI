import { EmbeddingProvider } from './base';
export class OpenAIEmbedding extends EmbeddingProvider {
    async generateEmbedding(text) {
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
    async generateEmbeddings(texts) {
        return Promise.all(texts.map(text => this.generateEmbedding(text)));
    }
}
