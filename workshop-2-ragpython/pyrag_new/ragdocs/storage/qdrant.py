"""Qdrant storage provider for RAGDocs."""

import logging
import uuid
import os
from typing import List, Dict, Any, Optional, Set

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from .base import BaseStorage, Document, SearchResult


class QdrantStorage(BaseStorage):
    """Qdrant storage provider."""
    
    def __init__(
        self, 
        url: str, 
        collection_name: str = None,
        embedding_dimension: int = 1536,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the Qdrant storage provider.
        
        Args:
            url: Qdrant server URL
            collection_name: Collection name
            embedding_dimension: Dimension of embeddings
            logger: Logger instance
        """
        super().__init__(logger)
        self.url = url
        # ใช้ค่าจาก environment variable หรือค่าที่ส่งเข้ามา หรือค่าเริ่มต้น
        self.collection_name = collection_name or os.environ.get("QDRANT_COLLECTION", "ragdocs")
        self.embedding_dimension = embedding_dimension
        
        # Parse URL components
        protocol = "http"
        if "://" in url:
            protocol, url = url.split("://", 1)
        
        host = url
        port = 6333
        if ":" in url:
            host, port_str = url.split(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                self.logger.warning(f"Invalid port number: {port_str}, using default port 6333")
        
        # Create Qdrant client
        self.client = QdrantClient(host=host, port=port, prefix="", timeout=60)
        
        # Ensure collection exists
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure the collection exists and has the correct configuration."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                self.logger.info(f"Creating collection: {self.collection_name}")
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.embedding_dimension,
                        distance=models.Distance.COSINE
                    ),
                    optimizers_config=models.OptimizersConfigDiff(
                        indexing_threshold=0  # Create index immediately
                    )
                )
                
                # Add payload index for source field
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="source",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                
                self.logger.info(f"Collection {self.collection_name} created successfully")
            else:
                self.logger.info(f"Collection {self.collection_name} already exists")
                
                # Check vector configuration
                collection_info = self.client.get_collection(self.collection_name)
                if collection_info.config.params.vectors.size != self.embedding_dimension:
                    self.logger.warning(
                        f"Collection dimension ({collection_info.config.params.vectors.size}) "
                        f"does not match expected dimension ({self.embedding_dimension})"
                    )
        
        except Exception as e:
            self.logger.error(f"Error setting up Qdrant collection: {str(e)}")
            raise
    
    async def add(self, embeddings: List[List[float]], documents: List[Document]) -> None:
        """Add documents with embeddings to Qdrant.
        
        Args:
            embeddings: List of embedding vectors
            documents: List of documents
        """
        if len(embeddings) != len(documents):
            raise ValueError("Number of embeddings must match number of documents")
        
        if not embeddings:
            return
        
        try:
            # Prepare points
            points = []
            for i, (embedding, document) in enumerate(zip(embeddings, documents)):
                # Create payload
                payload = {
                    "text": document.text,
                    "metadata": document.metadata
                }
                
                # Add source field for filtering
                if "url" in document.metadata:
                    payload["source"] = document.metadata["url"]
                elif "source" in document.metadata:
                    payload["source"] = document.metadata["source"]
                
                # Create point
                point_id = str(uuid.uuid4())
                points.append(models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                ))
            
            # Upload in batches of 100
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                
                self.client.upload_points(
                    collection_name=self.collection_name,
                    points=batch
                )
                
                self.logger.info(f"Uploaded batch of {len(batch)} documents to Qdrant")
            
            self.logger.info(f"Successfully added {len(documents)} documents to Qdrant")
            
        except Exception as e:
            self.logger.error(f"Error adding documents to Qdrant: {str(e)}")
            raise
    
    async def search(
        self, 
        embedding: List[float], 
        limit: int = 5, 
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """Search for similar documents in Qdrant.
        
        Args:
            embedding: Query embedding vector
            limit: Maximum number of results
            filters: Optional metadata filters
            min_score: Minimum similarity score
            
        Returns:
            List of search results
        """
        try:
            # Prepare filter
            filter_conditions = None
            if filters:
                filter_conditions = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                        for key, value in filters.items()
                    ]
                )
            
            # Execute search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=limit,
                query_filter=filter_conditions,
                score_threshold=min_score
            )
            
            # Convert to SearchResult objects
            results = []
            for result in search_results:
                # Extract text and metadata
                text = result.payload.get("text", "")
                metadata = result.payload.get("metadata", {})
                
                # Create document
                document = Document(text=text, metadata=metadata)
                
                # Create search result
                search_result = SearchResult(chunk=document, score=result.score)
                results.append(search_result)
            
            return results
        
        except Exception as e:
            self.logger.error(f"Error searching in Qdrant: {str(e)}")
            raise
    
    async def list_sources(self) -> List[str]:
        """List all document sources in Qdrant.
        
        Returns:
            List of source identifiers
        """
        try:
            # Get all unique source values
            response = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=None,
                limit=10000,
                with_payload=["source"],
                with_vectors=False
            )
            
            points = response[0]
            
            # Extract unique sources
            sources = set()
            for point in points:
                source = point.payload.get("source")
                if source:
                    sources.add(source)
            
            return sorted(list(sources))
        
        except Exception as e:
            self.logger.error(f"Error listing sources from Qdrant: {str(e)}")
            raise
