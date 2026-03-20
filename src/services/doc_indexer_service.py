"""
Documentation Indexer Service - Indexes markdown docs to ES for semantic search.

Provides:
- Markdown parsing with heading-based chunking
- ES index creation with semantic_text field
- Semantic search for help chat RAG
- Index status checking

Index: vulcan-help-docs
Field: content (semantic_text with .elser-2-elastic inference)
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass

from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class IndexingResult:
    """Result of documentation indexing operation."""
    success: bool
    documents_indexed: int
    total_chunks: int
    errors: List[str]
    duration_seconds: float


@dataclass
class DocChunk:
    """A chunk of documentation for indexing."""
    doc_path: str
    doc_title: str
    section_title: str
    section_level: int
    content: str
    content_preview: str
    doc_category: str


class DocIndexerService:
    """
    Service for indexing Elastic Demo Builder documentation to Elasticsearch.

    Uses semantic_text field type with ELSER for embeddings.
    Chunks documents by markdown headings for semantic coherence.
    """

    INDEX_NAME = "vulcan-help-docs"
    BATCH_SIZE = 16  # ELSER limit for semantic_text batches

    # Directories to index (relative to project root)
    DOC_DIRECTORIES = [
        "docs",
        "docs/esql"
    ]

    # Files to skip
    SKIP_PATTERNS = [
        "archive/",
        "CHANGELOG",
        "LICENSE"
    ]

    # Category mappings based on path/filename
    CATEGORY_MAPPINGS = {
        "esql/": "esql",
        "RAG_": "architecture",
        "QUICK_START": "guide",
        "DEVELOPER_": "guide",
        "MODULAR_": "architecture",
        "API_": "api",
        "ESQL_COMPLETE": "esql",
        "ESQL_PATTERNS": "esql",
        "ERROR_": "troubleshooting",
        "INTEGER_DIVISION": "esql",
        "NULL_HANDLING": "esql",
        "DATA_QUERY": "architecture",
        "TWO_TIER": "architecture"
    }

    def __init__(self):
        """Initialize the doc indexer service."""
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Elasticsearch client from environment variables."""
        try:
            cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID") or os.getenv("ELASTIC_CLOUD_ID")
            api_key = os.getenv("ELASTICSEARCH_API_KEY") or os.getenv("ELASTIC_API_KEY")

            if not cloud_id or not api_key:
                logger.warning("Missing ES credentials - doc indexer unavailable")
                return

            self._client = Elasticsearch(
                cloud_id=cloud_id,
                api_key=api_key,
                request_timeout=60
            )

            # Test connection
            info = self._client.info()
            logger.info(f"Doc indexer connected to ES cluster: {info['cluster_name']}")

        except Exception as e:
            logger.error(f"Failed to initialize ES client for doc indexer: {e}")
            self._client = None

    def is_available(self) -> bool:
        """Check if the doc indexer service is available."""
        return self._client is not None

    def check_index_exists(self) -> bool:
        """Check if the documentation index exists and has documents."""
        if not self._client:
            return False

        try:
            if not self._client.indices.exists(index=self.INDEX_NAME):
                return False

            # Check if it has documents
            count = self._client.count(index=self.INDEX_NAME)
            return count.get('count', 0) > 0

        except Exception as e:
            logger.warning(f"Error checking index existence: {e}")
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the documentation index."""
        if not self._client:
            return {"exists": False, "count": 0}

        try:
            if not self._client.indices.exists(index=self.INDEX_NAME):
                return {"exists": False, "count": 0}

            count = self._client.count(index=self.INDEX_NAME)

            # Get category distribution
            cat_agg = self._client.search(
                index=self.INDEX_NAME,
                size=0,
                aggs={
                    "categories": {
                        "terms": {"field": "doc_category"}
                    }
                }
            )

            categories = {}
            for bucket in cat_agg.get("aggregations", {}).get("categories", {}).get("buckets", []):
                categories[bucket["key"]] = bucket["doc_count"]

            return {
                "exists": True,
                "count": count.get('count', 0),
                "categories": categories
            }

        except Exception as e:
            logger.warning(f"Error getting index stats: {e}")
            return {"exists": False, "count": 0, "error": str(e)}

    def index_documentation(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> IndexingResult:
        """
        Index all documentation to Elasticsearch.

        Args:
            progress_callback: Optional callback(percentage, message) for progress updates

        Returns:
            IndexingResult with success status and statistics
        """
        import time
        start_time = time.time()
        errors = []

        if not self._client:
            return IndexingResult(
                success=False,
                documents_indexed=0,
                total_chunks=0,
                errors=["Elasticsearch client not available"],
                duration_seconds=0
            )

        if progress_callback:
            progress_callback(0, "Parsing documentation files...")

        # Step 1: Parse all documentation files into chunks
        chunks = self._parse_all_documentation()

        if not chunks:
            return IndexingResult(
                success=False,
                documents_indexed=0,
                total_chunks=0,
                errors=["No documentation files found to index"],
                duration_seconds=time.time() - start_time
            )

        logger.info(f"Parsed {len(chunks)} documentation chunks")

        if progress_callback:
            progress_callback(10, f"Creating index {self.INDEX_NAME}...")

        # Step 2: Create or recreate the index
        try:
            self._create_index()
        except Exception as e:
            error_msg = f"Failed to create index: {e}"
            logger.error(error_msg)
            return IndexingResult(
                success=False,
                documents_indexed=0,
                total_chunks=len(chunks),
                errors=[error_msg],
                duration_seconds=time.time() - start_time
            )

        if progress_callback:
            progress_callback(20, f"Indexing {len(chunks)} documentation chunks...")

        # Step 3: Index documents in batches
        indexed_count = 0
        total_chunks = len(chunks)

        for i in range(0, total_chunks, self.BATCH_SIZE):
            batch = chunks[i:i + self.BATCH_SIZE]

            try:
                # Bulk index the batch
                operations = []
                for chunk in batch:
                    operations.append({"index": {"_index": self.INDEX_NAME}})
                    operations.append({
                        "doc_path": chunk.doc_path,
                        "doc_title": chunk.doc_title,
                        "section_title": chunk.section_title,
                        "section_level": chunk.section_level,
                        "content": chunk.content,
                        "content_preview": chunk.content_preview,
                        "doc_category": chunk.doc_category,
                        "indexed_at": datetime.utcnow().isoformat()
                    })

                resp = self._client.bulk(operations=operations, refresh=False)
                if not resp.get("errors"):
                    indexed_count += len(batch)
                else:
                    # Count successes individually
                    for item in resp.get("items", []):
                        if item.get("index", {}).get("status") in (200, 201):
                            indexed_count += 1

            except Exception as e:
                error_msg = f"Batch indexing error at {i}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

            # Update progress
            if progress_callback:
                pct = 20 + int((indexed_count / total_chunks) * 70)
                progress_callback(pct, f"Indexed {indexed_count}/{total_chunks} chunks...")

        # Step 4: Refresh index
        if progress_callback:
            progress_callback(95, "Finalizing index...")

        try:
            self._client.indices.refresh(index=self.INDEX_NAME)
        except Exception as e:
            errors.append(f"Index refresh warning: {e}")

        duration = time.time() - start_time

        if progress_callback:
            progress_callback(100, f"Indexing complete! {indexed_count} chunks indexed.")

        logger.info(f"Documentation indexing complete: {indexed_count}/{total_chunks} in {duration:.1f}s")

        return IndexingResult(
            success=indexed_count > 0,
            documents_indexed=indexed_count,
            total_chunks=total_chunks,
            errors=errors,
            duration_seconds=duration
        )

    def _create_index(self):
        """Create the documentation index with semantic_text mapping."""
        # Delete existing index if present
        if self._client.indices.exists(index=self.INDEX_NAME):
            self._client.indices.delete(index=self.INDEX_NAME)
            logger.info(f"Deleted existing index: {self.INDEX_NAME}")

        # Create index with semantic_text field
        # On EIS Serverless, semantic_text auto-uses .elser-2-elastic
        mapping = {
            "settings": {
                "index": {
                    "mode": "lookup"
                }
            },
            "mappings": {
                "properties": {
                    "doc_path": {"type": "keyword"},
                    "doc_title": {"type": "keyword"},
                    "section_title": {"type": "keyword"},
                    "section_level": {"type": "integer"},
                    "content": {
                        "type": "semantic_text"
                        # inference_id auto-detected on EIS Serverless
                    },
                    "content_preview": {"type": "text"},
                    "doc_category": {"type": "keyword"},
                    "indexed_at": {"type": "date"}
                }
            }
        }

        self._client.indices.create(index=self.INDEX_NAME, body=mapping)
        logger.info(f"Created index: {self.INDEX_NAME}")

    def _parse_all_documentation(self) -> List[DocChunk]:
        """Parse all documentation files into chunks."""
        chunks = []
        project_root = self._get_project_root()

        for doc_dir in self.DOC_DIRECTORIES:
            dir_path = project_root / doc_dir
            if not dir_path.exists():
                continue

            # Find all markdown files
            for md_file in dir_path.glob("*.md"):
                # Skip archived/excluded files
                file_str = str(md_file)
                if any(pattern in file_str for pattern in self.SKIP_PATTERNS):
                    continue

                try:
                    file_chunks = self._chunk_markdown(md_file)
                    chunks.extend(file_chunks)
                except Exception as e:
                    logger.warning(f"Error parsing {md_file}: {e}")

        return chunks

    def _chunk_markdown(self, file_path: Path) -> List[DocChunk]:
        """
        Parse a markdown file into chunks split by headings.

        Chunking strategy:
        - Split on ## and ### headings
        - Each chunk is 500-1500 chars (adjust for semantic coherence)
        - Preserve heading hierarchy for context
        """
        chunks = []

        content = file_path.read_text(encoding='utf-8')

        # Extract doc title from first # heading or filename
        doc_title = self._extract_doc_title(content, file_path)
        doc_category = self._categorize_doc(file_path)
        relative_path = str(file_path.relative_to(self._get_project_root()))

        # Split by headings (## or ###)
        # Pattern captures the heading level and title
        heading_pattern = r'^(#{2,3})\s+(.+)$'

        sections = []
        current_section = {
            "title": doc_title,
            "level": 1,
            "content": []
        }

        for line in content.split('\n'):
            match = re.match(heading_pattern, line)
            if match:
                # Save previous section if it has content
                if current_section["content"]:
                    sections.append(current_section.copy())

                # Start new section
                level = len(match.group(1))
                title = match.group(2).strip()
                current_section = {
                    "title": title,
                    "level": level,
                    "content": []
                }
            else:
                current_section["content"].append(line)

        # Don't forget the last section
        if current_section["content"]:
            sections.append(current_section)

        # Convert sections to chunks
        for section in sections:
            section_content = '\n'.join(section["content"]).strip()

            # Skip empty or very short sections
            if len(section_content) < 50:
                continue

            # Create chunk
            chunk = DocChunk(
                doc_path=relative_path,
                doc_title=doc_title,
                section_title=section["title"],
                section_level=section["level"],
                content=section_content[:3000],  # Limit content length
                content_preview=section_content[:200],
                doc_category=doc_category
            )
            chunks.append(chunk)

        return chunks

    def _extract_doc_title(self, content: str, file_path: Path) -> str:
        """Extract document title from content or filename."""
        # Try to find # Title at start
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Fall back to filename
        return file_path.stem.replace('_', ' ').replace('-', ' ').title()

    def _categorize_doc(self, file_path: Path) -> str:
        """Categorize document based on path and filename."""
        path_str = str(file_path)

        for pattern, category in self.CATEGORY_MAPPINGS.items():
            if pattern in path_str:
                return category

        return "general"

    def _get_project_root(self) -> Path:
        """Get the project root directory."""
        # Navigate up from src/services to project root
        return Path(__file__).parent.parent.parent

    def search_docs(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documentation using semantic search.

        Args:
            query: Natural language search query
            limit: Maximum number of results
            category: Optional category filter (esql, architecture, guide, api)

        Returns:
            List of matching document chunks with scores
        """
        if not self._client:
            logger.warning("ES client not available for doc search")
            return []

        if not self.check_index_exists():
            logger.warning("Documentation index does not exist")
            return []

        try:
            # Build query - simple match on semantic_text field
            query_body = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"content": query}}
                        ]
                    }
                },
                "size": limit,
                "_source": [
                    "doc_path", "doc_title", "section_title",
                    "content_preview", "doc_category"
                ]
            }

            # Add category filter if specified
            if category:
                query_body["query"]["bool"]["filter"] = [
                    {"term": {"doc_category": category}}
                ]

            response = self._client.search(index=self.INDEX_NAME, body=query_body)

            results = []
            for hit in response.get("hits", {}).get("hits", []):
                result = {
                    "score": hit.get("_score", 0),
                    "doc_title": hit["_source"].get("doc_title", ""),
                    "section_title": hit["_source"].get("section_title", ""),
                    "content_preview": hit["_source"].get("content_preview", ""),
                    "doc_category": hit["_source"].get("doc_category", ""),
                    "doc_path": hit["_source"].get("doc_path", "")
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Documentation search error: {e}")
            return []

    def delete_index(self) -> bool:
        """Delete the documentation index."""
        if not self._client:
            return False

        try:
            if self._client.indices.exists(index=self.INDEX_NAME):
                self._client.indices.delete(index=self.INDEX_NAME)
                logger.info(f"Deleted index: {self.INDEX_NAME}")
            return True
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            return False


# Singleton instance
_doc_indexer_instance: Optional[DocIndexerService] = None


def get_doc_indexer() -> DocIndexerService:
    """Get or create the doc indexer service singleton."""
    global _doc_indexer_instance
    if _doc_indexer_instance is None:
        _doc_indexer_instance = DocIndexerService()
    return _doc_indexer_instance
