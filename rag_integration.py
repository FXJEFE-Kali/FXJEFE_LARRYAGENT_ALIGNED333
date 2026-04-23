#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║  🧠 RAG Integration Module                                                 ║
║  ═══════════════════════════════════════════════════════════════════════  ║
║  Provides RAG (Retrieval Augmented Generation) capabilities for all       ║
║  agent tasks including Telegram bot and CLI agent.                        ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import os
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# 📦 IMPORTS
# ═══════════════════════════════════════════════════════════════════════════

try:
    from production_rag import ProductionRAG, get_rag
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger.warning("⚠️ RAG dependencies not available - basic RAG disabled")


# ═══════════════════════════════════════════════════════════════════════════
# 🧠 RAG MANAGER
# ═══════════════════════════════════════════════════════════════════════════


class RAGManager:
    """
    Unified RAG manager for all agent tasks.
    Provides context retrieval, memory storage, and conversation enhancement.
    Supports ChromaDB (local files) and PostgreSQL (PGVector).
    """

    def __init__(self, persist_directory: str = None, backend: str = None, db_config: str = None):
        """
        Initialize RAG manager.
        Backend: 'chroma' or 'postgres' (defaults to 'chroma' if not set)
        """
        self.persist_directory = persist_directory or self._get_default_path()
        self.backend = "chroma"  # Only chroma supported via production_rag
        self.db_config = db_config
        self.rag = None
        self.initialized = False

        self._initialize()

    def _get_default_path(self) -> str:
        """Get default ChromaDB path."""
        # Try to find the LarryLinux directory
        base_paths = [
            Path("Y:/LarryLocalLLM-Agents/LarryLinux/chroma_db"),
            Path("./chroma_db"),
            Path.home() / ".larry_agent" / "chroma_db",
        ]

        for path in base_paths:
            if path.exists():
                return str(path)

        # Default to current directory
        return "./chroma_db"

    def _initialize(self):
        """Initialize RAG components."""
        if not RAG_AVAILABLE:
            logger.warning("RAG not available - running without memory")
            return

        try:
            self.rag = ProductionRAG(chroma_path=self.persist_directory)
            self.initialized = True
            stats = self.get_stats()
            total = sum(stats.get("collections", {}).values())
            logger.info(f"✅ RAG Ready: {total} documents")
        except Exception as e:
            logger.error(f"❌ RAG initialization failed: {e}")
            self.initialized = False

    def get_relevant_context(self, query: str, max_results: int = 2) -> str:
        """Get relevant context using hybrid search + reranker."""
        if not self.initialized:
            return ""

        try:
            hits = self.rag.hybrid_search(query, k=max_results * 3, final_k=max_results)
            contexts = []
            for h in hits:
                score = h.get('rerank_score', h.get('score', 0))
                if score < 0.3:
                    continue
                source = h.get('metadata', {}).get('source', 'memory')
                contexts.append(f"[{source}]: {h['content'][:500]}")
            return "\n\n---\n\n".join(contexts)
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return ""

    def store_conversation(
        self, user_message: str, assistant_response: str, metadata: Dict = None
    ) -> bool:
        """Store a conversation exchange in RAG memory."""
        if not self.initialized:
            return False

        try:
            conv_collection = getattr(self.rag, 'conv_collection', None)
            if not conv_collection:
                return False
            content = f"Q: {user_message}\nA: {assistant_response[:500]}"
            doc_id = f"conv_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            meta = {"source": "conversation", "timestamp": datetime.now().isoformat()}
            if metadata:
                meta.update(metadata)
            conv_collection.add(documents=[content], ids=[doc_id], metadatas=[meta])
            return True
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            return False

    def store_document(self, content: str, metadata: Dict = None) -> bool:
        """Store a document in ChromaDB knowledge base."""
        if not self.initialized:
            return False

        try:
            kb_collection = getattr(self.rag, 'kb_collection', None)
            if not kb_collection:
                return False
            doc_id = f"doc_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            meta = {"source": "manual", "timestamp": datetime.now().isoformat()}
            if metadata:
                meta.update(metadata)
            kb_collection.add(documents=[content], ids=[doc_id], metadatas=[meta])
            return True
        except Exception as e:
            logger.error(f"Error storing document: {e}")
            return False

    def index_file(self, file_path: str) -> bool:
        """Index a single file."""
        if not self.initialized:
            return False
        try:
            self.rag.index_file(file_path)
            return True
        except Exception as e:
            logger.error(f"Error indexing file: {e}")
            return False

    def index_directory(self, directory: str) -> Dict:
        """Index all files in a directory."""
        if not self.initialized:
            return {"indexed_count": 0, "files": [], "errors": ["RAG not initialized"]}
        try:
            result = self.rag.index_directory(directory)
            # production_rag returns {'indexed': N, ...} — normalise key
            count = result.get('indexed', result.get('indexed_count', 0))
            return {"indexed_count": count, "files": [], "errors": []}
        except Exception as e:
            logger.error(f"Error indexing directory: {e}")
            return {"indexed_count": 0, "files": [], "errors": [str(e)]}

    def search_files(self, query: str, file_types: List[str] = None) -> Dict:
        """Search indexed files."""
        if not self.initialized:
            return {"documents": [], "metadatas": [], "distances": []}
        try:
            hits = self.rag.hybrid_search(query, k=10, final_k=5)
            return {
                "documents": [h['content'] for h in hits],
                "metadatas": [h.get('metadata', {}) for h in hits],
                "distances": [1 - h.get('rerank_score', h.get('score', 0)) for h in hits],
            }
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return {"documents": [], "metadatas": [], "distances": []}

    def get_stats(self) -> Dict:
        """Get RAG statistics."""
        if not self.initialized or not self.rag:
            return {"status": "inactive", "collections": {}, "total_documents": 0}
        try:
            raw = self.rag.get_stats()
            # production_rag returns {'status', 'reranker', 'collections': {...}, 'total_documents': N}
            collections = raw.get("collections", {})
            return {
                "status": raw.get("status", "active"),
                "backend": "chroma",
                "collections": collections,
                "total_documents": raw.get("total_documents", sum(collections.values())),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def build_enhanced_prompt(
        self,
        user_query: str,
        system_prompt: str,
        conversation_context: str = "",
        max_rag_tokens: int = 1000,
    ) -> str:
        """
        Build an enhanced prompt with RAG context.

        Args:
            user_query: The user's current query
            system_prompt: The system/role prompt
            conversation_context: Recent conversation history
            max_rag_tokens: Maximum tokens for RAG context

        Returns:
            Enhanced prompt string with relevant context
        """
        # Get relevant RAG context
        rag_context = self.get_relevant_context(user_query)

        # Truncate if too long (rough estimate: 4 chars per token)
        max_chars = max_rag_tokens * 4
        if len(rag_context) > max_chars:
            rag_context = rag_context[:max_chars] + "..."

        # Build the prompt
        parts = [system_prompt]

        if rag_context:
            parts.append(f"\n📚 Relevant Knowledge:\n{rag_context}")

        if conversation_context:
            parts.append(f"\n💬 Recent Conversation:\n{conversation_context}")

        parts.append(f"\n👤 User: {user_query}\n\n🤖 Assistant:")

        return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# 🏭 SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════

_rag_manager: Optional[RAGManager] = None


def get_rag_manager(
    persist_directory: str = None, backend: str = None, db_config: str = None
) -> RAGManager:
    """Get or create the RAG manager singleton."""
    global _rag_manager

    if _rag_manager is None:
        _rag_manager = RAGManager(persist_directory, backend, db_config)

    return _rag_manager


# ═══════════════════════════════════════════════════════════════════════════
# 🧪 TESTING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🧠 RAG Integration Test")
    print("=" * 60)

    # Initialize
    rag = get_rag_manager()

    # Show stats
    stats = rag.get_stats()
    print(f"\n📊 RAG Status: {stats['status']}")

    if stats.get("collections"):
        print("\n📁 Collections:")
        for name, count in stats["collections"].items():
            print(f"  • {name}: {count} documents")

    # Test context retrieval
    print("\n🔍 Testing context retrieval...")
    context = rag.get_relevant_context("python telegram bot")
    if context:
        print(f"  Found relevant context ({len(context)} chars)")
        print(f"  Preview: {context[:200]}...")
    else:
        print("  No relevant context found")

    # Test enhanced prompt
    print("\n📝 Testing enhanced prompt...")
    prompt = rag.build_enhanced_prompt(
        user_query="How do I create a Telegram bot?",
        system_prompt="You are Larry, a helpful AI assistant.",
        conversation_context="User asked about Python earlier.",
    )
    print(f"  Prompt length: {len(prompt)} chars")

    print("\n✅ RAG Integration test complete!")
