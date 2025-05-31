"""
KnowledgeBaseAgent - Manages knowledge base operations for the AI Handyman Secretary Assistant.
Handles procedures, FAQs, client history, and pricing information.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Define data models inline for now (these would typically be in separate model files)
class Procedure:
    def __init__(self, id: str, name: str, description: str, estimated_time_minutes: int, required_tools: List[str], price: float):
        self.id = id
        self.name = name
        self.description = description
        self.estimated_time_minutes = estimated_time_minutes
        self.required_tools = required_tools
        self.price = price

class FAQ:
    def __init__(self, id: str, question: str, answer: str, category: str = "general"):
        self.id = id
        self.question = question
        self.answer = answer
        self.category = category

class ClientHistory:
    def __init__(self, client_id: str, interactions: List[Dict[str, Any]]):
        self.client_id = client_id
        self.interactions = interactions

class Pricing:
    def __init__(self, service_id: str, base_price: float, hourly_rate: float):
        self.service_id = service_id
        self.base_price = base_price
        self.hourly_rate = hourly_rate

class KnowledgeBaseAgent:
    """
    Knowledge base management agent that handles procedures, FAQs, and learning from interactions.
    """
    
    def __init__(self, user_role: str = 'user'):
        """
        Initialize the KnowledgeBaseAgent.
        
        Args:
            user_role: Role of the user (admin, user, etc.)
        """
        self.user_role = user_role
        
        # In-memory storage (would typically be a database)
        self.procedures: Dict[str, Procedure] = {}
        self.faqs: Dict[str, FAQ] = {}
        self.client_histories: Dict[str, ClientHistory] = {}
        self.pricing: Dict[str, Pricing] = {}
        
        logger.info(f"KnowledgeBaseAgent initialized with role: {user_role}")
    
    def add_procedure(self, procedure: Procedure) -> bool:
        """
        Add a new procedure to the knowledge base.
        
        Args:
            procedure: Procedure object to add
            
        Returns:
            bool: True if procedure added successfully
        """
        try:
            self.procedures[procedure.id] = procedure
            logger.info(f"Added procedure: {procedure.name} (ID: {procedure.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add procedure {procedure.id}: {str(e)}")
            return False
    
    def get_procedure(self, procedure_id: str) -> Optional[Procedure]:
        """
        Get a procedure by ID.
        
        Args:
            procedure_id: ID of the procedure to retrieve
            
        Returns:
            Procedure object if found, None otherwise
        """
        return self.procedures.get(procedure_id)
    
    def update_procedure(self, procedure_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing procedure.
        
        Args:
            procedure_id: ID of the procedure to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if procedure updated successfully
        """
        try:
            if procedure_id not in self.procedures:
                logger.warning(f"Procedure {procedure_id} not found for update")
                return False
            
            procedure = self.procedures[procedure_id]
            
            # Update fields
            for field, value in updates.items():
                if hasattr(procedure, field):
                    setattr(procedure, field, value)
                    logger.info(f"Updated procedure {procedure_id} field {field} to {value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update procedure {procedure_id}: {str(e)}")
            return False
    
    def delete_procedure(self, procedure_id: str) -> bool:
        """
        Delete a procedure from the knowledge base.
        
        Args:
            procedure_id: ID of the procedure to delete
            
        Returns:
            bool: True if procedure deleted successfully
        """
        try:
            if procedure_id in self.procedures:
                del self.procedures[procedure_id]
                logger.info(f"Deleted procedure: {procedure_id}")
                return True
            else:
                logger.warning(f"Procedure {procedure_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete procedure {procedure_id}: {str(e)}")
            return False
    
    def list_procedures(self, category: Optional[str] = None) -> List[Procedure]:
        """
        List all procedures, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of Procedure objects
        """
        procedures = list(self.procedures.values())
        
        if category:
            # Filter by category if specified (would need category field in Procedure)
            logger.info(f"Filtering procedures by category: {category}")
        
        return procedures
    
    def learn_from_interaction(self, client_id: str, interaction: Dict[str, Any]) -> bool:
        """
        Learn from a client interaction and potentially create FAQs.
        
        Args:
            client_id: ID of the client
            interaction: Dictionary containing interaction details
            
        Returns:
            bool: True if learning was successful
        """
        try:
            # Store the interaction in client history
            if client_id not in self.client_histories:
                self.client_histories[client_id] = ClientHistory(client_id, [])
            
            self.client_histories[client_id].interactions.append(interaction)
            
            # If this is a question, consider adding it as an FAQ
            if 'question' in interaction:
                question = interaction['question']
                
                # Check if this question already exists in FAQs
                existing_faq = None
                for faq in self.faqs.values():
                    if faq.question.lower() == question.lower():
                        existing_faq = faq
                        break
                
                if not existing_faq:
                    # Create a new FAQ
                    faq_id = str(uuid.uuid4())
                    answer = self._generate_answer_for_question(question)
                    new_faq = FAQ(faq_id, question, answer)
                    self.faqs[faq_id] = new_faq
                    logger.info(f"Created new FAQ from interaction: {question}")
            
            logger.info(f"Learned from interaction for client {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to learn from interaction for client {client_id}: {str(e)}")
            return False
    
    def list_faqs(self, category: Optional[str] = None) -> List[FAQ]:
        """
        List all FAQs, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of FAQ objects
        """
        faqs = list(self.faqs.values())
        
        if category:
            faqs = [faq for faq in faqs if faq.category == category]
        
        return faqs
    
    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant information.
        
        Args:
            query: Search query string
            
        Returns:
            List of relevant knowledge items
        """
        results = []
        query_lower = query.lower()
        
        # Search procedures
        for procedure in self.procedures.values():
            if (query_lower in procedure.name.lower() or 
                query_lower in procedure.description.lower()):
                results.append({
                    'type': 'procedure',
                    'id': procedure.id,
                    'name': procedure.name,
                    'description': procedure.description,
                    'relevance_score': 0.8  # Simple scoring
                })
        
        # Search FAQs
        for faq in self.faqs.values():
            if (query_lower in faq.question.lower() or 
                query_lower in faq.answer.lower()):
                results.append({
                    'type': 'faq',
                    'id': faq.id,
                    'question': faq.question,
                    'answer': faq.answer,
                    'relevance_score': 0.7
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"Knowledge search for '{query}' returned {len(results)} results")
        return results
    
    def _generate_answer_for_question(self, question: str) -> str:
        """
        Generate an answer for a question (placeholder implementation).
        
        Args:
            question: The question to answer
            
        Returns:
            Generated answer string
        """
        # This would typically use AI/ML to generate answers
        # For now, return a placeholder
        if "time" in question.lower() and "repair" in question.lower():
            return "Most repairs take between 30 minutes to 2 hours depending on complexity."
        elif "cost" in question.lower() or "price" in question.lower():
            return "Pricing varies by service. Please contact us for a detailed quote."
        else:
            return "Thank you for your question. Our team will provide a detailed answer soon."