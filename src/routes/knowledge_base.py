# FastAPI router for Knowledge Base Agent
from fastapi import APIRouter, Depends, HTTPException
from src.knowledge_base_agent import KnowledgeBaseAgent
from src.schemas import RepairKnowledgeQuery, ToolMaterialRecommendationRequest, CostEstimationRequest, SafetyGuidelinesRequest, LearningResourceRequest

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])

# Dependency injection for KnowledgeBaseAgent (db client setup elsewhere)
def get_agent():
    # Place-holder: Replace with real DB client
    from src.mock_knowledge_db import MockKnowledgeDB
    return KnowledgeBaseAgent(MockKnowledgeDB())

@router.post("/repair-knowledge")
def repair_knowledge(
    body: RepairKnowledgeQuery,
    agent: KnowledgeBaseAgent = Depends(get_agent)
):
    result = agent.get_repair_knowledge(body.query)
    if not result:
        raise HTTPException(status_code=404, detail="Knowledge not found.")
    return result

@router.post("/recommend-tools-materials")
def recommend_tools_materials(
    body: ToolMaterialRecommendationRequest,
    agent: KnowledgeBaseAgent = Depends(get_agent)
):
    return agent.recommend_tools_materials(body.task_type)

@router.post("/estimate-cost")
def estimate_cost(
    body: CostEstimationRequest,
    agent: KnowledgeBaseAgent = Depends(get_agent)
):
    return agent.estimate_cost(body.task_type, body.params)

@router.post("/safety-guidelines")
def safety_guidelines(
    body: SafetyGuidelinesRequest,
    agent: KnowledgeBaseAgent = Depends(get_agent)
):
    return agent.get_safety_guidelines(body.task_type)

@router.post("/learning-resources")
def learning_resources(
    body: LearningResourceRequest,
    agent: KnowledgeBaseAgent = Depends(get_agent)
):
    return agent.get_learning_resources(body.topic)
