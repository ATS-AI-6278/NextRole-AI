from typing import Optional
from app.core.ai_client import AIClient
from app.memory.vector.chroma_client import ChromaClient

# Global Singleton Instances
_ai_client: Optional[AIClient] = None
_chroma_client: Optional[ChromaClient] = None

def get_ai_client() -> AIClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client

def get_chroma_client() -> ChromaClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient()
    return _chroma_client
