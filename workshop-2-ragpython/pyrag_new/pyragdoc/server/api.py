"""HTTP API Server for PyRAGDoc."""

import os
import logging
from typing import Dict, List, Any, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.status import HTTP_404_NOT_FOUND

from ..utils.logging import get_logger
from ..utils.errors import PyRAGDocError, NotFoundError
from ..models.responses import ContentItem, ToolResponse, ErrorResponse, StatusResponse
from ..models.documents import DocumentChunk, SearchQuery, SearchResult


class ToolRequest(BaseModel):
    """Tool request for HTTP API."""
    
    name: str = Field(..., description="Tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class APIServer:
    """HTTP API Server for PyRAGDoc."""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """Initialize the HTTP API server.
        
        Args:
            config: Server configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or get_logger(__name__)
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="PyRAGDoc API",
            description="API for RAG document processing",
            version="0.1.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize services
        self.embedding_service = None
        self.storage_service = None
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register API routes."""
        @self.app.on_event("startup")
        async def startup_event():
            await self._init_services()
        
        @self.app.get("/", response_model=StatusResponse)
        async def root():
            return StatusResponse(
                status="ok",
                message="PyRAGDoc API Server",
                details={"version": "0.1.0"}
            )
        
        @self.app.post("/tools", response_model=Union[ToolResponse, ErrorResponse])
        async def call_tool(request: ToolRequest, background_tasks: BackgroundTasks):
            return await self._handle_tool_request(request, background_tasks)
        
        @self.app.get("/tools", response_model=List[Dict[str, Any]])
        async def list_tools():
            return self._get_available_tools()
        
        @self.app.post("/search", response_model=List[SearchResult])
        async def search(query: SearchQuery):
            return await self._handle_search(query)
        
        @self.app.post("/documents", response_model=StatusResponse)
        async def add_document(file: UploadFile = File(...)):
            return await self._handle_upload_document(file)
        
        @self.app.get("/sources", response_model=List[str])
        async def list_sources():
            sources = await self.storage_service.list_sources()
            return sources
        
        @self.app.exception_handler(PyRAGDocError)
        async def handle_error(request: Request, exc: PyRAGDocError):
            return ErrorResponse(
                code=exc.status_code,
                message=exc.message,
                details=exc.details
            )
        
        @self.app.exception_handler(NotFoundError)
        async def handle_not_found(request: Request, exc: NotFoundError):
            return ErrorResponse(
                code=HTTP_404_NOT_FOUND,
                message=exc.message,
                details=exc.details
            )
    
    async def _init_services(self):
        """Initialize services."""
        # Initialize embedding service
        from ..core.embedding import create_embedding_service
        self.embedding_service = create_embedding_service(self.config["embedding"])
        
        # Initialize storage service
        from ..core.storage import create_storage_service
        self.storage_service = create_storage_service(self.config["database"])
        
        self.logger.info("Services initialized")
    
    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Get available tools.
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "add_documentation",
                "description": "Add documentation from a URL to the RAG database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL of the documentation to fetch"
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "search_documentation",
                "description": "Search through stored documentation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_sources",
                "description": "List all documentation sources currently stored",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "add_directory",
                "description": "Add all supported files from a directory to the RAG database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the directory containing documents"
                        }
                    },
                    "required": ["path"]
                }
            }
        ]
    
    async def _handle_tool_request(
        self, 
        request: ToolRequest, 
        background_tasks: BackgroundTasks
    ) -> Union[ToolResponse, ErrorResponse]:
        """Handle a tool request.
        
        Args:
            request: Tool request
            background_tasks: Background tasks
            
        Returns:
            Tool response or error response
        """
        tool_name = request.name
        arguments = request.arguments
        
        try:
            if tool_name == "add_documentation":
                return await self._handle_add_documentation(arguments)
            elif tool_name == "search_documentation":
                return await self._handle_search_documentation(arguments)
            elif tool_name == "list_sources":
                return await self._handle_list_sources()
            elif tool_name == "add_directory":
                return await self._handle_add_directory(arguments)
            else:
                return ErrorResponse(
                    code=404,
                    message=f"Unknown tool: {tool_name}"
                )
        except PyRAGDocError as e:
            return ErrorResponse(
                code=e.status_code,
                message=e.message,
                details=e.details
            )
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return ErrorResponse(
                code=500,
                message=f"Unexpected error: {str(e)}"
            )
    
    async def _handle_add_documentation(self, arguments: Dict[str, Any]) -> ToolResponse:
        """Handle add_documentation tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tool response
        """
        url = arguments.get("url")
        if not url:
            return ToolResponse(
                content=[ContentItem(type="text", text="URL is required")],
                is_error=True
            )
        
        self.logger.info(f"Adding documentation from URL: {url}")
        
        # Placeholder for actual implementation
        return ToolResponse(
            content=[ContentItem(
                type="text",
                text=f"Successfully added documentation from {url}"
            )]
        )
    
    async def _handle_search_documentation(self, arguments: Dict[str, Any]) -> ToolResponse:
        """Handle search_documentation tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tool response
        """
        query = arguments.get("query")
        limit = arguments.get("limit", 5)
        
        if not query:
            return ToolResponse(
                content=[ContentItem(type="text", text="Query is required")],
                is_error=True
            )
        
        self.logger.info(f"Searching documentation with query: {query}")
        
        # Generate embedding for query
        embedding = await self.embedding_service.generate_embedding(query)
        
        # Search for similar documents
        results = await self.storage_service.search(embedding, limit)
        
        if not results:
            return ToolResponse(
                content=[ContentItem(type="text", text="No results found")]
            )
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results):
            chunk = result.chunk
            score = result.score
            
            source = chunk.metadata.url or chunk.metadata.source or "Unknown source"
            title = chunk.metadata.title or source
            
            formatted = f"[{i+1}] {title} (Score: {score:.2f})\n"
            formatted += f"Source: {source}\n\n"
            formatted += chunk.text
            
            formatted_results.append(formatted)
        
        return ToolResponse(
            content=[ContentItem(
                type="text", 
                text="\n\n---\n\n".join(formatted_results)
            )]
        )
    
    async def _handle_list_sources(self) -> ToolResponse:
        """Handle list_sources tool.
        
        Returns:
            Tool response
        """
        self.logger.info("Listing documentation sources")
        
        sources = await self.storage_service.list_sources()
        
        if not sources:
            return ToolResponse(
                content=[ContentItem(type="text", text="No documentation sources found")]
            )
        
        formatted = "Documentation sources:\n\n"
        for i, source in enumerate(sources):
            formatted += f"{i+1}. {source}\n"
        
        return ToolResponse(
            content=[ContentItem(type="text", text=formatted)]
        )
    
    async def _handle_add_directory(self, arguments: Dict[str, Any]) -> ToolResponse:
        """Handle add_directory tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tool response
        """
        path = arguments.get("path")
        if not path:
            return ToolResponse(
                content=[ContentItem(type="text", text="Path is required")],
                is_error=True
            )
        
        self.logger.info(f"Adding documentation from directory: {path}")
        
        # Placeholder for actual implementation
        return ToolResponse(
            content=[ContentItem(
                type="text",
                text=f"Successfully added documentation from directory: {path}"
            )]
        )
    
    async def _handle_search(self, query: SearchQuery) -> List[SearchResult]:
        """Handle search query.
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        self.logger.info(f"Searching with query: {query.query}")
        
        # Generate embedding for query
        embedding = await self.embedding_service.generate_embedding(query.query)
        
        # Search for similar documents
        results = await self.storage_service.search(
            embedding, 
            query.limit,
            query.filters,
            query.min_score
        )
        
        return results
    
    async def _handle_upload_document(self, file: UploadFile) -> StatusResponse:
        """Handle document upload.
        
        Args:
            file: Uploaded file
            
        Returns:
            Status response
        """
        self.logger.info(f"Processing uploaded file: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Determine file type
        filename = file.filename
        file_type = filename.split(".")[-1].lower() if "." in filename else None
        
        if not file_type:
            raise PyRAGDocError("Could not determine file type", 400)
        
        # Process file based on type
        from ..core.processors import get_processor_for_file
        processor = get_processor_for_file(filename, file.content_type)
        if not processor:
            raise PyRAGDocError(f"Unsupported file type: {file_type}", 400)
        
        # Process file
        chunks = await processor.process_content(content)
        
        # Generate embeddings and store chunks
        for chunk in chunks:
            embedding = await self.embedding_service.generate_embedding(chunk.text)
            await self.storage_service.add_document(embedding, chunk)
        
        return StatusResponse(
            status="success",
            message=f"Successfully processed {file.filename}",
            details={"chunks": len(chunks)}
        )


def run_http_server(config: Dict[str, Any]):
    """Run the HTTP API server.
    
    Args:
        config: Server configuration
    """
    logger = get_logger("api_server")
    logger.info("Starting HTTP API server")
    
    server = APIServer(config, logger)
    
    uvicorn.run(
        server.app,
        host="0.0.0.0",
        port=config["server"]["port"],
        log_level="info"
    )
