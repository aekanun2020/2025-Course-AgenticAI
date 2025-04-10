"""Storage services for vector database operations."""

import logging
import uuid
from typing import Dict, List, Any, Optional, Set, Union

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from ..utils.logging import get_logger
from ..utils.errors import StorageError
from ..models.documents import DocumentChunk, SearchResult


class StorageService:
    """Base class for storage services."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the storage service.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or get_logger(__name__)
    
    async def initialize(self) -> None:
        """Initialize the storage service.
        
        Raises:
            StorageError: If initialization fails
        """
        pass
    
    async def add_document(self, embedding: List[float], chunk: DocumentChunk) -> None:
        """Add a document chunk to storage.
        
        Args:
            embedding: Document embedding
            chunk: Document chunk
            
        Raises:
            StorageError: If adding document fails
        """
        pass
    
    async def add_documents(self, embeddings: List[List[float]], chunks: List[DocumentChunk]) -> None:
        """Add multiple document chunks to storage.
        
        Args:
            embeddings: Document embeddings
            chunks: Document chunks
            
        Raises:
            StorageError: If adding documents fails
        """
        pass
    
    async def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None
    ) -> List[SearchResult]:
        """Search for similar documents.
        
        Args:
            query_vector: Query vector
            limit: Maximum number of results
            filters: Metadata filters
            min_score: Minimum similarity score
            
        Returns:
            List of search results
            
        Raises:
            StorageError: If search fails
        """
        pass
    
    async def list_sources(self) -> List[str]:
        """List all document sources.
        
        Returns:
            List of source identifiers
            
        Raises:
            StorageError: If listing sources fails
        """
        pass
    
    async def delete_documents(self, filter_conditions: Dict[str, Any]) -> int:
        """Delete documents matching filter.
        
        Args:
            filter_conditions: Filter conditions
            
        Returns:
            Number of deleted documents
            
        Raises:
            StorageError: If deletion fails
        """
        pass


class QdrantService(StorageService):
    """Storage service using Qdrant vector database."""
    
    def __init__(
        self,
        url: str,
        collection_name: str,
        vector_size: int = 768,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the Qdrant storage service.
        
        Args:
            url: Qdrant server URL
            collection_name: Collection name
            vector_size: Vector size
            logger: Logger instance
        """
        super().__init__(logger)
        
        self.url = url
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # Initialize client
        self.client = QdrantClient(url=url)
        
        self.logger.info(f"Initialized Qdrant service with URL: {url}, "
                         f"collection: {collection_name}, vector size: {vector_size}")
    
    async def initialize(self) -> None:
        """Initialize the Qdrant collection.
        
        Raises:
            StorageError: If initialization fails
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_exists = any(c.name == self.collection_name for c in collections.collections)
            
            if not collection_exists:
                # Create collection
                self.logger.info(f"Creating collection '{self.collection_name}' "
                                 f"with vector size {self.vector_size}")
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=self.vector_size,
                        distance=qdrant_models.Distance.COSINE
                    )
                )
                
                self.logger.info(f"Collection '{self.collection_name}' created successfully")
            else:
                # Check vector size
                collection_info = self.client.get_collection(self.collection_name)
                current_vector_size = collection_info.config.params.vectors.size
                
                if current_vector_size != self.vector_size:
                    self.logger.warning(f"Collection '{self.collection_name}' has vector size "
                                       f"{current_vector_size}, but {self.vector_size} is required")
                    
                    # Recreate collection with correct vector size
                    await self.recreate_collection()
        except Exception as e:
            error_msg = f"Failed to initialize Qdrant collection: {str(e)}"
            self.logger.error(error_msg)
            raise StorageError(error_msg)
    
    async def recreate_collection(self) -> None:
        """Recreate the Qdrant collection.
        
        Raises:
            StorageError: If recreation fails
        """
        try:
            # Delete existing collection
            self.logger.info(f"Deleting collection '{self.collection_name}'")
            self.client.delete_collection(collection_name=self.collection_name)
            
            # Create new collection
            self.logger.info(f"Creating collection '{self.collection_name}' "
                             f"with vector size {self.vector_size}")
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=self.vector_size,
                    distance=qdrant_models.Distance.COSINE
                )
            )
            
            self.logger.info(f"Collection '{self.collection_name}' recreated successfully")
        except Exception as e:
            error_msg = f"Failed to recreate Qdrant collection: {str(e)}"
            self.logger.error(error_msg)
            raise StorageError(error_msg)
    
    async def add_document(self, embedding: List[float], chunk: DocumentChunk) -> None:
        """Add a document chunk to Qdrant.
        
        Args:
            embedding: Document embedding
            chunk: Document chunk
            
        Raises:
            StorageError: If adding document fails
        """
        try:
            # Create point - restructure data to have source at root level
            metadata = chunk.metadata.model_dump()
            source = metadata.get("source")
            title = metadata.get("title", "Unknown")
            
            # Create payload with source and title at root level
            payload = {
                "text": chunk.text,
                "timestamp": chunk.timestamp.isoformat(),
                "_type": "DocumentChunk"
            }
            
            # Add source and title to root level if available
            if source:
                payload["source"] = source
            if title:
                payload["title"] = title
                
            # Keep metadata for backward compatibility
            payload["metadata"] = metadata
            
            point = qdrant_models.PointStruct(
                id=chunk.id or str(uuid.uuid4()),
                vector=embedding,
                payload=payload
            )
            
            # Upsert point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
                wait=True
            )
            
            self.logger.debug(f"Added document to Qdrant: {chunk.id}")
        except Exception as e:
            error_msg = f"Failed to add document to Qdrant: {str(e)}"
            self.logger.error(error_msg)
            raise StorageError(error_msg)
    
    async def add_documents(self, embeddings: List[List[float]], chunks: List[DocumentChunk]) -> None:
        """Add multiple document chunks to Qdrant.
        
        Args:
            embeddings: Document embeddings
            chunks: Document chunks
            
        Raises:
            StorageError: If adding documents fails
        """
        try:
            if len(embeddings) != len(chunks):
                raise ValueError("Number of embeddings must match number of chunks")
            
            # Create points with restructured data
            points = []
            for embedding, chunk in zip(embeddings, chunks):
                metadata = chunk.metadata.model_dump()
                source = metadata.get("source")
                title = metadata.get("title", "Unknown")
                
                # Create payload with source and title at root level
                payload = {
                    "text": chunk.text,
                    "timestamp": chunk.timestamp.isoformat(),
                    "_type": "DocumentChunk"
                }
                
                # Add source and title to root level if available
                if source:
                    payload["source"] = source
                if title:
                    payload["title"] = title
                    
                # Keep metadata for backward compatibility
                payload["metadata"] = metadata
                
                points.append(qdrant_models.PointStruct(
                    id=chunk.id or str(uuid.uuid4()),
                    vector=embedding,
                    payload=payload
                ))
            
            # Upsert points
            # Split into batches to avoid hitting size limits
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                    wait=True
                )
                
                self.logger.debug(f"Added batch of {len(batch)} documents to Qdrant")
            
            self.logger.info(f"Added {len(chunks)} documents to Qdrant")
        except Exception as e:
            error_msg = f"Failed to add documents to Qdrant: {str(e)}"
            self.logger.error(error_msg)
            raise StorageError(error_msg)
    
    async def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None
    ) -> List[SearchResult]:
        """Search for similar documents in Qdrant.
        
        Args:
            query_vector: Query vector
            limit: Maximum number of results
            filters: Metadata filters
            min_score: Minimum similarity score
            
        Returns:
            List of search results
            
        Raises:
            StorageError: If search fails
        """
        try:
            # Convert filters to Qdrant filter
            qdrant_filter = None
            if filters:
                # TODO: Implement filter conversion
                pass
            
            # Set score threshold
            score_threshold = min_score or 0.0
            
            # Search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=qdrant_filter,
                score_threshold=score_threshold,
                with_payload=True
            )
            
            # Convert results
            from ..models.documents import DocumentMetadata
            results = []
            
            for result in search_results:
                payload = result.payload
                
                # Extract metadata
                metadata_dict = payload.get("metadata", {})
                metadata = DocumentMetadata(**metadata_dict)
                
                # Create document chunk
                import datetime
                timestamp_str = payload.get("timestamp")
                timestamp = datetime.datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.datetime.now()
                
                chunk = DocumentChunk(
                    text=payload.get("text", ""),
                    metadata=metadata,
                    timestamp=timestamp,
                    id=str(result.id)
                )
                
                # Create search result
                search_result = SearchResult(
                    chunk=chunk,
                    score=result.score
                )
                
                results.append(search_result)
            
            self.logger.info(f"Found {len(results)} results for search query")
            return results
        except Exception as e:
            error_msg = f"Failed to search Qdrant: {str(e)}"
            self.logger.error(error_msg)
            raise StorageError(error_msg)
    
    async def list_sources(self) -> List[str]:
        """List all document sources in Qdrant.
        
        Returns:
            List of source identifiers
            
        Raises:
            StorageError: If listing sources fails
        """
        try:
            # Get all points with payload
            scroll_results = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            
            # ดูเหมือนว่า scroll_results อาจเป็น tuple ซึ่งเปลี่ยนแปลงในเวอร์ชันใหม่ของ Qdrant client
            # รองรับทั้งรูปแบบเดิมและรูปแบบใหม่
            if isinstance(scroll_results, tuple) and len(scroll_results) > 0:
                # รูปแบบใหม่: (points, next_page_offset)
                points = scroll_results[0]
                self.logger.info(f"Received tuple from scroll: {len(points)} points")
            elif hasattr(scroll_results, 'points'):
                # รูปแบบเดิม: object with .points attribute
                points = scroll_results.points
                self.logger.info(f"Received object with points from scroll: {len(points)} points")
            else:
                # ไม่รู้จักรูปแบบ
                self.logger.error(f"Unknown format from scroll: {type(scroll_results)}")
                points = []
            
            # ล็อกข้อมูลเพื่อดีบัก
            self.logger.info(f"Total points found: {len(points)}")
            if len(points) > 0:
                sample_point = points[0]
                self.logger.info(f"First point type: {type(sample_point)}")
                if hasattr(sample_point, 'payload'):
                    self.logger.info(f"First point has payload attribute: {sample_point.payload}")
                elif isinstance(sample_point, dict) and 'payload' in sample_point:
                    self.logger.info(f"First point has payload key: {sample_point['payload']}")
                else:
                    self.logger.info(f"First point has no recognizable payload: {sample_point}")
            
            # Extract sources
            sources = set()
            source_count = 0
            
            for point in points:
                payload = None
                
                # ตรวจสอบรูปแบบของ point และดึง payload
                if hasattr(point, 'payload'):
                    # รูปแบบเก่า: point เป็น object ที่มี attribute payload
                    payload = point.payload
                elif isinstance(point, dict) and 'payload' in point:
                    # รูปแบบใหม่: point เป็น dict ที่มี key payload
                    payload = point['payload']
                else:
                    self.logger.debug(f"Point has unrecognized format: {point}")
                    continue
                
                # ตรวจสอบโดยตรงจาก payload ตามที่เห็นในล็อก
                if isinstance(payload, dict):
                    # ตรวจสอบ source และ url ใน payload โดยตรง
                    source = payload.get('source')
                    url = payload.get('url')
                    
                    if source:
                        sources.add(source)
                        source_count += 1
                        self.logger.debug(f"Found source directly in payload: {source}")
                    elif url:
                        sources.add(url)
                        source_count += 1
                        self.logger.debug(f"Found url directly in payload: {url}")
                elif hasattr(payload, 'source'):
                    source = payload.source
                    sources.add(source)
                    source_count += 1
                    self.logger.debug(f"Found source as attribute in payload: {source}")
                elif hasattr(payload, 'url'):
                    url = payload.url
                    sources.add(url)
                    source_count += 1
                    self.logger.debug(f"Found url as attribute in payload: {url}")
            
            self.logger.info(f"Total sources found: {source_count}")
            return list(sources)
        except Exception as e:
            error_msg = f"Failed to list sources from Qdrant: {str(e)}"
            self.logger.error(error_msg)
            raise StorageError(error_msg)
    
    async def delete_documents(self, filter_conditions: Dict[str, Any]) -> int:
        """Delete documents matching filter from Qdrant.
        
        Args:
            filter_conditions: Filter conditions
            
        Returns:
            Number of deleted documents
            
        Raises:
            StorageError: If deletion fails
        """
        try:
            # Convert filter conditions to Qdrant filter
            qdrant_filter = None
            if filter_conditions:
                # TODO: Implement filter conversion
                pass
            
            # Delete points
            result = self.client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_filter
                ),
                wait=True
            )
            
            self.logger.info(f"Deleted {result.deleted} documents from Qdrant")
            return result.deleted
        except Exception as e:
            error_msg = f"Failed to delete documents from Qdrant: {str(e)}"
            self.logger.error(error_msg)
            raise StorageError(error_msg)


def create_storage_service(config: Dict[str, Any]) -> StorageService:
    """Create a storage service from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Storage service
        
    Raises:
        StorageError: If configuration is invalid
    """
    logger = get_logger("storage")
    
    service_type = "qdrant"  # Currently only Qdrant is supported
    
    if service_type == "qdrant":
        url = config.get("url", "http://localhost:6333")
        collection_name = config.get("collection", "documentation")
        
        logger.info(f"Creating QdrantService with URL: {url}, collection: {collection_name}")
        return QdrantService(
            url=url,
            collection_name=collection_name,
            # Vector size will be set later when embedding service is initialized
            logger=logger
        )
    else:
        raise StorageError(f"Unknown storage service type: {service_type}")
