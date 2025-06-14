"""
Knowledge Base API endpoint for the AI Handyman Secretary Assistant.
Handles procedures, FAQs, and knowledge search through the KnowledgeBaseAgent.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()

# Pydantic models for knowledge base
class ProcedureCreate(BaseModel):
    name: str
    description: str
    estimated_time_minutes: int
    required_tools: List[str]
    price: float

class ProcedureUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    estimated_time_minutes: Optional[int] = None
    required_tools: Optional[List[str]] = None
    price: Optional[float] = None

class ProcedureResponse(BaseModel):
    id: str
    name: str
    description: str
    estimated_time_minutes: int
    required_tools: List[str]
    price: float

class FAQCreate(BaseModel):
    question: str
    answer: str
    category: str = "general"

class FAQResponse(BaseModel):
    id: str
    question: str
    answer: str
    category: str

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class SearchResult(BaseModel):
    type: str  # procedure, faq
    id: str
    title: str
    content: str
    relevance_score: float

class InteractionRequest(BaseModel):
    client_id: str
    question: str
    context: Optional[Dict[str, Any]] = None

# In-memory storage
procedures_db = {}
faqs_db = {}
interactions_db = {}

@router.post("/knowledge/procedures", response_model=ProcedureResponse)
async def create_procedure(procedure: ProcedureCreate):
    """Create a new procedure."""
    procedure_id = str(uuid.uuid4())
    
    procedure_data = {
        "id": procedure_id,
        "name": procedure.name,
        "description": procedure.description,
        "estimated_time_minutes": procedure.estimated_time_minutes,
        "required_tools": procedure.required_tools,
        "price": procedure.price
    }
    
    procedures_db[procedure_id] = procedure_data
    return ProcedureResponse(**procedure_data)

@router.get("/knowledge/procedures", response_model=List[ProcedureResponse])
async def list_procedures():
    """List all procedures."""
    return [ProcedureResponse(**proc) for proc in procedures_db.values()]

@router.get("/knowledge/procedures/{procedure_id}", response_model=ProcedureResponse)
async def get_procedure(procedure_id: str):
    """Get a specific procedure."""
    if procedure_id not in procedures_db:
        raise HTTPException(status_code=404, detail="Procedure not found")
    
    return ProcedureResponse(**procedures_db[procedure_id])

@router.put("/knowledge/procedures/{procedure_id}", response_model=ProcedureResponse)
async def update_procedure(procedure_id: str, procedure_update: ProcedureUpdate):
    """Update a procedure."""
    if procedure_id not in procedures_db:
        raise HTTPException(status_code=404, detail="Procedure not found")
    
    procedure_data = procedures_db[procedure_id]
    
    # Update fields that are provided
    update_data = procedure_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        procedure_data[field] = value
    
    procedures_db[procedure_id] = procedure_data
    return ProcedureResponse(**procedure_data)

@router.delete("/knowledge/procedures/{procedure_id}")
async def delete_procedure(procedure_id: str):
    """Delete a procedure."""
    if procedure_id not in procedures_db:
        raise HTTPException(status_code=404, detail="Procedure not found")
    
    del procedures_db[procedure_id]
    return {"message": "Procedure deleted successfully"}

@router.post("/knowledge/faqs", response_model=FAQResponse)
async def create_faq(faq: FAQCreate):
    """Create a new FAQ."""
    faq_id = str(uuid.uuid4())
    
    faq_data = {
        "id": faq_id,
        "question": faq.question,
        "answer": faq.answer,
        "category": faq.category
    }
    
    faqs_db[faq_id] = faq_data
    return FAQResponse(**faq_data)

@router.get("/knowledge/faqs", response_model=List[FAQResponse])
async def list_faqs(category: Optional[str] = None):
    """List all FAQs, optionally filtered by category."""
    faqs = list(faqs_db.values())
    
    if category:
        faqs = [faq for faq in faqs if faq["category"] == category]
    
    return [FAQResponse(**faq) for faq in faqs]

@router.get("/knowledge/faqs/{faq_id}", response_model=FAQResponse)
async def get_faq(faq_id: str):
    """Get a specific FAQ."""
    if faq_id not in faqs_db:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    return FAQResponse(**faqs_db[faq_id])

@router.delete("/knowledge/faqs/{faq_id}")
async def delete_faq(faq_id: str):
    """Delete an FAQ."""
    if faq_id not in faqs_db:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    del faqs_db[faq_id]
    return {"message": "FAQ deleted successfully"}

@router.post("/knowledge/search", response_model=List[SearchResult])
async def search_knowledge(search_request: SearchRequest):
    """Search the knowledge base."""
    query = search_request.query.lower()
    results = []
    
    # Search procedures
    for proc_id, proc in procedures_db.items():
        relevance = 0
        if query in proc["name"].lower():
            relevance += 0.8
        if query in proc["description"].lower():
            relevance += 0.6
        
        if relevance > 0:
            results.append(SearchResult(
                type="procedure",
                id=proc_id,
                title=proc["name"],
                content=proc["description"],
                relevance_score=relevance
            ))
    
    # Search FAQs
    for faq_id, faq in faqs_db.items():
        relevance = 0
        if query in faq["question"].lower():
            relevance += 0.9
        if query in faq["answer"].lower():
            relevance += 0.7
        
        if relevance > 0:
            results.append(SearchResult(
                type="faq",
                id=faq_id,
                title=faq["question"],
                content=faq["answer"],
                relevance_score=relevance
            ))
    
    # Sort by relevance and limit results
    results.sort(key=lambda x: x.relevance_score, reverse=True)
    return results[:search_request.limit]

@router.post("/knowledge/learn")
async def learn_from_interaction(interaction: InteractionRequest):
    """Learn from a client interaction."""
    interaction_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    interaction_data = {
        "id": interaction_id,
        "client_id": interaction.client_id,
        "question": interaction.question,
        "context": interaction.context or {},
        "timestamp": now
    }
    
    interactions_db[interaction_id] = interaction_data
    
    # Check if this question should become an FAQ
    question_lower = interaction.question.lower()
    existing_faq = None
    
    for faq in faqs_db.values():
        if question_lower in faq["question"].lower() or faq["question"].lower() in question_lower:
            existing_faq = faq
            break
    
    if not existing_faq and len(interaction.question) > 10:
        # Create a new FAQ for common questions
        faq_id = str(uuid.uuid4())
        new_faq = {
            "id": faq_id,
            "question": interaction.question,
            "answer": "This question is being reviewed by our team. We'll provide an answer soon.",
            "category": "auto-generated"
        }
        faqs_db[faq_id] = new_faq
        
        return {
            "message": "Interaction recorded and new FAQ created",
            "interaction_id": interaction_id,
            "faq_id": faq_id
        }
    
    return {
        "message": "Interaction recorded",
        "interaction_id": interaction_id
    }

@router.get("/knowledge/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics."""
    return {
        "total_procedures": len(procedures_db),
        "total_faqs": len(faqs_db),
        "total_interactions": len(interactions_db),
        "faq_categories": list(set(faq["category"] for faq in faqs_db.values())),
        "recent_interactions": len([i for i in interactions_db.values() if 
                                   (datetime.now() - datetime.fromisoformat(i["timestamp"])).days <= 7])
    }