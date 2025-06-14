"""
Memory Analytics for Karen AI
Advanced customer insight generation and pattern analysis

Provides intelligent analytics by:
- Analyzing customer behavior patterns across all channels
- Identifying service request trends and patterns
- VIP customer identification and value scoring
- Churn risk detection and early warning systems
- Operational insights for business optimization
- Predictive analytics for proactive service
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from memory_embeddings_manager import MemoryEmbeddingsManager
from customer_profile_builder import CustomerProfileBuilder, CustomerProfile

logger = logging.getLogger(__name__)

@dataclass
class CustomerInsight:
    """Individual customer insight with confidence scoring"""
    customer_id: str
    insight_type: str  # behavior, preference, risk, value
    title: str
    description: str
    confidence: float
    impact: str  # low, medium, high
    actionable: bool
    created_at: str
    data_points: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data_points is None:
            self.data_points = {}
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

@dataclass
class CustomerSegment:
    """Customer segment with characteristics"""
    segment_id: str
    name: str
    description: str
    customer_count: int
    characteristics: Dict[str, Any]
    typical_behavior: List[str]
    recommended_actions: List[str]
    value_score: float
    
@dataclass
class BusinessInsight:
    """Business-level operational insight"""
    insight_id: str
    category: str  # operational, customer_service, product, trend
    title: str
    description: str
    impact_level: str  # low, medium, high, critical
    affected_customers: int
    recommendation: str
    data_source: str
    created_at: str
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

class CustomerBehaviorAnalyzer:
    """Analyzes individual customer behavior patterns"""
    
    def __init__(self, memory_manager: MemoryEmbeddingsManager):
        self.memory_manager = memory_manager
    
    def analyze_customer_behavior(self, customer_id: str) -> List[CustomerInsight]:
        """
        Analyze individual customer behavior patterns
        
        Args:
            customer_id: Customer to analyze
            
        Returns:
            List of behavioral insights
        """
        insights = []
        
        try:
            # Get customer conversations
            conversations = self.memory_manager.get_customer_conversations(
                customer_id=customer_id,
                limit=200
            )
            
            if not conversations:
                return insights
            
            # Analyze communication patterns
            insights.extend(self._analyze_communication_patterns(customer_id, conversations))
            
            # Analyze service patterns
            insights.extend(self._analyze_service_patterns(customer_id, conversations))
            
            # Analyze satisfaction trends
            insights.extend(self._analyze_satisfaction_trends(customer_id, conversations))
            
            # Analyze timing patterns
            insights.extend(self._analyze_timing_patterns(customer_id, conversations))
            
            logger.info(f"✅ Generated {len(insights)} insights for customer {customer_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze customer behavior: {e}")
        
        return insights
    
    def _analyze_communication_patterns(self, customer_id: str, conversations: List[Dict]) -> List[CustomerInsight]:
        """Analyze how customer prefers to communicate"""
        insights = []
        
        # Channel preferences
        channels = [conv['metadata'].get('channel', 'unknown') for conv in conversations]
        channel_counts = Counter(channels)
        
        if len(channel_counts) > 1:
            preferred_channel = channel_counts.most_common(1)[0][0]
            usage_percent = channel_counts[preferred_channel] / len(conversations) * 100
            
            if usage_percent > 70:
                insights.append(CustomerInsight(
                    customer_id=customer_id,
                    insight_type="preference",
                    title=f"Strong {preferred_channel} preference",
                    description=f"Customer uses {preferred_channel} for {usage_percent:.0f}% of communications",
                    confidence=min(0.9, usage_percent / 100),
                    impact="medium",
                    actionable=True,
                    data_points={"preferred_channel": preferred_channel, "usage_percent": usage_percent}
                ))
        
        # Response time patterns
        response_times = []
        for i in range(1, len(conversations)):
            if (conversations[i-1]['metadata'].get('direction') == 'outbound' and 
                conversations[i]['metadata'].get('direction') == 'inbound'):
                
                prev_time = datetime.fromisoformat(conversations[i-1]['metadata']['timestamp'].replace('Z', '+00:00'))
                curr_time = datetime.fromisoformat(conversations[i]['metadata']['timestamp'].replace('Z', '+00:00'))
                
                response_hours = (curr_time - prev_time).total_seconds() / 3600
                if response_hours < 48:  # Only count responses within 48 hours
                    response_times.append(response_hours)
        
        if response_times:
            avg_response = np.mean(response_times)
            if avg_response < 2:
                insights.append(CustomerInsight(
                    customer_id=customer_id,
                    insight_type="behavior",
                    title="Very responsive customer",
                    description=f"Average response time: {avg_response:.1f} hours",
                    confidence=0.8,
                    impact="low",
                    actionable=True,
                    data_points={"avg_response_hours": avg_response}
                ))
            elif avg_response > 24:
                insights.append(CustomerInsight(
                    customer_id=customer_id,
                    insight_type="behavior",
                    title="Slow to respond",
                    description=f"Average response time: {avg_response:.1f} hours. May need follow-up.",
                    confidence=0.7,
                    impact="medium",
                    actionable=True,
                    data_points={"avg_response_hours": avg_response}
                ))
        
        return insights
    
    def _analyze_service_patterns(self, customer_id: str, conversations: List[Dict]) -> List[CustomerInsight]:
        """Analyze customer service request patterns"""
        insights = []
        
        # Service request frequency
        service_requests = [
            conv for conv in conversations 
            if conv['metadata'].get('intent') == 'service_request'
        ]
        
        if len(service_requests) > 3:
            # Calculate request frequency
            if len(service_requests) > 1:
                first_request = datetime.fromisoformat(service_requests[-1]['metadata']['timestamp'].replace('Z', '+00:00'))
                last_request = datetime.fromisoformat(service_requests[0]['metadata']['timestamp'].replace('Z', '+00:00'))
                
                months = max(1, (last_request - first_request).days / 30)
                requests_per_month = len(service_requests) / months
                
                if requests_per_month > 2:
                    insights.append(CustomerInsight(
                        customer_id=customer_id,
                        insight_type="behavior",
                        title="High service usage",
                        description=f"{requests_per_month:.1f} service requests per month",
                        confidence=0.8,
                        impact="high",
                        actionable=True,
                        data_points={"requests_per_month": requests_per_month, "total_requests": len(service_requests)}
                    ))
        
        # Service type analysis
        service_texts = [req['text'].lower() for req in service_requests]
        service_types = defaultdict(int)
        
        type_keywords = {
            'plumbing': ['faucet', 'sink', 'pipe', 'leak', 'drain', 'toilet', 'water'],
            'electrical': ['outlet', 'light', 'switch', 'wire', 'electrical', 'power'],
            'maintenance': ['maintain', 'check', 'inspect', 'service', 'tune'],
            'emergency': ['emergency', 'urgent', 'broken', 'not working']
        }
        
        for text in service_texts:
            for service_type, keywords in type_keywords.items():
                if any(keyword in text for keyword in keywords):
                    service_types[service_type] += 1
        
        if service_types:
            most_common_service = max(service_types, key=service_types.get)
            if service_types[most_common_service] > 2:
                insights.append(CustomerInsight(
                    customer_id=customer_id,
                    insight_type="preference",
                    title=f"Frequent {most_common_service} issues",
                    description=f"Customer has {service_types[most_common_service]} {most_common_service} requests",
                    confidence=0.7,
                    impact="medium",
                    actionable=True,
                    data_points={"service_type": most_common_service, "frequency": service_types[most_common_service]}
                ))
        
        return insights
    
    def _analyze_satisfaction_trends(self, customer_id: str, conversations: List[Dict]) -> List[CustomerInsight]:
        """Analyze customer satisfaction trends over time"""
        insights = []
        
        # Get conversations with sentiment
        sentiment_convs = [
            conv for conv in conversations
            if conv['metadata'].get('sentiment') in ['positive', 'negative', 'neutral']
        ]
        
        if len(sentiment_convs) < 3:
            return insights
        
        # Analyze recent vs historical sentiment
        recent_convs = sentiment_convs[:5]  # Last 5 conversations
        historical_convs = sentiment_convs[5:] if len(sentiment_convs) > 5 else []
        
        recent_negative = sum(1 for conv in recent_convs if conv['metadata']['sentiment'] == 'negative')
        recent_positive = sum(1 for conv in recent_convs if conv['metadata']['sentiment'] == 'positive')
        
        if historical_convs:
            historical_negative = sum(1 for conv in historical_convs if conv['metadata']['sentiment'] == 'negative')
            historical_positive = sum(1 for conv in historical_convs if conv['metadata']['sentiment'] == 'positive')
            
            recent_negative_ratio = recent_negative / len(recent_convs)
            historical_negative_ratio = historical_negative / len(historical_convs) if historical_convs else 0
            
            # Detect satisfaction decline
            if recent_negative_ratio > 0.4 and recent_negative_ratio > historical_negative_ratio + 0.2:
                insights.append(CustomerInsight(
                    customer_id=customer_id,
                    insight_type="risk",
                    title="Declining satisfaction",
                    description=f"Recent negative sentiment: {recent_negative_ratio:.0%} vs historical: {historical_negative_ratio:.0%}",
                    confidence=0.8,
                    impact="high",
                    actionable=True,
                    data_points={
                        "recent_negative_ratio": recent_negative_ratio,
                        "historical_negative_ratio": historical_negative_ratio
                    }
                ))
            
            # Detect satisfaction improvement
            elif recent_positive / len(recent_convs) > 0.6 and recent_negative_ratio < historical_negative_ratio:
                insights.append(CustomerInsight(
                    customer_id=customer_id,
                    insight_type="value",
                    title="Improving satisfaction",
                    description=f"Recent positive trend: {recent_positive}/{len(recent_convs)} positive interactions",
                    confidence=0.7,
                    impact="medium",
                    actionable=False,
                    data_points={"recent_positive_ratio": recent_positive / len(recent_convs)}
                ))
        
        return insights
    
    def _analyze_timing_patterns(self, customer_id: str, conversations: List[Dict]) -> List[CustomerInsight]:
        """Analyze when customer typically communicates"""
        insights = []
        
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
        
        if len(hours) > 5:
            # Analyze preferred hours
            hour_counts = Counter(hours)
            peak_hour = hour_counts.most_common(1)[0][0]
            peak_count = hour_counts[peak_hour]
            
            if peak_count > len(hours) * 0.3:  # 30% of communications in one hour
                if 9 <= peak_hour <= 17:
                    time_desc = "business hours"
                elif 18 <= peak_hour <= 22:
                    time_desc = "evening"
                else:
                    time_desc = "off-hours"
                
                insights.append(CustomerInsight(
                    customer_id=customer_id,
                    insight_type="preference",
                    title=f"Prefers {time_desc} communication",
                    description=f"Most active at {peak_hour}:00 ({peak_count}/{len(hours)} interactions)",
                    confidence=0.7,
                    impact="low",
                    actionable=True,
                    data_points={"peak_hour": peak_hour, "time_category": time_desc}
                ))
        
        if len(days) > 5:
            # Analyze preferred days
            weekday_count = sum(1 for day in days if day < 5)
            weekend_count = len(days) - weekday_count
            
            if weekend_count > weekday_count and weekend_count > len(days) * 0.6:
                insights.append(CustomerInsight(
                    customer_id=customer_id,
                    insight_type="preference",
                    title="Weekend communicator",
                    description=f"Prefers weekend communication ({weekend_count}/{len(days)} interactions)",
                    confidence=0.6,
                    impact="low",
                    actionable=True,
                    data_points={"weekend_ratio": weekend_count / len(days)}
                ))
        
        return insights

class CustomerSegmentationEngine:
    """Segments customers based on behavior and value"""
    
    def __init__(self, memory_manager: MemoryEmbeddingsManager, profile_builder: CustomerProfileBuilder):
        self.memory_manager = memory_manager
        self.profile_builder = profile_builder
    
    def segment_customers(self, customer_ids: List[str] = None) -> List[CustomerSegment]:
        """
        Segment customers based on behavior and value patterns
        
        Args:
            customer_ids: Specific customers to segment (if None, segments all)
            
        Returns:
            List of customer segments
        """
        try:
            # Get all customers if not specified
            if customer_ids is None:
                customer_ids = self._get_all_customer_ids()
            
            if len(customer_ids) < 10:
                logger.warning(f"Too few customers ({len(customer_ids)}) for meaningful segmentation")
                return []
            
            # Build feature matrix for clustering
            feature_matrix, feature_names = self._build_feature_matrix(customer_ids)
            
            if feature_matrix is None or len(feature_matrix) == 0:
                return []
            
            # Perform clustering
            segments = self._perform_clustering(feature_matrix, customer_ids, feature_names)
            
            logger.info(f"✅ Created {len(segments)} customer segments")
            return segments
            
        except Exception as e:
            logger.error(f"❌ Failed to segment customers: {e}")
            return []
    
    def _get_all_customer_ids(self) -> List[str]:
        """Get all unique customer IDs from conversations"""
        try:
            # Sample conversations to get customer IDs
            results = self.memory_manager.collection.get(limit=5000)
            
            customer_ids = set()
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if metadata.get('customer_id'):
                        customer_ids.add(metadata['customer_id'])
            
            return list(customer_ids)
            
        except Exception as e:
            logger.error(f"Failed to get customer IDs: {e}")
            return []
    
    def _build_feature_matrix(self, customer_ids: List[str]) -> Tuple[Optional[np.ndarray], List[str]]:
        """Build feature matrix for customer clustering"""
        
        features = []
        feature_names = [
            'conversation_count', 'avg_response_time', 'service_requests',
            'satisfaction_score', 'channel_diversity', 'recency_days',
            'urgency_ratio', 'weekend_ratio', 'business_hours_ratio'
        ]
        
        for customer_id in customer_ids:
            try:
                # Get customer conversations
                conversations = self.memory_manager.get_customer_conversations(
                    customer_id=customer_id,
                    limit=100
                )
                
                if not conversations:
                    continue
                
                # Extract features
                customer_features = self._extract_customer_features(conversations)
                features.append(customer_features)
                
            except Exception as e:
                logger.warning(f"Failed to extract features for {customer_id}: {e}")
                continue
        
        if not features:
            return None, feature_names
        
        # Convert to numpy array and normalize
        feature_matrix = np.array(features)
        scaler = StandardScaler()
        normalized_features = scaler.fit_transform(feature_matrix)
        
        return normalized_features, feature_names
    
    def _extract_customer_features(self, conversations: List[Dict]) -> List[float]:
        """Extract numerical features from customer conversations"""
        
        # Basic counts
        conversation_count = len(conversations)
        service_requests = sum(1 for conv in conversations 
                             if conv['metadata'].get('intent') == 'service_request')
        
        # Response time analysis
        response_times = []
        for i in range(1, len(conversations)):
            if (conversations[i-1]['metadata'].get('direction') == 'outbound' and 
                conversations[i]['metadata'].get('direction') == 'inbound'):
                
                prev_time = datetime.fromisoformat(conversations[i-1]['metadata']['timestamp'].replace('Z', '+00:00'))
                curr_time = datetime.fromisoformat(conversations[i]['metadata']['timestamp'].replace('Z', '+00:00'))
                
                response_hours = (curr_time - prev_time).total_seconds() / 3600
                if response_hours < 48:
                    response_times.append(response_hours)
        
        avg_response_time = np.mean(response_times) if response_times else 24
        
        # Satisfaction score
        sentiments = [conv['metadata'].get('sentiment') for conv in conversations 
                     if conv['metadata'].get('sentiment')]
        
        if sentiments:
            positive_count = sum(1 for s in sentiments if s == 'positive')
            satisfaction_score = positive_count / len(sentiments)
        else:
            satisfaction_score = 0.5
        
        # Channel diversity
        channels = set(conv['metadata'].get('channel', 'unknown') for conv in conversations)
        channel_diversity = len(channels)
        
        # Recency
        if conversations:
            last_conv = datetime.fromisoformat(conversations[0]['metadata']['timestamp'].replace('Z', '+00:00'))
            recency_days = (datetime.now(timezone.utc) - last_conv).days
        else:
            recency_days = 365
        
        # Urgency ratio
        urgent_count = sum(1 for conv in conversations 
                          if conv['metadata'].get('urgency') in ['high', 'critical'])
        urgency_ratio = urgent_count / conversation_count if conversation_count > 0 else 0
        
        # Time patterns
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
        
        # Weekend ratio
        weekend_count = sum(1 for day in days if day >= 5)
        weekend_ratio = weekend_count / len(days) if days else 0
        
        # Business hours ratio
        business_hours_count = sum(1 for hour in hours if 9 <= hour <= 17)
        business_hours_ratio = business_hours_count / len(hours) if hours else 0
        
        return [
            conversation_count,
            avg_response_time,
            service_requests,
            satisfaction_score,
            channel_diversity,
            recency_days,
            urgency_ratio,
            weekend_ratio,
            business_hours_ratio
        ]
    
    def _perform_clustering(
        self, 
        feature_matrix: np.ndarray, 
        customer_ids: List[str], 
        feature_names: List[str]
    ) -> List[CustomerSegment]:
        """Perform K-means clustering on customer features"""
        
        # Determine optimal number of clusters (3-6 for business usefulness)
        n_clusters = min(6, max(3, len(customer_ids) // 20))
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(feature_matrix)
        
        segments = []
        
        for cluster_id in range(n_clusters):
            # Get customers in this cluster
            cluster_mask = cluster_labels == cluster_id
            cluster_customers = [customer_ids[i] for i in range(len(customer_ids)) if cluster_mask[i]]
            
            if not cluster_customers:
                continue
            
            # Analyze cluster characteristics
            cluster_features = feature_matrix[cluster_mask]
            avg_features = np.mean(cluster_features, axis=0)
            
            # Create segment
            segment = self._create_segment_from_cluster(
                cluster_id, 
                cluster_customers, 
                avg_features, 
                feature_names
            )
            
            segments.append(segment)
        
        return segments
    
    def _create_segment_from_cluster(
        self, 
        cluster_id: int, 
        customers: List[str], 
        avg_features: np.ndarray, 
        feature_names: List[str]
    ) -> CustomerSegment:
        """Create a customer segment from cluster analysis"""
        
        # Map features back to interpretable characteristics
        characteristics = dict(zip(feature_names, avg_features))
        
        # Determine segment type based on features
        conversation_count = characteristics['conversation_count']
        satisfaction_score = characteristics['satisfaction_score']
        service_requests = characteristics['service_requests']
        recency_days = characteristics['recency_days']
        
        # Segment naming logic
        if satisfaction_score > 0.7 and conversation_count > 5:
            if service_requests > 3:
                segment_name = "VIP Heavy Users"
                description = "High-value customers with frequent service needs and high satisfaction"
                value_score = 0.9
            else:
                segment_name = "Happy Loyalists"
                description = "Satisfied customers with regular but moderate usage"
                value_score = 0.8
        elif satisfaction_score < 0.4:
            segment_name = "At-Risk Customers"
            description = "Customers with low satisfaction requiring attention"
            value_score = 0.3
        elif recency_days > 90:
            segment_name = "Dormant Customers"
            description = "Previously active customers who haven't engaged recently"
            value_score = 0.4
        elif conversation_count < 3:
            segment_name = "New Customers"
            description = "Recent customers with limited interaction history"
            value_score = 0.6
        else:
            segment_name = f"Segment {cluster_id + 1}"
            description = "Mixed customer segment with average characteristics"
            value_score = 0.5
        
        # Generate behavioral insights
        typical_behavior = []
        if characteristics['avg_response_time'] < 4:
            typical_behavior.append("Quick to respond")
        if characteristics['channel_diversity'] > 2:
            typical_behavior.append("Uses multiple channels")
        if characteristics['urgency_ratio'] > 0.2:
            typical_behavior.append("Often urgent requests")
        if characteristics['weekend_ratio'] > 0.3:
            typical_behavior.append("Weekend communicator")
        
        # Generate recommendations
        recommendations = []
        if "At-Risk" in segment_name:
            recommendations.extend([
                "Proactive outreach to address concerns",
                "Priority customer service handling",
                "Satisfaction survey and feedback collection"
            ])
        elif "VIP" in segment_name:
            recommendations.extend([
                "Dedicated account management",
                "Premium service offerings",
                "Loyalty program enrollment"
            ])
        elif "Dormant" in segment_name:
            recommendations.extend([
                "Re-engagement campaigns",
                "Special offers to encourage return",
                "Check-in on previous services"
            ])
        else:
            recommendations.extend([
                "Regular satisfaction monitoring",
                "Personalized communication",
                "Service optimization"
            ])
        
        return CustomerSegment(
            segment_id=f"segment_{cluster_id}",
            name=segment_name,
            description=description,
            customer_count=len(customers),
            characteristics=characteristics,
            typical_behavior=typical_behavior,
            recommended_actions=recommendations,
            value_score=value_score
        )

class BusinessInsightsGenerator:
    """Generates business-level operational insights"""
    
    def __init__(self, memory_manager: MemoryEmbeddingsManager):
        self.memory_manager = memory_manager
    
    def generate_business_insights(self, days_back: int = 30) -> List[BusinessInsight]:
        """
        Generate business-level insights from conversation data
        
        Args:
            days_back: Days of data to analyze
            
        Returns:
            List of business insights
        """
        insights = []
        
        try:
            # Get recent conversations
            start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            # Sample recent conversations for analysis
            results = self.memory_manager.collection.get(
                limit=2000,
                where={
                    "timestamp": {"$gte": start_date.isoformat()}
                } if hasattr(self.memory_manager.collection, 'get') else None
            )
            
            if not results['documents']:
                return insights
            
            conversations = []
            for i in range(len(results['documents'])):
                conversations.append({
                    'id': results['ids'][i],
                    'text': results['documents'][i],
                    'metadata': results['metadatas'][i]
                })
            
            # Generate different types of insights
            insights.extend(self._analyze_service_trends(conversations, days_back))
            insights.extend(self._analyze_satisfaction_trends(conversations, days_back))
            insights.extend(self._analyze_operational_efficiency(conversations, days_back))
            insights.extend(self._analyze_channel_performance(conversations, days_back))
            
            logger.info(f"✅ Generated {len(insights)} business insights")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate business insights: {e}")
        
        return insights
    
    def _analyze_service_trends(self, conversations: List[Dict], days_back: int) -> List[BusinessInsight]:
        """Analyze service request trends and patterns"""
        insights = []
        
        # Filter service requests
        service_requests = [
            conv for conv in conversations 
            if conv['metadata'].get('intent') == 'service_request'
        ]
        
        if len(service_requests) < 10:
            return insights
        
        # Analyze service types
        service_types = defaultdict(int)
        type_keywords = {
            'plumbing': ['faucet', 'sink', 'pipe', 'leak', 'drain', 'toilet', 'water'],
            'electrical': ['outlet', 'light', 'switch', 'wire', 'electrical', 'power'],
            'maintenance': ['maintain', 'check', 'inspect', 'service', 'tune'],
            'emergency': ['emergency', 'urgent', 'broken', 'not working']
        }
        
        for request in service_requests:
            text = request['text'].lower()
            for service_type, keywords in type_keywords.items():
                if any(keyword in text for keyword in keywords):
                    service_types[service_type] += 1
                    break
        
        # Find trending service types
        total_requests = len(service_requests)
        for service_type, count in service_types.items():
            percentage = count / total_requests * 100
            
            if percentage > 30:  # More than 30% of requests
                insights.append(BusinessInsight(
                    insight_id=f"service_trend_{service_type}",
                    category="operational",
                    title=f"High demand for {service_type} services",
                    description=f"{percentage:.0f}% of service requests are {service_type}-related ({count}/{total_requests})",
                    impact_level="medium" if percentage > 50 else "low",
                    affected_customers=count,
                    recommendation=f"Consider expanding {service_type} capacity or training",
                    data_source=f"Last {days_back} days of service requests",
                    metrics={
                        "service_type": service_type,
                        "request_count": count,
                        "percentage": percentage
                    }
                ))
        
        # Analyze request frequency trends
        daily_requests = defaultdict(int)
        for request in service_requests:
            timestamp = datetime.fromisoformat(request['metadata']['timestamp'].replace('Z', '+00:00'))
            date_key = timestamp.date().isoformat()
            daily_requests[date_key] += 1
        
        if len(daily_requests) > 7:  # Need at least a week of data
            daily_counts = list(daily_requests.values())
            avg_daily = np.mean(daily_counts)
            recent_avg = np.mean(daily_counts[-7:])  # Last week average
            
            if recent_avg > avg_daily * 1.5:
                insights.append(BusinessInsight(
                    insight_id="service_volume_spike",
                    category="operational",
                    title="Service request volume spike",
                    description=f"Recent daily average ({recent_avg:.1f}) is 50% higher than period average ({avg_daily:.1f})",
                    impact_level="high",
                    affected_customers=int(recent_avg * 7),
                    recommendation="Monitor capacity and consider additional staffing",
                    data_source=f"Last {days_back} days of service requests",
                    metrics={
                        "avg_daily_requests": avg_daily,
                        "recent_avg_daily": recent_avg,
                        "increase_percentage": (recent_avg / avg_daily - 1) * 100
                    }
                ))
        
        return insights
    
    def _analyze_satisfaction_trends(self, conversations: List[Dict], days_back: int) -> List[BusinessInsight]:
        """Analyze customer satisfaction trends"""
        insights = []
        
        # Get conversations with sentiment
        sentiment_convs = [
            conv for conv in conversations
            if conv['metadata'].get('sentiment') in ['positive', 'negative', 'neutral']
        ]
        
        if len(sentiment_convs) < 20:
            return insights
        
        # Calculate overall satisfaction
        negative_count = sum(1 for conv in sentiment_convs if conv['metadata']['sentiment'] == 'negative')
        negative_rate = negative_count / len(sentiment_convs)
        
        if negative_rate > 0.3:  # More than 30% negative
            insights.append(BusinessInsight(
                insight_id="high_negative_sentiment",
                category="customer_service",
                title="High negative sentiment rate",
                description=f"{negative_rate:.0%} of recent interactions have negative sentiment",
                impact_level="high" if negative_rate > 0.5 else "medium",
                affected_customers=negative_count,
                recommendation="Review recent service quality and address common complaints",
                data_source=f"Last {days_back} days of conversations",
                metrics={
                    "negative_rate": negative_rate,
                    "total_conversations": len(sentiment_convs),
                    "negative_count": negative_count
                }
            ))
        
        # Trend analysis (compare first half vs second half of period)
        mid_point = len(sentiment_convs) // 2
        first_half = sentiment_convs[mid_point:]  # Older conversations
        second_half = sentiment_convs[:mid_point]  # Recent conversations
        
        if len(first_half) > 10 and len(second_half) > 10:
            first_negative_rate = sum(1 for conv in first_half if conv['metadata']['sentiment'] == 'negative') / len(first_half)
            second_negative_rate = sum(1 for conv in second_half if conv['metadata']['sentiment'] == 'negative') / len(second_half)
            
            if second_negative_rate > first_negative_rate + 0.15:  # 15% increase in negative sentiment
                insights.append(BusinessInsight(
                    insight_id="deteriorating_satisfaction",
                    category="customer_service",
                    title="Deteriorating customer satisfaction",
                    description=f"Negative sentiment increased from {first_negative_rate:.0%} to {second_negative_rate:.0%}",
                    impact_level="high",
                    affected_customers=len(second_half),
                    recommendation="Immediate investigation into service quality issues",
                    data_source=f"Trend analysis over last {days_back} days",
                    metrics={
                        "early_negative_rate": first_negative_rate,
                        "recent_negative_rate": second_negative_rate,
                        "change": second_negative_rate - first_negative_rate
                    }
                ))
        
        return insights
    
    def _analyze_operational_efficiency(self, conversations: List[Dict], days_back: int) -> List[BusinessInsight]:
        """Analyze operational efficiency metrics"""
        insights = []
        
        # Analyze response times (time between customer message and our response)
        response_times = []
        
        for i in range(1, len(conversations)):
            if (conversations[i]['metadata'].get('direction') == 'inbound' and 
                conversations[i-1]['metadata'].get('direction') == 'outbound'):
                
                customer_time = datetime.fromisoformat(conversations[i]['metadata']['timestamp'].replace('Z', '+00:00'))
                our_time = datetime.fromisoformat(conversations[i-1]['metadata']['timestamp'].replace('Z', '+00:00'))
                
                response_hours = (our_time - customer_time).total_seconds() / 3600
                if 0 < response_hours < 72:  # Valid response time
                    response_times.append(response_hours)
        
        if response_times:
            avg_response_time = np.mean(response_times)
            
            if avg_response_time > 24:  # Slow response time
                insights.append(BusinessInsight(
                    insight_id="slow_response_times",
                    category="operational",
                    title="Slow customer response times",
                    description=f"Average response time: {avg_response_time:.1f} hours",
                    impact_level="medium" if avg_response_time < 48 else "high",
                    affected_customers=len(response_times),
                    recommendation="Review staffing levels and response procedures",
                    data_source=f"Response time analysis over {days_back} days",
                    metrics={
                        "avg_response_hours": avg_response_time,
                        "total_responses": len(response_times)
                    }
                ))
        
        return insights
    
    def _analyze_channel_performance(self, conversations: List[Dict], days_back: int) -> List[BusinessInsight]:
        """Analyze performance across different communication channels"""
        insights = []
        
        # Group conversations by channel
        channel_data = defaultdict(list)
        for conv in conversations:
            channel = conv['metadata'].get('channel', 'unknown')
            channel_data[channel].append(conv)
        
        if len(channel_data) < 2:
            return insights
        
        # Analyze satisfaction by channel
        channel_satisfaction = {}
        for channel, convs in channel_data.items():
            sentiment_convs = [conv for conv in convs if conv['metadata'].get('sentiment')]
            if sentiment_convs:
                negative_count = sum(1 for conv in sentiment_convs if conv['metadata']['sentiment'] == 'negative')
                satisfaction_score = 1 - (negative_count / len(sentiment_convs))
                channel_satisfaction[channel] = {
                    'score': satisfaction_score,
                    'total': len(sentiment_convs),
                    'negative': negative_count
                }
        
        # Find problematic channels
        for channel, data in channel_satisfaction.items():
            if data['score'] < 0.6 and data['total'] > 10:  # Low satisfaction with significant volume
                insights.append(BusinessInsight(
                    insight_id=f"channel_satisfaction_{channel}",
                    category="customer_service",
                    title=f"Low satisfaction on {channel} channel",
                    description=f"{channel} has {data['score']:.0%} satisfaction rate ({data['negative']} negative / {data['total']} total)",
                    impact_level="medium",
                    affected_customers=data['total'],
                    recommendation=f"Review {channel} processes and training",
                    data_source=f"Channel analysis over {days_back} days",
                    metrics={
                        "channel": channel,
                        "satisfaction_score": data['score'],
                        "negative_interactions": data['negative'],
                        "total_interactions": data['total']
                    }
                ))
        
        return insights

class MemoryAnalytics:
    """Main analytics engine combining all analysis capabilities"""
    
    def __init__(self, memory_manager: MemoryEmbeddingsManager, profile_builder: CustomerProfileBuilder):
        self.memory_manager = memory_manager
        self.profile_builder = profile_builder
        self.behavior_analyzer = CustomerBehaviorAnalyzer(memory_manager)
        self.segmentation_engine = CustomerSegmentationEngine(memory_manager, profile_builder)
        self.business_insights = BusinessInsightsGenerator(memory_manager)
    
    def generate_comprehensive_analytics(self, customer_id: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive analytics report
        
        Args:
            customer_id: Specific customer to analyze (if None, analyzes all)
            
        Returns:
            Complete analytics report
        """
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'customer_insights': [],
            'customer_segments': [],
            'business_insights': [],
            'summary_metrics': {}
        }
        
        try:
            if customer_id:
                # Single customer analysis
                insights = self.behavior_analyzer.analyze_customer_behavior(customer_id)
                report['customer_insights'] = [asdict(insight) for insight in insights]
                
                # Get customer profile for metrics
                profile = self.profile_builder.build_profile(customer_id)
                conversations = self.memory_manager.get_customer_conversations(customer_id, limit=100)
                
                report['summary_metrics'] = {
                    'customer_id': customer_id,
                    'total_conversations': len(conversations),
                    'insights_generated': len(insights),
                    'satisfaction_score': np.mean(profile.service_history.satisfaction_scores) if profile.service_history.satisfaction_scores else 0,
                    'last_interaction': conversations[0]['metadata']['timestamp'] if conversations else None
                }
            
            else:
                # Full analytics
                
                # Customer segmentation
                segments = self.segmentation_engine.segment_customers()
                report['customer_segments'] = [asdict(segment) for segment in segments]
                
                # Business insights
                business_insights = self.business_insights.generate_business_insights()
                report['business_insights'] = [asdict(insight) for insight in business_insights]
                
                # Summary metrics
                stats = self.memory_manager.get_collection_stats()
                report['summary_metrics'] = {
                    'total_conversations': stats.get('total_conversations', 0),
                    'total_customers': stats.get('customer_count', 0),
                    'segments_created': len(segments),
                    'business_insights': len(business_insights),
                    'channels': stats.get('channels', [])
                }
            
            logger.info(f"✅ Generated comprehensive analytics report")
            return report
            
        except Exception as e:
            logger.error(f"❌ Failed to generate analytics: {e}")
            return report

