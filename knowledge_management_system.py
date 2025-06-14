#!/usr/bin/env python3
"""
Knowledge Management System for Karen AI Multi-Agent Troubleshooting

Captures troubleshooting patterns, builds searchable issue database,
and creates automated learning from agent collaboration experiences.
"""

import json
import time
import threading
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import uuid
from collections import defaultdict, Counter
import difflib

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    TROUBLESHOOTING_PATTERN = "troubleshooting_pattern"
    SOLUTION_TEMPLATE = "solution_template"
    BEST_PRACTICE = "best_practice"
    COMMON_PITFALL = "common_pitfall"
    TOOL_USAGE = "tool_usage"
    INTEGRATION_GUIDE = "integration_guide"
    PERFORMANCE_TIP = "performance_tip"

class ConfidenceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"

@dataclass
class KnowledgeEntry:
    id: str
    type: KnowledgeType
    title: str
    description: str
    content: Dict[str, Any]
    tags: List[str]
    keywords: List[str]
    confidence: ConfidenceLevel
    created_by: str
    created_at: str
    updated_at: str
    validation_count: int
    success_rate: float
    related_entries: List[str]
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type.value,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'tags': self.tags,
            'keywords': self.keywords,
            'confidence': self.confidence.value,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'validation_count': self.validation_count,
            'success_rate': self.success_rate,
            'related_entries': self.related_entries
        }

@dataclass
class PatternMatch:
    pattern_id: str
    confidence_score: float
    matched_keywords: List[str]
    similarity: float
    suggested_actions: List[str]

@dataclass
class LearningEvent:
    id: str
    event_type: str  # issue_resolved, solution_failed, pattern_discovered
    context: Dict[str, Any]
    outcome: str
    agents_involved: List[str]
    timestamp: str
    extracted_knowledge: List[str]

