"""
Memory Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..memory_client import memory_client, ConversationEntry, search_memory, get_conversation_context
from ..config import USE_MEMORY_SYSTEM

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memory", tags=["memory"])

@router.get("/status")
async def get_memory_status():
    """Get memory system status"""
    if not USE_MEMORY_SYSTEM:
        return {"enabled": False, "message": "Memory system is disabled"}
    
    try:
        # Get some basic stats
        conversations_count = memory_client.conversations_collection.count()
        return {
            "enabled": True,
            "conversations_stored": conversations_count,
            "storage_path": str(memory_client.memory_dir),
            "status": "operational"
        }
    except Exception as e:
        logger.error(f"Error getting memory status: {e}")
        return {"enabled": True, "status": "error", "message": str(e)}

@router.get("/conversation/{participant1}/{participant2}")
async def get_conversation_history(
    participant1: str,
    participant2: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Get conversation history between two participants"""
    if not USE_MEMORY_SYSTEM:
        raise HTTPException(status_code=503, detail="Memory system is disabled")
    
    try:
        history = await memory_client.get_conversation_history([participant1, participant2], limit)
        return {
            "participants": [participant1, participant2],
            "message_count": len(history),
            "history": [entry.to_dict() for entry in history]
        }
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation history: {str(e)}")

@router.get("/context/{sender}/{recipient}")
async def get_conversation_context_endpoint(sender: str, recipient: str):
    """Get conversation context for two participants"""
    if not USE_MEMORY_SYSTEM:
        raise HTTPException(status_code=503, detail="Memory system is disabled")
    
    try:
        context = await get_conversation_context(sender, recipient)
        return context
    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation context: {str(e)}")

@router.get("/search")
async def search_conversations(
    query: str,
    limit: int = Query(10, ge=1, le=50)
):
    """Search conversations by content"""
    if not USE_MEMORY_SYSTEM:
        raise HTTPException(status_code=503, detail="Memory system is disabled")
    
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        results = await search_memory(query, limit)
        return {
            "query": query,
            "result_count": len(results),
            "results": [entry.to_dict() for entry in results]
        }
    except Exception as e:
        logger.error(f"Error searching conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_memories(days_to_keep: int = Query(90, ge=1, le=365)):
    """Clean up old conversation memories"""
    if not USE_MEMORY_SYSTEM:
        raise HTTPException(status_code=503, detail="Memory system is disabled")
    
    try:
        await memory_client.cleanup_old_memories(days_to_keep)
        return {
            "message": f"Memory cleanup initiated for conversations older than {days_to_keep} days",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error during memory cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@router.get("/stats")
async def get_memory_statistics():
    """Get detailed memory system statistics"""
    if not USE_MEMORY_SYSTEM:
        raise HTTPException(status_code=503, detail="Memory system is disabled")
    
    try:
        # Query collections for stats
        conversations_count = memory_client.conversations_collection.count()
        
        # Get medium distribution
        results = memory_client.conversations_collection.query(
            n_results=min(1000, conversations_count) if conversations_count > 0 else 1
        )
        
        mediums = {}
        if results and results['metadatas']:
            for metadata in results['metadatas']:
                medium = metadata.get('medium', 'unknown')
                mediums[medium] = mediums.get(medium, 0) + 1
        
        return {
            "total_conversations": conversations_count,
            "medium_distribution": mediums,
            "storage_path": str(memory_client.memory_dir),
            "collections": {
                "conversations": conversations_count,
                "context": memory_client.context_collection.count()
            }
        }
    except Exception as e:
        logger.error(f"Error getting memory statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")