import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging
import re
import unicodedata
from core.config import config
from core.types import ToolResult
import uuid
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

def normalize_name(name: str) -> str:
    name = unicodedata.normalize('NFD', name)
    name = name.encode('ascii', 'ignore').decode('utf-8')
    name = name.replace(' ', '_')
    name = re.sub(r'[^A-Za-z0-9_-]', '', name)
    name = name.strip('_-')
    return name[:60]

class VectorDBTool:
    """Tool để làm việc với Vector Database và tránh trùng vector."""

    def __init__(self):
        self.persist_dir = config.CHROMA_PERSIST_DIR
        self.collection_prefix = config.VECTOR_DB_COLLECTION_PREFIX

        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )
        logger.info(f"Initialized ChromaDB at {self.persist_dir}")

    def create_collection(self, collection_name: str, metadata: Optional[Dict[str, Any]] = None) -> ToolResult:
        try:
            safe_name = normalize_name(collection_name)
            full_name = f"{self.collection_prefix}_{safe_name}"
            try:
                existing = self.client.get_collection(name=full_name)
                return ToolResult(success=True, data={'collection_name': full_name, 'already_exists': True})
            except:
                pass

            collection = self.client.create_collection(
                name=full_name,
                metadata=metadata or {"source": "auto_created"}
            )
            logger.info(f"Created collection: {full_name}")
            return ToolResult(success=True, data={'collection_name': full_name})
        except Exception as e:
            logger.error(f"Create collection error: {str(e)}")
            return ToolResult(success=False, error=f"Failed to create collection: {str(e)}")

    def add_documents(
            self,
            collection_name: str,
            documents: List[str],
            embeddings: List[np.ndarray],
            metadatas: Optional[List[Dict[str, Any]]] = None,
            ids: Optional[List[str]] = None,
            similarity_threshold: float = 0.95
    ) -> ToolResult:
        """
        Thêm documents kèm embeddings. Tránh vector trùng dựa trên cosine similarity.
        """
        try:
            safe_name = normalize_name(collection_name)
            full_name = f"{self.collection_prefix}_{safe_name}"
            collection = self.client.get_collection(name=full_name)

            # Lấy embeddings hiện tại
            try:
                existing_embeddings = np.array(collection.get(include=['embeddings'])['embeddings'])
            except:
                existing_embeddings = np.empty((0, len(embeddings[0])))

            filtered_docs = []
            filtered_embeddings = []
            filtered_metas = []
            filtered_ids = []

            for i, emb in enumerate(embeddings):
                skip = False
                if existing_embeddings.size > 0:
                    sims = cosine_similarity([emb], existing_embeddings)[0]
                    if np.max(sims) >= similarity_threshold:
                        logger.debug(f"[VectorDB] Skipping duplicate document {i}")
                        skip = True
                if skip:
                    continue
                filtered_docs.append(documents[i])
                filtered_embeddings.append(emb)
                filtered_metas.append(metadatas[i] if metadatas else {})
                filtered_ids.append(ids[i] if ids else f"doc_{uuid.uuid4().hex}")

            if not filtered_docs:
                return ToolResult(success=True, data={'added_count': 0, 'collection_name': full_name})

            collection.add(
                documents=filtered_docs,
                embeddings=filtered_embeddings,
                metadatas=filtered_metas,
                ids=filtered_ids
            )
            logger.info(f"Added {len(filtered_docs)} documents to {full_name}")
            return ToolResult(success=True, data={'added_count': len(filtered_docs), 'collection_name': full_name,
                                                  'ids': filtered_ids})

        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            return ToolResult(success=False, error=f"Failed to add documents: {str(e)}")

    def search(self, collection_name: str, query_text: str, n_results: int = 10) -> ToolResult:
        try:
            safe_name = normalize_name(collection_name)
            full_name = f"{self.collection_prefix}_{safe_name}"
            collection = self.client.get_collection(name=full_name)
            results = collection.query(query_texts=[query_text], n_results=n_results)

            formatted_results = []
            if results.get('documents'):
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'document': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'id': results['ids'][0][i] if results['ids'] else None,
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })

            return ToolResult(success=True, data={'query': query_text, 'results': formatted_results, 'count': len(formatted_results)})
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return ToolResult(success=False, error=f"Search failed: {str(e)}")

# Singleton instance
vector_db_tool = VectorDBTool()