class KnowledgeManagementSystem:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.base_path = Path("/workspace/autonomous-agents")
        self.knowledge_path = self.base_path / "troubleshooting" / "knowledge-base"
        self.patterns_path = self.knowledge_path / "patterns"
        self.templates_path = self.knowledge_path / "templates"
        self.learning_path = self.knowledge_path / "learning"
        
        # Knowledge storage
        self.knowledge_entries: Dict[str, KnowledgeEntry] = {}
        self.pattern_index: Dict[str, List[str]] = defaultdict(list)  # keyword -> entry_ids
        self.success_metrics: Dict[str, Dict] = {}
        self.learning_events: List[LearningEvent] = []
        
        # Pattern recognition
        self.common_patterns = {
            "mcp_tool_errors": [
                "connection refused", "timeout", "protocol error", "schema validation",
                "tool not found", "parameter missing", "authentication failed"
            ],
            "testing_issues": [
                "test failed", "assertion error", "fixture not found", "import error",
                "dependency missing", "environment setup", "permission denied"
            ],
            "integration_problems": [
                "api endpoint", "data format", "serialization", "configuration",
                "environment variable", "service unavailable", "rate limit"
            ],
            "performance_issues": [
                "memory leak", "high cpu", "slow response", "timeout", "bottleneck",
                "resource exhaustion", "deadlock", "scaling issue"
            ]
        }
        
        # Initialize knowledge infrastructure
        self._initialize_knowledge_base()
        self._load_existing_knowledge()
        
        # Start knowledge processing
        self.running = True
        threading.Thread(target=self._monitor_learning_events, daemon=True).start()
        threading.Thread(target=self._update_pattern_effectiveness, daemon=True).start()
        
    def _initialize_knowledge_base(self):
        """Initialize knowledge base directory structure"""
        directories = [
            self.knowledge_path,
            self.patterns_path,
            self.templates_path,
            self.learning_path,
            self.knowledge_path / "best-practices",
            self.knowledge_path / "common-issues",
            self.knowledge_path / "automation-rules"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Create knowledge index file
        index_file = self.knowledge_path / "knowledge_index.json"
        if not index_file.exists():
            with open(index_file, 'w') as f:
                json.dump({"entries": [], "patterns": {}, "last_updated": datetime.now().isoformat()}, f, indent=2)
                
    def _load_existing_knowledge(self):
        """Load existing knowledge entries from filesystem"""
        try:
            # Load knowledge entries
            for entry_file in self.knowledge_path.glob("**/*.json"):
                if entry_file.name in ["knowledge_index.json", "learning_events.json"]:
                    continue
                    
                try:
                    with open(entry_file, 'r') as f:
                        entry_data = json.load(f)
                        
                    if 'type' in entry_data and 'id' in entry_data:
                        entry = KnowledgeEntry(
                            id=entry_data['id'],
                            type=KnowledgeType(entry_data['type']),
                            title=entry_data['title'],
                            description=entry_data['description'],
                            content=entry_data['content'],
                            tags=entry_data['tags'],
                            keywords=entry_data['keywords'],
                            confidence=ConfidenceLevel(entry_data['confidence']),
                            created_by=entry_data['created_by'],
                            created_at=entry_data['created_at'],
                            updated_at=entry_data['updated_at'],
                            validation_count=entry_data.get('validation_count', 0),
                            success_rate=entry_data.get('success_rate', 0.0),
                            related_entries=entry_data.get('related_entries', [])
                        )
                        
                        self.knowledge_entries[entry.id] = entry
                        self._update_pattern_index(entry)
                        
                except Exception as e:
                    logger.error(f"Error loading knowledge entry {entry_file}: {e}")
                    
            # Load learning events
            learning_file = self.learning_path / "learning_events.json"
            if learning_file.exists():
                with open(learning_file, 'r') as f:
                    events_data = json.load(f)
                    for event_data in events_data.get("events", []):
                        event = LearningEvent(**event_data)
                        self.learning_events.append(event)
                        
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            
    def create_knowledge_entry(self, entry_type: KnowledgeType, title: str, description: str,
                              content: Dict[str, Any], tags: List[str] = None,
                              keywords: List[str] = None, confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM) -> str:
        """Create a new knowledge entry"""
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Extract keywords from content if not provided
        if keywords is None:
            keywords = self._extract_keywords(title + " " + description + " " + str(content))
            
        entry = KnowledgeEntry(
            id=entry_id,
            type=entry_type,
            title=title,
            description=description,
            content=content,
            tags=tags or [],
            keywords=keywords,
            confidence=confidence,
            created_by=self.agent_id,
            created_at=timestamp,
            updated_at=timestamp,
            validation_count=0,
            success_rate=0.0,
            related_entries=[]
        )
        
        self.knowledge_entries[entry_id] = entry
        self._update_pattern_index(entry)
        self._save_knowledge_entry(entry)
        
        # Find and link related entries
        self._link_related_entries(entry)
        
        logger.info(f"Created knowledge entry: {title} ({entry_id})")
        return entry_id
        
    def search_knowledge(self, query: str, entry_type: KnowledgeType = None,
                        tags: List[str] = None, min_confidence: ConfidenceLevel = None) -> List[Tuple[KnowledgeEntry, float]]:
        """Search knowledge base with ranking"""
        results = []
        query_keywords = self._extract_keywords(query.lower())
        
        for entry in self.knowledge_entries.values():
            # Apply filters
            if entry_type and entry.type != entry_type:
                continue
                
            if tags and not any(tag in entry.tags for tag in tags):
                continue
                
            if min_confidence and entry.confidence.value < min_confidence.value:
                continue
                
            # Calculate relevance score
            relevance_score = self._calculate_relevance(entry, query, query_keywords)
            
            if relevance_score > 0.1:  # Minimum threshold
                results.append((entry, relevance_score))
                
        # Sort by relevance and success rate
        results.sort(key=lambda x: (x[1], x[0].success_rate), reverse=True)
        return results
        
    def find_matching_patterns(self, issue_description: str, context: Dict[str, Any] = None) -> List[PatternMatch]:
        """Find patterns that match the given issue"""
        matches = []
        issue_keywords = self._extract_keywords(issue_description.lower())
        
        # Check against known pattern categories
        for category, pattern_keywords in self.common_patterns.items():
            matched_keywords = [kw for kw in pattern_keywords if any(kw in issue_description.lower() for kw in [kw])]
            
            if matched_keywords:
                confidence = len(matched_keywords) / len(pattern_keywords)
                similarity = self._calculate_text_similarity(issue_description, " ".join(pattern_keywords))
                
                # Get suggested actions for this pattern category
                suggested_actions = self._get_pattern_actions(category, context)
                
                match = PatternMatch(
                    pattern_id=category,
                    confidence_score=confidence,
                    matched_keywords=matched_keywords,
                    similarity=similarity,
                    suggested_actions=suggested_actions
                )
                matches.append(match)
                
        # Check against learned patterns
        for entry in self.knowledge_entries.values():
            if entry.type == KnowledgeType.TROUBLESHOOTING_PATTERN:
                keyword_overlap = len(set(issue_keywords) & set(entry.keywords))
                if keyword_overlap > 0:
                    confidence = keyword_overlap / len(entry.keywords)
                    similarity = self._calculate_text_similarity(issue_description, entry.description)
                    
                    suggested_actions = entry.content.get("suggested_actions", [])
                    
                    match = PatternMatch(
                        pattern_id=entry.id,
                        confidence_score=confidence * (entry.success_rate + 0.1),  # Boost by success rate
                        matched_keywords=list(set(issue_keywords) & set(entry.keywords)),
                        similarity=similarity,
                        suggested_actions=suggested_actions
                    )
                    matches.append(match)
                    
        # Sort by confidence and return top matches
        matches.sort(key=lambda m: m.confidence_score, reverse=True)
        return matches[:5]
        
    def record_learning_event(self, event_type: str, context: Dict[str, Any],
                             outcome: str, agents_involved: List[str] = None) -> str:
        """Record a learning event for pattern extraction"""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Extract potential knowledge from the event
        extracted_knowledge = self._extract_knowledge_from_event(event_type, context, outcome)
        
        event = LearningEvent(
            id=event_id,
            event_type=event_type,
            context=context,
            outcome=outcome,
            agents_involved=agents_involved or [self.agent_id],
            timestamp=timestamp,
            extracted_knowledge=extracted_knowledge
        )
        
        self.learning_events.append(event)
        self._save_learning_events()
        
        # Process immediate learning opportunities
        self._process_learning_event(event)
        
        logger.info(f"Recorded learning event: {event_type}")
        return event_id
        
    def validate_knowledge_entry(self, entry_id: str, success: bool, feedback: str = "") -> bool:
        """Validate a knowledge entry based on usage outcome"""
        if entry_id not in self.knowledge_entries:
            return False
            
        entry = self.knowledge_entries[entry_id]
        entry.validation_count += 1
        
        # Update success rate
        if entry.validation_count == 1:
            entry.success_rate = 1.0 if success else 0.0
        else:
            # Moving average with more weight on recent validations
            weight = 0.3  # Weight for new validation
            entry.success_rate = (1 - weight) * entry.success_rate + weight * (1.0 if success else 0.0)
            
        # Update confidence based on validation count and success rate
        if entry.validation_count >= 10 and entry.success_rate >= 0.9:
            entry.confidence = ConfidenceLevel.VERIFIED
        elif entry.validation_count >= 5 and entry.success_rate >= 0.7:
            entry.confidence = ConfidenceLevel.HIGH
        elif entry.success_rate >= 0.5:
            entry.confidence = ConfidenceLevel.MEDIUM
        else:
            entry.confidence = ConfidenceLevel.LOW
            
        entry.updated_at = datetime.now().isoformat()
        self._save_knowledge_entry(entry)
        
        # Record validation event
        self.record_learning_event(
            "knowledge_validation",
            {
                "entry_id": entry_id,
                "entry_type": entry.type.value,
                "success": success,
                "feedback": feedback
            },
            "validated" if success else "invalidated"
        )
        
        return True
        
    def generate_troubleshooting_playbook(self, issue_category: str) -> Dict[str, Any]:
        """Generate a troubleshooting playbook for a specific issue category"""
        relevant_entries = []
        
        # Find relevant knowledge entries
        for entry in self.knowledge_entries.values():
            if (issue_category.lower() in entry.title.lower() or 
                issue_category.lower() in entry.description.lower() or
                issue_category in entry.tags):
                relevant_entries.append(entry)
                
        # Sort by confidence and success rate
        relevant_entries.sort(key=lambda e: (e.confidence.value, e.success_rate), reverse=True)
        
        playbook = {
            "category": issue_category,
            "generated_at": datetime.now().isoformat(),
            "generated_by": self.agent_id,
            "steps": [],
            "common_patterns": [],
            "best_practices": [],
            "tools_required": [],
            "estimated_time_minutes": 0
        }
        
        # Extract troubleshooting steps
        step_counter = 1
        for entry in relevant_entries[:10]:  # Top 10 most relevant
            if entry.type in [KnowledgeType.TROUBLESHOOTING_PATTERN, KnowledgeType.SOLUTION_TEMPLATE]:
                steps = entry.content.get("steps", [])
                for step in steps:
                    playbook["steps"].append({
                        "number": step_counter,
                        "description": step,
                        "source_entry": entry.id,
                        "confidence": entry.confidence.value
                    })
                    step_counter += 1
                    
            elif entry.type == KnowledgeType.BEST_PRACTICE:
                playbook["best_practices"].append({
                    "practice": entry.title,
                    "description": entry.description,
                    "confidence": entry.confidence.value
                })
                
            # Extract tools
            tools = entry.content.get("tools_required", [])
            playbook["tools_required"].extend(tools)
            
            # Add to estimated time
            time_estimate = entry.content.get("estimated_time_minutes", 0)
            playbook["estimated_time_minutes"] += time_estimate
            
        # Remove duplicates from tools
        playbook["tools_required"] = list(set(playbook["tools_required"]))
        
        # Add common patterns
        for pattern_category, keywords in self.common_patterns.items():
            if any(keyword in issue_category.lower() for keyword in keywords):
                playbook["common_patterns"].append({
                    "category": pattern_category,
                    "indicators": keywords
                })
                
        return playbook
        
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Simple keyword extraction (can be enhanced with NLP)
        stop_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "shall"}
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Remove duplicates and return most frequent
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(20)]
        
    def _calculate_relevance(self, entry: KnowledgeEntry, query: str, query_keywords: List[str]) -> float:
        """Calculate relevance score for a knowledge entry"""
        score = 0.0
        
        # Keyword overlap
        keyword_overlap = len(set(query_keywords) & set(entry.keywords))
        score += (keyword_overlap / max(len(query_keywords), 1)) * 0.4
        
        # Title similarity
        title_similarity = self._calculate_text_similarity(query, entry.title)
        score += title_similarity * 0.3
        
        # Description similarity
        desc_similarity = self._calculate_text_similarity(query, entry.description)
        score += desc_similarity * 0.2
        
        # Confidence boost
        confidence_boost = {"low": 0.0, "medium": 0.05, "high": 0.1, "verified": 0.15}
        score += confidence_boost.get(entry.confidence.value, 0.0)
        
        # Success rate boost
        score += entry.success_rate * 0.1
        
        return min(score, 1.0)
        
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using sequence matching"""
        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        
    def _get_pattern_actions(self, category: str, context: Dict[str, Any] = None) -> List[str]:
        """Get suggested actions for a pattern category"""
        action_map = {
            "mcp_tool_errors": [
                "Check MCP server connection",
                "Validate tool parameters",
                "Review authentication credentials",
                "Check network connectivity",
                "Restart MCP server"
            ],
            "testing_issues": [
                "Check test environment setup",
                "Verify test dependencies",
                "Review test configuration",
                "Check file permissions",
                "Update test fixtures"
            ],
            "integration_problems": [
                "Verify API endpoint availability",
                "Check data format compatibility",
                "Review environment variables",
                "Test service dependencies",
                "Check rate limits"
            ],
            "performance_issues": [
                "Monitor resource usage",
                "Check for memory leaks",
                "Profile application performance",
                "Review database queries",
                "Optimize critical paths"
            ]
        }
        
        return action_map.get(category, ["Investigate further", "Check logs", "Review documentation"])
        
    def _extract_knowledge_from_event(self, event_type: str, context: Dict[str, Any], outcome: str) -> List[str]:
        """Extract potential knowledge from a learning event"""
        knowledge = []
        
        if event_type == "issue_resolved":
            solution_steps = context.get("solution_steps", [])
            if solution_steps and outcome == "success":
                knowledge.append(f"Successful resolution pattern: {' -> '.join(solution_steps)}")
                
        elif event_type == "solution_failed":
            failed_approach = context.get("attempted_solution", "")
            if failed_approach:
                knowledge.append(f"Ineffective approach: {failed_approach}")
                
        elif event_type == "pattern_discovered":
            pattern_description = context.get("pattern", "")
            if pattern_description:
                knowledge.append(f"New pattern identified: {pattern_description}")
                
        return knowledge
        
    def _process_learning_event(self, event: LearningEvent):
        """Process a learning event to create new knowledge entries"""
        if event.event_type == "issue_resolved" and len(event.extracted_knowledge) > 0:
            # Create a new troubleshooting pattern
            issue_description = event.context.get("issue_description", "")
            solution_steps = event.context.get("solution_steps", [])
            
            if issue_description and solution_steps:
                self.create_knowledge_entry(
                    entry_type=KnowledgeType.TROUBLESHOOTING_PATTERN,
                    title=f"Resolution Pattern: {issue_description[:50]}...",
                    description=issue_description,
                    content={
                        "steps": solution_steps,
                        "context": event.context,
                        "success_indicators": event.context.get("success_indicators", []),
                        "tools_required": event.context.get("tools_used", []),
                        "estimated_time_minutes": event.context.get("resolution_time_minutes", 30)
                    },
                    tags=event.context.get("tags", []),
                    confidence=ConfidenceLevel.MEDIUM
                )
                
    def _update_pattern_index(self, entry: KnowledgeEntry):
        """Update the pattern index for faster searching"""
        for keyword in entry.keywords:
            self.pattern_index[keyword.lower()].append(entry.id)
            
    def _link_related_entries(self, entry: KnowledgeEntry):
        """Find and link related knowledge entries"""
        related = []
        
        for other_entry in self.knowledge_entries.values():
            if other_entry.id == entry.id:
                continue
                
            # Check for keyword overlap
            keyword_overlap = len(set(entry.keywords) & set(other_entry.keywords))
            if keyword_overlap >= 3:  # Minimum overlap threshold
                similarity = self._calculate_text_similarity(entry.description, other_entry.description)
                if similarity > 0.3:
                    related.append(other_entry.id)
                    
        entry.related_entries = related[:5]  # Limit to top 5 related entries
        
        # Update reverse links
        for related_id in related:
            if related_id in self.knowledge_entries:
                related_entry = self.knowledge_entries[related_id]
                if entry.id not in related_entry.related_entries:
                    related_entry.related_entries.append(entry.id)
                    self._save_knowledge_entry(related_entry)
                    
    def _save_knowledge_entry(self, entry: KnowledgeEntry):
        """Save knowledge entry to filesystem"""
        entry_file = self.knowledge_path / f"{entry.id}.json"
        with open(entry_file, 'w') as f:
            json.dump(entry.to_dict(), f, indent=2)
            
    def _save_learning_events(self):
        """Save learning events to filesystem"""
        learning_file = self.learning_path / "learning_events.json"
        events_data = {
            "events": [asdict(event) for event in self.learning_events[-1000:]],  # Keep last 1000 events
            "last_updated": datetime.now().isoformat()
        }
        with open(learning_file, 'w') as f:
            json.dump(events_data, f, indent=2)
            
    def _monitor_learning_events(self):
        """Monitor for learning opportunities from other agents"""
        while self.running:
            try:
                # Check for new learning events from other agents
                # This would integrate with the communication system
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error monitoring learning events: {e}")
                time.sleep(60)
                
    def _update_pattern_effectiveness(self):
        """Update pattern effectiveness based on usage statistics"""
        while self.running:
            try:
                # Update effectiveness scores based on recent validations
                cutoff_time = datetime.now() - timedelta(days=30)
                
                for entry in self.knowledge_entries.values():
                    if entry.validation_count > 0:
                        # Decay old effectiveness if not recently validated
                        last_updated = datetime.fromisoformat(entry.updated_at)
                        if last_updated < cutoff_time:
                            entry.success_rate *= 0.95  # Slight decay
                            entry.updated_at = datetime.now().isoformat()
                            self._save_knowledge_entry(entry)
                            
                time.sleep(3600)  # Update every hour
                
            except Exception as e:
                logger.error(f"Error updating pattern effectiveness: {e}")
                time.sleep(3600)
                
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge management statistics"""
        return {
            "total_entries": len(self.knowledge_entries),
            "by_type": {ktype.value: len([e for e in self.knowledge_entries.values() if e.type == ktype]) 
                       for ktype in KnowledgeType},
            "by_confidence": {conf.value: len([e for e in self.knowledge_entries.values() if e.confidence == conf])
                             for conf in ConfidenceLevel},
            "learning_events": len(self.learning_events),
            "average_success_rate": sum(e.success_rate for e in self.knowledge_entries.values()) / max(len(self.knowledge_entries), 1),
            "most_validated_entry": max(self.knowledge_entries.values(), key=lambda e: e.validation_count, default=None)
        }
        
    def stop(self):
        """Stop the knowledge management system"""
        self.running = False
        logger.info("Knowledge management system stopped")

def create_knowledge_manager(agent_id: str) -> KnowledgeManagementSystem:
    """Factory function to create a knowledge management system"""
    return KnowledgeManagementSystem(agent_id)