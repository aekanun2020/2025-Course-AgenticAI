import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
const server = new Server({
    name: 'ragdocs',
    description: 'RAG Documents Server',
    version: '1.0.0',
}, {
    capabilities: {
        tools: {},
    },
});
const transport = new StdioServerTransport();
server.connect(transport).catch(console.error);
