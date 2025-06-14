# Pydantic schemas for request/response validation
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class RepairKnowledgeQuery(BaseModel):
    query: str = Field(..., example="How to fix a leaking faucet?")

class ToolMaterialRecommendationRequest(BaseModel):
    task_type: str = Field(..., example="plumbing/leak_fix")

class CostEstimationRequest(BaseModel):
    task_type: str
    params: Dict[str, str]

class SafetyGuidelinesRequest(BaseModel):
    task_type: str

class LearningResourceRequest(BaseModel):
    topic: str

# Response models can be extended as needed.