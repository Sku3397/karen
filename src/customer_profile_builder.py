"""
Customer Profile Builder for Karen AI
Intelligent customer profile construction with automatic preference learning

Builds comprehensive customer profiles by:
- Analyzing conversation patterns and preferences
- Learning communication styles and timing preferences
- Tracking service history and satisfaction
- Merging profiles across channels for identity resolution
- Privacy-compliant data handling with granular controls
"""

import re
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import logging
from fuzzywuzzy import fuzz, process
import numpy as np

from memory_embeddings_manager import MemoryEmbeddingsManager

logger = logging.getLogger(__name__)

@dataclass
class ContactPreferences:
    """Customer contact preferences learned from interactions"""
    preferred_channel: str = "email"
    preferred_times: List[int] = None  # Hours of day (0-23)
    preferred_days: List[int] = None   # Days of week (0-6, Monday=0)
    response_urgency: str = "normal"   # low, normal, high
    communication_style: str = "formal"  # formal, casual, friendly
    language_preference: str = "en"
    timezone: str = "UTC"
    
    def __post_init__(self):
        if self.preferred_times is None:
            self.preferred_times = []
        if self.preferred_days is None:
            self.preferred_days = []

@dataclass
class ServiceHistory:
    """Customer service history and satisfaction tracking"""
    total_requests: int = 0
    completed_requests: int = 0
    satisfaction_scores: List[float] = None
    service_types: List[str] = None
    average_response_time: float = 0.0  # hours
    last_service_date: str = None
    favorite_technician: str = None
    
    def __post_init__(self):
        if self.satisfaction_scores is None:
            self.satisfaction_scores = []
        if self.service_types is None:
            self.service_types = []

@dataclass
class CustomerProfile:
    """Complete customer profile with learned preferences"""
    customer_id: str
    primary_name: str = ""
    alternative_names: List[str] = None
    email_addresses: List[str] = None
    phone_numbers: List[str] = None
    contact_preferences: ContactPreferences = None
    service_history: ServiceHistory = None
    
    # Behavioral insights
    personality_traits: Dict[str, float] = None  # patience, politeness, detail_oriented, etc.
    value_indicators: Dict[str, Any] = None      # spending_tier, loyalty_score, etc.
    risk_factors: Dict[str, float] = None        # churn_risk, payment_risk, etc.
    
    # Metadata
    created_at: str = ""
    updated_at: str = ""
    last_interaction: str = ""
    confidence_score: float = 1.0
    privacy_settings: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.alternative_names is None:
            self.alternative_names = []
        if self.email_addresses is None:
            self.email_addresses = []
        if self.phone_numbers is None:
            self.phone_numbers = []
        if self.contact_preferences is None:
            self.contact_preferences = ContactPreferences()
        if self.service_history is None:
            self.service_history = ServiceHistory()
        if self.personality_traits is None:
            self.personality_traits = {}
        if self.value_indicators is None:
            self.value_indicators = {}
        if self.risk_factors is None:
            self.risk_factors = {}
        if self.privacy_settings is None:
            self.privacy_settings = {
                "store_conversations": True,
                "learn_preferences": True,
                "cross_channel_linking": True,
                "analytics": True
            }
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

