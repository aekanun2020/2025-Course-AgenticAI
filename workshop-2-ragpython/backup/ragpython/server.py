import os
import sys
import json
import asyncio
import logging
import hashlib
import aiofiles
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import aiohttp
import mcp.server
from mcp.server.stdio import stdio_server
from mcp.types import ErrorCode, McpError

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import fitz  # PyMuPDF

from embeddings import EmbeddingService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables for configuration
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
QDRANT_URL = os.environ.get('QDRANT_URL', 'http://127.0.0.1:6333')
COLLECTION_NAME = 'documentation'
EMBEDDING_PROVIDER = os.environ.get('EMBEDDING_PROVIDER', 'ollama')
EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Log configuration on startup
logger.info('Configuration:')
logger.info(f'QDRANT_URL: {QDRANT_URL}')
logger.info(f'OLLAMA_URL: {OLLAMA_URL}')
logger.info(f'EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}')


class RagDocsServer:
    def __init__(self):
        self.server = mcp.server.Server(
            "mcp-ragdocs",
            version="0.1.0",
            capabilities={
                "tools": {
                    "listChanged": True
                }
            }
        )
        
        self.qdrant_client = None
        self.embedding_service = None
        self.browser = None
        self.browser_context = None
        
        # Register signal handlers
        try:
            import signal
            signal.signal(signal.SIGINT, self._handle_sigint)
            signal.signal(signal.SIGTERM, self._handle_sigint)
        except (ImportError, AttributeError):
            # Signal might not be available on all platforms
            pass
    
    def _handle_sigint(self, sig, frame):
        """Handle SIGINT signal by cleaning up and exiting."""
        logger.info("Received signal to shutdown")
        asyncio.create_task(self.cleanup())
        sys.exit(0)
    
    async def init(self):
        """Initialize the server components."""
        # 1. Initialize Qdrant client
        self.qdrant_client = QdrantClient(url=QDRANT_URL)
        
        # 2. Test connection
        try:
            response = self.qdrant_client.get_collections()
            logger.info(f'Successfully connected to Qdrant: {response}')
        except Exception as error:
            logger.error(f'Failed to connect to Qdrant: {error}')
            raise McpError(
                ErrorCode.InternalError, 
                'Failed to establish initial connection to Qdrant server'
            )
        
        # 3. Initialize embedding service from environment configuration
        self.embedding_service = EmbeddingService.create_from_config({
            'provider': EMBEDDING_PROVIDER,
            'model': EMBEDDING_MODEL,
            'api_key': OPENAI_API_KEY
        })
        
        # 4. Initialize collection if needed
        await self.init_collection()
        
        # 5. Setup tool handlers
        self.setup_tool_handlers()
    
    async def init_collection(self):
        """Initialize Qdrant collection."""
        required_vector_size = self.embedding_service.get_vector_size()
        
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if COLLECTION_NAME not in collection_names:
                logger.info(f'Creating new collection with vector size {required_vector_size}')
                self.qdrant_client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=qmodels.VectorParams(
                        size=required_vector_size,
                        distance=qmodels.Distance.COSINE
                    )
                )
                logger.info('Collection created successfully')
                return
            
            # Check vector size if collection exists
            collection_info = self.qdrant_client.get_collection(COLLECTION_NAME)
            current_vector_size = collection_info.config.params.vectors.size
            
            if current_vector_size != required_vector_size:
                logger.info(f'Vector size mismatch. Recreating collection...')
                await self.recreate_collection(required_vector_size)
                
        except Exception as error:
            raise McpError(ErrorCode.InternalError, f'Failed to initialize collection: {error}')
    
    async def recreate_collection(self, vector_size):
        """Recreate collection with new vector size."""
        try:
            # Delete existing collection if any
            try:
                self.qdrant_client.delete_collection(COLLECTION_NAME)
            except Exception:
                # Ignore if collection doesn't exist
                pass
            
            # Create new collection
            self.qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=qmodels.VectorParams(
                    size=vector_size,
                    distance=qmodels.Distance.COSINE
                )
            )
            logger.info(f'Collection recreated with vector size {vector_size}')
        except Exception as error:
            raise McpError(ErrorCode.InternalError, f'Failed to recreate collection: {error}')
    
    async def cleanup(self):
        """Cleanup resources before shutdown."""
        if self.browser:
            await self.browser.close()
            self.browser = None
    
    async def process_file(self, file_path):
        """Process a file into text chunks for embedding."""
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower()[1:]  # Remove the dot
        
        if not file_ext:
            logger.error(f'No file extension found for: {file_path}')
            return []
        
        if file_ext == 'pdf':
            try:
                chunks = []
                # Open the PDF file
                pdf_document = fitz.open(file_path)
                
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    text = page.get_text()
                    
                    # Split into chunks
                    words = text.split()
                    current_chunk = []
                    
                    for word in words:
                        current_chunk.append(word)
                        if len(' '.join(current_chunk)) > 1000:
                            chunks.append({
                                'text': ' '.join(current_chunk),
                                'source': str(file_path),
                                'title': f'PDF: {file_path.name} (Page {page_num + 1})',
                                'timestamp': None  # Will be set when upserting
                            })
                            current_chunk = []
                    
                    if current_chunk:
                        chunks.append({
                            'text': ' '.join(current_chunk),
                            'source': str(file_path),
                            'title': f'PDF: {file_path.name} (Page {page_num + 1})',
                            'timestamp': None
                        })
                
                return chunks
                
            except Exception as e:
                logger.error(f'Error processing PDF {file_path}: {e}')
                return []
                
        elif file_ext in ['txt', 'md', 'js', 'ts', 'py', 'java', 'c', 'cpp', 'h', 'hpp']:
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                chunks = []
                words = content.split()
                current_chunk = []
                
                for word in words:
                    current_chunk.append(word)
                    if len(' '.join(current_chunk)) > 1000:
                        chunks.append({
                            'text': ' '.join(current_chunk),
                            'source': str(file_path),
                            'title': f'File: {file_path.name}',
                            'timestamp': None
                        })
                        current_chunk = []
                
                if current_chunk:
                    chunks.append({
                        'text': ' '.join(current_chunk),
                        'source': str(file_path),
                        'title': f'File: {file_path.name}',
                        'timestamp': None
                    })
                
                return chunks
                
            except Exception as e:
                logger.error(f'Error processing text file {file_path}: {e}')
                return []
        
        return []
    
    async def process_directory(self, dir_path):
        """Process all supported files in a directory."""
        stats = {'processed': 0, 'failed': 0}
        
        try:
            dir_path = Path(dir_path)
            for file_path in dir_path.glob('**/*'):
                if file_path.is_dir():
                    continue
                
                try:
                    chunks = await self.process_file(file_path)
                    for chunk in chunks:
                        # Set timestamp
                        from datetime import datetime
                        chunk['timestamp'] = datetime.now().isoformat()
                        
                        # Generate embedding
                        embedding = await self.embedding_service.generate_embeddings(chunk['text'])
                        
                        # Generate point ID from content hash
                        point_id = hashlib.md5(chunk['text'].encode('utf-8')).hexdigest()
                        
                        # Upsert to Qdrant
                        self.qdrant_client.upsert(
                            collection_name=COLLECTION_NAME,
                            points=[
                                qmodels.PointStruct(
                                    id=point_id,
                                    vector=embedding,
                                    payload={
                                        **chunk,
                                        '_type': 'DocumentChunk'
                                    }
                                )
                            ],
                            wait=True
                        )
                    
                    stats['processed'] += 1
                    
                except Exception as error:
                    logger.error(f'Failed to process file {file_path}: {error}')
                    stats['failed'] += 1
            
        except Exception as error:
            logger.error(f'Failed to read directory {dir_path}: {error}')
            raise McpError(ErrorCode.InternalError, f'Failed to read directory: {error}')
        
        return stats
    
    def setup_tool_handlers(self):
        """Set up MCP tool handlers."""
        # Register tools list
        @self.server.list_tools()
        async def list_tools():
            return [
                {
                    'name': 'add_documentation',
                    'description': 'Add documentation from a URL to the RAG database',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'url': {
                                'type': 'string',
                                'description': 'URL of the documentation to fetch'
                            }
                        },
                        'required': ['url']
                    }
                },
                {
                    'name': 'search_documentation',
                    'description': 'Search through stored documentation',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'Search query'
                            },
                            'limit': {
                                'type': 'number',
                                'description': 'Maximum number of results to return',
                                'default': 5
                            }
                        },
                        'required': ['query']
                    }
                },
                {
                    'name': 'list_sources',
                    'description': 'List all documentation sources currently stored',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {}
                    }
                },
                {
                    'name': 'add_directory',
                    'description': 'Add all supported files from a directory to the RAG database',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'path': {
                                'type': 'string',
                                'description': 'Path to the directory containing documents'
                            }
                        },
                        'required': ['path']
                    }
                }
            ]
        
        # Register tool call handler
        @self.server.call_tool()
        async def call_tool(name, arguments):
            # Initialize collection before handling any request
            await self.init_collection()
            
            if name == 'add_directory':
                return await self.handle_add_directory(arguments)
            elif name == 'add_documentation':
                return await self.handle_add_documentation(arguments)
            elif name == 'search_documentation':
                return await self.handle_search_documentation(arguments)
            elif name == 'list_sources':
                return await self.handle_list_sources()
            else:
                raise McpError(ErrorCode.MethodNotFound, f'Unknown tool: {name}')
    
    async def handle_add_directory(self, args):
        """Handle add_directory tool call."""
        path = args.get('path')
        if not path or not isinstance(path, str):
            raise McpError(ErrorCode.InvalidParams, 'Directory path is required')
        
        try:
            # Check if directory exists
            dir_path = Path(path)
            if not dir_path.is_dir():
                raise McpError(ErrorCode.InvalidParams, 'Path must be a directory')
            
            result = await self.process_directory(path)
            
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f'Successfully processed {result["processed"]} files, failed to process {result["failed"]} files from {path}'
                    }
                ]
            }
        except Exception as error:
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f'Failed to process directory: {error}'
                    }
                ],
                'isError': True
            }
    
    async def handle_add_documentation(self, args):
        """Handle add_documentation tool call."""
        url = args.get('url')
        if not url or not isinstance(url, str):
            raise McpError(ErrorCode.InvalidParams, 'URL is required')
        
        try:
            chunks = await self.fetch_and_process_url(url)
            processed_chunks = 0
            
            for chunk in chunks:
                embedding = await self.embedding_service.generate_embeddings(chunk['text'])
                
                # Generate point ID from content hash
                point_id = hashlib.md5(chunk['text'].encode('utf-8')).hexdigest()
                
                self.qdrant_client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=[
                        qmodels.PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload={
                                **chunk,
                                '_type': 'DocumentChunk'
                            }
                        )
                    ],
                    wait=True
                )
                processed_chunks += 1
            
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f'Successfully added {processed_chunks} chunks from {url}'
                    }
                ]
            }
        except Exception as error:
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f'Failed to add documentation: {error}'
                    }
                ],
                'isError': True
            }
    
    async def handle_search_documentation(self, args):
        """Handle search_documentation tool call."""
        query = args.get('query')
        if not query or not isinstance(query, str):
            raise McpError(ErrorCode.InvalidParams, 'Query is required')
        
        try:
            embedding = await self.embedding_service.generate_embeddings(query)
            results = self.qdrant_client.search(
                collection_name=COLLECTION_NAME,
                query_vector=embedding,
                limit=args.get('limit', 5),
                with_payload=True
            )
            
            formatted = []
            for result in results:
                payload = result.payload
                formatted.append(
                    f"[{payload.get('title')}]({payload.get('url') or payload.get('source')})\n"
                    f"Score: {result.score}\n{payload.get('text')}\n"
                )
            
            formatted_text = '\n---\n'.join(formatted) or 'No results found'
            
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': formatted_text
                    }
                ]
            }
        except Exception as error:
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f'Search failed: {error}'
                    }
                ],
                'isError': True
            }
    
    async def handle_list_sources(self):
        """Handle list_sources tool call."""
        try:
            # Using scroll to get all points
            scroll_result = self.qdrant_client.scroll(
                collection_name=COLLECTION_NAME,
                with_payload=True,
                limit=100  # You may need to paginate for large collections
            )
            
            sources = set()
            for point in scroll_result[0]:
                payload = point.payload
                if payload.get('url'):
                    sources.add(f"{payload.get('title')} ({payload.get('url')})")
                elif payload.get('source'):
                    sources.add(f"{payload.get('title')} ({payload.get('source')})")
            
            source_list = '\n'.join(sources) or 'No documentation sources found.'
            
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': source_list
                    }
                ]
            }
        except Exception as error:
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f'Failed to list sources: {error}'
                    }
                ],
                'isError': True
            }
    
    async def fetch_and_process_url(self, url):
        """Fetch and process a URL into text chunks."""
        # Check if PDF
        async with aiohttp.ClientSession() as session:
            try:
                head_response = await session.head(url)
                content_type = head_response.headers.get('Content-Type', '')
                
                if 'application/pdf' in content_type:
                    # Handle PDF
                    async with session.get(url) as response:
                        if response.status != 200:
                            raise Exception(f"Failed to download PDF: HTTP {response.status}")
                        
                        pdf_data = await response.read()
                        
                        # Save to temporary file
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                            tmp.write(pdf_data)
                            tmp_path = tmp.name
                        
                        try:
                            # Process PDF file
                            pdf_document = fitz.open(tmp_path)
                            chunks = []
                            
                            for page_num in range(len(pdf_document)):
                                page = pdf_document[page_num]
                                text = page.get_text()
                                
                                # Split into chunks
                                words = text.split()
                                current_chunk = []
                                
                                for word in words:
                                    current_chunk.append(word)
                                    if len(' '.join(current_chunk)) > 1000:
                                        chunks.append({
                                            'text': ' '.join(current_chunk),
                                            'url': url,
                                            'title': f'PDF: {url} (Page {page_num + 1})',
                                            'timestamp': None
                                        })
                                        current_chunk = []
                                
                                if current_chunk:
                                    chunks.append({
                                        'text': ' '.join(current_chunk),
                                        'url': url,
                                        'title': f'PDF: {url} (Page {page_num + 1})',
                                        'timestamp': None
                                    })
                            
                            # Set timestamps
                            from datetime import datetime
                            for chunk in chunks:
                                chunk['timestamp'] = datetime.now().isoformat()
                            
                            return chunks
                        finally:
                            # Remove temporary file
                            os.unlink(tmp_path)
            
            except Exception as e:
                logger.error(f"Error with HEAD request or PDF processing: {e}")
            
            # Handle HTML (default if not PDF or if PDF processing failed)
            try:
                if not self.browser:
                    playwright = await async_playwright().start()
                    self.browser = await playwright.chromium.launch()
                
                page = await self.browser.new_page()
                try:
                    await page.goto(url, wait_until='networkidle')
                    content = await page.content()
                    
                    # Parse content
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Remove unnecessary elements
                    for tag in soup.select('script, style, nav, footer'):
                        tag.extract()
                    
                    # Get main content
                    text = soup.get_text(' ', strip=True)
                    title = soup.title.string if soup.title else url
                    
                    # Split into chunks
                    chunks = []
                    words = text.split()
                    current_chunk = []
                    
                    for word in words:
                        current_chunk.append(word)
                        if len(' '.join(current_chunk)) > 1000:
                            chunks.append({
                                'text': ' '.join(current_chunk),
                                'url': url,
                                'title': title,
                                'timestamp': datetime.now().isoformat()
                            })
                            current_chunk = []
                    
                    if current_chunk:
                        chunks.append({
                            'text': ' '.join(current_chunk),
                            'url': url,
                            'title': title,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    return chunks
                finally:
                    await page.close()
            except Exception as e:
                logger.error(f"Error processing HTML: {e}")
                raise
    
    async def run(self):
        """Run the server."""
        try:
            # Initialize components
            await self.init()
            
            # Connect to transport and run
            async with stdio_server() as streams:
                reader, writer = streams
                await self.server.run(reader, writer)
                
            logger.info('RAG Docs MCP server exited gracefully')
        
        except Exception as error:
            logger.error(f'Failed to start server: {error}')
            await self.cleanup()
            sys.exit(1)
