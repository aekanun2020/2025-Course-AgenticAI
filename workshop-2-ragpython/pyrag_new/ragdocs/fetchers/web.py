"""Web content fetcher for RAGDocs."""

import logging
import re
from typing import List, Dict, Any, Optional

import aiohttp
from bs4 import BeautifulSoup

from ..storage import Document


class WebFetcher:
    """Fetcher for web content."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the web fetcher.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    async def fetch(self, url: str) -> Optional[str]:
        """Fetch content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if fetch failed
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 RAGDocs Bot"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to fetch {url}, status: {response.status}")
                        return None
                    
                    content = await response.text()
                    self.logger.info(f"Successfully fetched {url}, size: {len(content)} bytes")
                    return content
        
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP error when fetching {url}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching {url}: {str(e)}")
            return None
    
    async def process(self, content: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """Process HTML content into document chunks.
        
        Args:
            content: HTML content
            metadata: Additional metadata
            
        Returns:
            List of document chunks
        """
        try:
            if not content:
                return []
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
            
            # Extract text
            text = soup.get_text(separator="\n")
            
            # Clean up text
            text = re.sub(r'\n+', '\n', text)  # Replace multiple newlines
            text = re.sub(r'\s+', ' ', text)   # Replace multiple spaces
            text = text.strip()
            
            if not text:
                return []
            
            # Default metadata
            if metadata is None:
                metadata = {}
            
            # Try to extract title
            title_tag = soup.find('title')
            if title_tag and title_tag.text and 'title' not in metadata:
                metadata['title'] = title_tag.text.strip()
            
            # Split into chunks (4000 characters each)
            chunk_size = 4000
            chunks = []
            
            # Simple chunking by size
            for i in range(0, len(text), chunk_size):
                chunk_text = text[i:i+chunk_size]
                
                # Create document
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = len(chunks)
                chunks.append(Document(text=chunk_text, metadata=chunk_metadata))
            
            self.logger.info(f"Processed HTML into {len(chunks)} chunks")
            return chunks
        
        except Exception as e:
            self.logger.error(f"Error processing HTML: {str(e)}")
            return []