class IdentityResolver:
    """Cross-channel identity resolution system"""
    
    def __init__(self, memory_manager: MemoryEmbeddingsManager):
        self.memory_manager = memory_manager
        
    def resolve_customer_identity(
        self,
        phone: str = None,
        email: str = None,
        name: str = None,
        confidence_threshold: float = 0.8
    ) -> Tuple[Optional[str], float]:
        """
        Resolve customer identity across channels using multiple signals
        
        Args:
            phone: Phone number
            email: Email address  
            name: Customer name
            confidence_threshold: Minimum confidence for positive match
            
        Returns:
            (customer_id, confidence_score) or (None, 0.0) if no match
        """
        try:
            matches = []
            
            # Search by phone number
            if phone:
                normalized_phone = self._normalize_phone(phone)
                phone_matches = self._search_by_phone(normalized_phone)
                matches.extend([(m, 0.9, "phone") for m in phone_matches])
            
            # Search by email
            if email:
                email_matches = self._search_by_email(email.lower())
                matches.extend([(m, 0.95, "email") for m in email_matches])
            
            # Search by name (fuzzy matching)
            if name:
                name_matches = self._fuzzy_name_search(name)
                matches.extend([(m, score, "name") for m, score in name_matches])
            
            # Merge and score matches
            merged_matches = self._merge_matches(matches)
            
            if merged_matches:
                best_match, confidence = merged_matches[0]
                
                if confidence >= confidence_threshold:
                    logger.info(f"✅ Identity resolved: {best_match} (confidence: {confidence:.2f})")
                    return best_match, confidence
                else:
                    logger.info(f"⚠️ Low confidence match: {best_match} (confidence: {confidence:.2f})")
            
            logger.info("No matching customer identity found")
            return None, 0.0
            
        except Exception as e:
            logger.error(f"❌ Failed to resolve identity: {e}")
            return None, 0.0
    
    def _search_by_phone(self, normalized_phone: str) -> List[str]:
        """Search for customers by normalized phone number"""
        try:
            results = self.memory_manager.collection.get(
                where={"phone_number": normalized_phone},
                limit=10
            )
            
            return list(set(
                metadata.get("customer_id") 
                for metadata in results["metadatas"] 
                if metadata.get("customer_id")
            ))
            
        except Exception as e:
            logger.error(f"Phone search failed: {e}")
            return []
    
    def _search_by_email(self, email: str) -> List[str]:
        """Search for customers by email address"""
        try:
            results = self.memory_manager.collection.get(
                where={"email_address": email},
                limit=10
            )
            
            return list(set(
                metadata.get("customer_id") 
                for metadata in results["metadatas"] 
                if metadata.get("customer_id")
            ))
            
        except Exception as e:
            logger.error(f"Email search failed: {e}")
            return []
    
    def _fuzzy_name_search(self, name: str, min_score: int = 70) -> List[Tuple[str, float]]:
        """Fuzzy search for customers by name"""
        try:
            # Get recent conversations to search through
            results = self.memory_manager.collection.get(
                limit=1000  # Search recent conversations
            )
            
            name_matches = []
            seen_customers = set()
            
            for metadata in results["metadatas"]:
                customer_id = metadata.get("customer_id")
                customer_name = metadata.get("customer_name")
                
                if customer_id and customer_name and customer_id not in seen_customers:
                    # Calculate fuzzy match score
                    score = fuzz.ratio(name.lower(), customer_name.lower())
                    
                    if score >= min_score:
                        confidence = score / 100.0 * 0.7  # Name matching gets lower base confidence
                        name_matches.append((customer_id, confidence))
                        seen_customers.add(customer_id)
            
            # Sort by confidence
            return sorted(name_matches, key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            logger.error(f"Name search failed: {e}")
            return []
    
    def _merge_matches(self, matches: List[Tuple[str, float, str]]) -> List[Tuple[str, float]]:
        """Merge and score customer matches from different sources"""
        customer_scores = defaultdict(list)
        
        # Group matches by customer_id
        for customer_id, confidence, source in matches:
            customer_scores[customer_id].append((confidence, source))
        
        # Calculate combined confidence scores
        merged = []
        for customer_id, scores in customer_scores.items():
            # Boost confidence if multiple sources agree
            source_boost = len(set(source for _, source in scores)) * 0.1
            avg_confidence = np.mean([conf for conf, _ in scores])
            final_confidence = min(1.0, avg_confidence + source_boost)
            
            merged.append((customer_id, final_confidence))
        
        # Sort by confidence
        return sorted(merged, key=lambda x: x[1], reverse=True)
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for consistent matching"""
        digits_only = ''.join(filter(str.isdigit, phone))
        
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        else:
            return f"+{digits_only}"

class CustomerProfileBuilder:
    """Main class for building and maintaining customer profiles"""
    
    def __init__(self, memory_manager: MemoryEmbeddingsManager):
        self.memory_manager = memory_manager
        self.identity_resolver = IdentityResolver(memory_manager)
        self.profiles_cache = {}  # In-memory cache for active profiles
    
    def build_profile(
        self,
        customer_id: str,
        phone: str = None,
        email: str = None,
        name: str = None,
        force_rebuild: bool = False
    ) -> CustomerProfile:
        """
        Build comprehensive customer profile from conversation history
        
        Args:
            customer_id: Customer identifier
            phone: Customer phone number
            email: Customer email
            name: Customer name
            force_rebuild: Force complete profile rebuild
            
        Returns:
            Complete customer profile with learned preferences
        """
        try:
            # Check cache first
            if not force_rebuild and customer_id in self.profiles_cache:
                cached_profile = self.profiles_cache[customer_id]
                # Return cached if recent (within 1 hour)
                cache_time = datetime.fromisoformat(cached_profile.updated_at.replace('Z', '+00:00'))
                if datetime.now(timezone.utc) - cache_time < timedelta(hours=1):
                    return cached_profile
            
            logger.info(f"Building profile for customer: {customer_id}")
            
            # Get all customer conversations
            conversations = self.memory_manager.get_customer_conversations(
                customer_id=customer_id,
                limit=500  # Analyze recent conversations
            )
            
            if not conversations:
                # Create minimal profile
                profile = CustomerProfile(
                    customer_id=customer_id,
                    primary_name=name or "",
                    email_addresses=[email] if email else [],
                    phone_numbers=[phone] if phone else []
                )
                self.profiles_cache[customer_id] = profile
                return profile
            
            # Build profile from conversations
            profile = self._analyze_conversations(customer_id, conversations)
            
            # Add provided contact info
            if phone and phone not in profile.phone_numbers:
                profile.phone_numbers.append(self.identity_resolver._normalize_phone(phone))
            if email and email not in profile.email_addresses:
                profile.email_addresses.append(email.lower())
            if name and name not in profile.alternative_names:
                if not profile.primary_name:
                    profile.primary_name = name
                elif name != profile.primary_name:
                    profile.alternative_names.append(name)
            
            # Update timestamps
            profile.updated_at = datetime.now(timezone.utc).isoformat()
            if conversations:
                profile.last_interaction = conversations[0]['metadata']['timestamp']
            
            # Cache the profile
            self.profiles_cache[customer_id] = profile
            
            logger.info(f"✅ Profile built for {customer_id}: {len(conversations)} conversations analyzed")
            return profile
            
        except Exception as e:
            logger.error(f"❌ Failed to build profile for {customer_id}: {e}")
            # Return minimal profile on error
            return CustomerProfile(
                customer_id=customer_id,
                primary_name=name or "",
                email_addresses=[email] if email else [],
                phone_numbers=[phone] if phone else []
            )
    
    def _analyze_conversations(self, customer_id: str, conversations: List[Dict]) -> CustomerProfile:
        """Analyze conversations to extract customer insights"""
        
        # Initialize profile
        profile = CustomerProfile(customer_id=customer_id)
        
        # Extract basic info from conversations
        names = set()
        emails = set()
        phones = set()
        channels = []
        timestamps = []
        sentiments = []
        response_times = []
        
        for conv in conversations:
            metadata = conv['metadata']
            
            # Collect contact info
            if metadata.get('customer_name'):
                names.add(metadata['customer_name'])
            if metadata.get('email_address'):
                emails.add(metadata['email_address'])
            if metadata.get('phone_number'):
                phones.add(metadata['phone_number'])
            
            # Collect behavioral data
            channels.append(metadata.get('channel', 'unknown'))
            timestamps.append(metadata.get('timestamp'))
            
            if metadata.get('sentiment'):
                sentiments.append(metadata['sentiment'])
        
        # Set profile basic info
        if names:
            name_counts = Counter(names)
            profile.primary_name = name_counts.most_common(1)[0][0]
            profile.alternative_names = [name for name in names if name != profile.primary_name]
        
        profile.email_addresses = list(emails)
        profile.phone_numbers = list(phones)
        
        # Analyze contact preferences
        profile.contact_preferences = self._analyze_contact_preferences(conversations)
        
        # Analyze service history
        profile.service_history = self._analyze_service_history(conversations)
        
        # Analyze personality traits
        profile.personality_traits = self._analyze_personality(conversations)
        
        # Calculate value indicators
        profile.value_indicators = self._calculate_value_indicators(conversations)
        
        # Assess risk factors
        profile.risk_factors = self._assess_risk_factors(conversations)
        
        return profile
    
    def _analyze_contact_preferences(self, conversations: List[Dict]) -> ContactPreferences:
        """Analyze customer contact preferences from conversation patterns"""
        
        prefs = ContactPreferences()
        
        # Channel preference
        channels = [conv['metadata'].get('channel', 'unknown') for conv in conversations]
        if channels:
            channel_counts = Counter(channels)
            prefs.preferred_channel = channel_counts.most_common(1)[0][0]
        
        # Time preferences
        hours = []
        days = []
        
        for conv in conversations:
            timestamp_str = conv['metadata'].get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    hours.append(timestamp.hour)
                    days.append(timestamp.weekday())
                except:
                    continue
        
        if hours:
            # Find most common hours (clustering approach)
            hour_counts = Counter(hours)
            # Get top 3 most common hours as preferred times
            prefs.preferred_times = [hour for hour, _ in hour_counts.most_common(3)]
        
        if days:
            day_counts = Counter(days)
            # Get weekdays if they appear more than weekends
            weekdays = sum(count for day, count in day_counts.items() if day < 5)
            weekends = sum(count for day, count in day_counts.items() if day >= 5)
            
            if weekdays > weekends:
                prefs.preferred_days = [0, 1, 2, 3, 4]  # Monday-Friday
            else:
                prefs.preferred_days = list(day_counts.keys())
        
        # Communication style analysis
        formal_indicators = 0
        casual_indicators = 0
        
        for conv in conversations:
            text = conv['text'].lower()
            
            # Formal indicators
            if any(word in text for word in ['please', 'thank you', 'sincerely', 'regards']):
                formal_indicators += 1
            
            # Casual indicators  
            if any(word in text for word in ['hey', 'hi', 'thanks', 'thx', '!']):
                casual_indicators += 1
        
        if formal_indicators > casual_indicators:
            prefs.communication_style = "formal"
        elif casual_indicators > formal_indicators:
            prefs.communication_style = "casual"
        else:
            prefs.communication_style = "friendly"
        
        return prefs
    
    def _analyze_service_history(self, conversations: List[Dict]) -> ServiceHistory:
        """Analyze customer service history and satisfaction"""
        
        history = ServiceHistory()
        
        service_requests = 0
        completed_services = 0
        satisfaction_scores = []
        service_types = []
        
        for conv in conversations:
            metadata = conv['metadata']
            text = conv['text'].lower()
            
            # Detect service requests
            if metadata.get('intent') == 'service_request' or any(
                keyword in text for keyword in ['fix', 'repair', 'install', 'service', 'help with']
            ):
                service_requests += 1
                
                # Extract service type
                if 'faucet' in text or 'sink' in text:
                    service_types.append('plumbing')
                elif 'electrical' in text or 'outlet' in text or 'light' in text:
                    service_types.append('electrical')
                elif 'door' in text or 'lock' in text:
                    service_types.append('hardware')
                else:
                    service_types.append('general')
            
            # Detect satisfaction indicators
            sentiment = metadata.get('sentiment')
            if sentiment == 'positive':
                # Look for completion/satisfaction keywords
                if any(keyword in text for keyword in ['great', 'excellent', 'perfect', 'thank you', 'satisfied']):
                    completed_services += 1
                    satisfaction_scores.append(0.9)
            elif sentiment == 'negative':
                if any(keyword in text for keyword in ['disappointed', 'unsatisfied', 'problem', 'issue']):
                    satisfaction_scores.append(0.3)
        
        history.total_requests = service_requests
        history.completed_requests = completed_services
        history.satisfaction_scores = satisfaction_scores
        history.service_types = list(set(service_types))
        
        if conversations:
            history.last_service_date = conversations[0]['metadata'].get('timestamp')
        
        return history
    
    def _analyze_personality(self, conversations: List[Dict]) -> Dict[str, float]:
        """Analyze customer personality traits from conversations"""
        
        traits = {
            'patience': 0.5,
            'politeness': 0.5,
            'detail_oriented': 0.5,
            'tech_savvy': 0.5,
            'urgency_prone': 0.5
        }
        
        total_conversations = len(conversations)
        if total_conversations == 0:
            return traits
        
        polite_count = 0
        urgent_count = 0
        detailed_count = 0
        tech_count = 0
        
        for conv in conversations:
            text = conv['text'].lower()
            
            # Politeness indicators
            if any(word in text for word in ['please', 'thank you', 'sorry', 'appreciate']):
                polite_count += 1
            
            # Urgency indicators
            if any(word in text for word in ['urgent', 'asap', 'emergency', 'immediately', '!!!']):
                urgent_count += 1
            
            # Detail orientation
            if len(text) > 200 or any(word in text for word in ['specifically', 'exactly', 'details']):
                detailed_count += 1
            
            # Tech savviness
            if any(word in text for word in ['wifi', 'app', 'smart', 'digital', 'online']):
                tech_count += 1
        
        # Calculate trait scores
        traits['politeness'] = min(1.0, polite_count / total_conversations * 2)
        traits['urgency_prone'] = min(1.0, urgent_count / total_conversations * 3)
        traits['detail_oriented'] = min(1.0, detailed_count / total_conversations * 2)
        traits['tech_savvy'] = min(1.0, tech_count / total_conversations * 2)
        
        # Patience is inverse of urgency
        traits['patience'] = 1.0 - traits['urgency_prone']
        
        return traits
    
    def _calculate_value_indicators(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Calculate customer value indicators"""
        
        indicators = {
            'conversation_frequency': 0.0,
            'engagement_level': 'low',
            'loyalty_score': 0.5,
            'spending_tier': 'basic'
        }
        
        if not conversations:
            return indicators
        
        # Conversation frequency (conversations per month)
        if len(conversations) > 1:
            first_conv = datetime.fromisoformat(conversations[-1]['metadata']['timestamp'].replace('Z', '+00:00'))
            last_conv = datetime.fromisoformat(conversations[0]['metadata']['timestamp'].replace('Z', '+00:00'))
            months = max(1, (last_conv - first_conv).days / 30)
            indicators['conversation_frequency'] = len(conversations) / months
        
        # Engagement level based on conversation length and frequency
        avg_length = np.mean([len(conv['text']) for conv in conversations])
        if avg_length > 100 and len(conversations) > 5:
            indicators['engagement_level'] = 'high'
        elif avg_length > 50 or len(conversations) > 3:
            indicators['engagement_level'] = 'medium'
        
        # Loyalty score based on positive sentiment and repeat interactions
        positive_count = sum(1 for conv in conversations 
                           if conv['metadata'].get('sentiment') == 'positive')
        if len(conversations) > 0:
            indicators['loyalty_score'] = min(1.0, positive_count / len(conversations) + 
                                            len(conversations) / 20)
        
        return indicators
    
    def _assess_risk_factors(self, conversations: List[Dict]) -> Dict[str, float]:
        """Assess customer risk factors"""
        
        risks = {
            'churn_risk': 0.5,
            'satisfaction_risk': 0.5,
            'payment_risk': 0.5
        }
        
        if not conversations:
            return risks
        
        # Churn risk: long time since last interaction, declining frequency
        last_interaction = datetime.fromisoformat(
            conversations[0]['metadata']['timestamp'].replace('Z', '+00:00')
        )
        days_since_last = (datetime.now(timezone.utc) - last_interaction).days
        
        if days_since_last > 90:
            risks['churn_risk'] = 0.8
        elif days_since_last > 30:
            risks['churn_risk'] = 0.6
        else:
            risks['churn_risk'] = 0.2
        
        # Satisfaction risk: negative sentiment trend
        recent_sentiments = [
            conv['metadata'].get('sentiment') 
            for conv in conversations[:5]  # Last 5 conversations
            if conv['metadata'].get('sentiment')
        ]
        
        if recent_sentiments:
            negative_ratio = sum(1 for s in recent_sentiments if s == 'negative') / len(recent_sentiments)
            risks['satisfaction_risk'] = negative_ratio
        
        return risks
    
    def merge_profiles(self, profile1: CustomerProfile, profile2: CustomerProfile) -> CustomerProfile:
        """Merge two customer profiles when same customer identified across channels"""
        
        logger.info(f"Merging profiles: {profile1.customer_id} and {profile2.customer_id}")
        
        # Use the profile with more data as base
        if len(profile1.email_addresses) + len(profile1.phone_numbers) >= \
           len(profile2.email_addresses) + len(profile2.phone_numbers):
            primary = profile1
            secondary = profile2
        else:
            primary = profile2
            secondary = profile1
        
        # Merge contact information
        primary.email_addresses = list(set(primary.email_addresses + secondary.email_addresses))
        primary.phone_numbers = list(set(primary.phone_numbers + secondary.phone_numbers))
        primary.alternative_names = list(set(primary.alternative_names + secondary.alternative_names))
        
        if not primary.primary_name and secondary.primary_name:
            primary.primary_name = secondary.primary_name
        
        # Merge preferences (weighted average based on confidence)
        primary.confidence_score = (primary.confidence_score + secondary.confidence_score) / 2
        
        # Update metadata
        primary.updated_at = datetime.now(timezone.utc).isoformat()
        
        return primary
    
    def get_profile(self, customer_id: str) -> Optional[CustomerProfile]:
        """Get cached customer profile"""
        return self.profiles_cache.get(customer_id)
    
    def save_profile(self, profile: CustomerProfile) -> bool:
        """Save profile to persistent storage (placeholder for future database integration)"""
        try:
            # For now, just update cache
            self.profiles_cache[profile.customer_id] = profile
            logger.info(f"✅ Profile saved for {profile.customer_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save profile: {e}")
            return False

# Convenience function
def get_profile_builder(memory_manager: MemoryEmbeddingsManager = None) -> CustomerProfileBuilder:
    """Get initialized customer profile builder"""
    if memory_manager is None:
        from memory_embeddings_manager import get_memory_manager
        memory_manager = get_memory_manager()
    
    return CustomerProfileBuilder(memory_manager)