# Convenience function
def get_memory_analytics(
    memory_manager: MemoryEmbeddingsManager = None,
    profile_builder: CustomerProfileBuilder = None
) -> MemoryAnalytics:
    """Get initialized memory analytics engine"""
    
    if memory_manager is None:
        from memory_embeddings_manager import get_memory_manager
        memory_manager = get_memory_manager()
    
    if profile_builder is None:
        from customer_profile_builder import get_profile_builder
        profile_builder = get_profile_builder(memory_manager)
    
    return MemoryAnalytics(memory_manager, profile_builder)

if __name__ == "__main__":
    # Example usage and testing
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize components
    from memory_embeddings_manager import get_memory_manager
    from customer_profile_builder import get_profile_builder
    
    memory_manager = get_memory_manager()
    profile_builder = get_profile_builder(memory_manager)
    analytics = MemoryAnalytics(memory_manager, profile_builder)
    
    # Generate comprehensive analytics
    report = analytics.generate_comprehensive_analytics()
    
    print("Analytics Report:")
    print(f"Total conversations: {report['summary_metrics'].get('total_conversations', 0)}")
    print(f"Customer segments: {report['summary_metrics'].get('segments_created', 0)}")
    print(f"Business insights: {report['summary_metrics'].get('business_insights', 0)}")
    
    # Example: Analyze specific customer
    if report['summary_metrics'].get('total_customers', 0) > 0:
        # This would analyze a specific customer if we had data
        customer_report = analytics.generate_comprehensive_analytics(customer_id="customer_123")
        print(f"\nCustomer insights: {customer_report['summary_metrics'].get('insights_generated', 0)}")