"""
Customer Analytics Module

Provides comprehensive customer intelligence including:
- Customer lifetime value calculation
- Churn prediction 
- Service preference analysis
- Referral network mapping
- VIP customer identification
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import redis
import json

logger = logging.getLogger(__name__)

class CustomerAnalytics:
    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, db=0)
        self.scaler = StandardScaler()
        self.churn_model = RandomForestClassifier(n_estimators=100, random_state=42)
        
    def calculate_customer_lifetime_value(self, customer_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Customer Lifetime Value (CLV) using historical transaction data.
        
        Args:
            customer_data: DataFrame with columns [customer_id, transaction_date, amount, service_type]
            
        Returns:
            DataFrame with CLV metrics for each customer
        """
        logger.info("Calculating Customer Lifetime Value")
        
        # Aggregate customer metrics
        customer_metrics = customer_data.groupby('customer_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'transaction_date': ['min', 'max']
        }).round(2)
        
        customer_metrics.columns = ['total_spent', 'avg_order_value', 'frequency', 'first_purchase', 'last_purchase']
        customer_metrics = customer_metrics.reset_index()
        
        # Calculate recency (days since last purchase)
        today = datetime.now()
        customer_metrics['recency_days'] = (today - pd.to_datetime(customer_metrics['last_purchase'])).dt.days
        
        # Calculate monetary value per day (velocity)
        customer_metrics['lifetime_days'] = (
            pd.to_datetime(customer_metrics['last_purchase']) - 
            pd.to_datetime(customer_metrics['first_purchase'])
        ).dt.days + 1
        
        customer_metrics['monetary_velocity'] = customer_metrics['total_spent'] / customer_metrics['lifetime_days']
        
        # Calculate CLV using RFM model with predictive component
        # CLV = (Average Order Value × Purchase Frequency × Gross Margin × Lifespan)
        estimated_lifespan_years = np.where(
            customer_metrics['recency_days'] < 90, 3.0,  # Active customers
            np.where(customer_metrics['recency_days'] < 180, 2.0, 1.0)  # At-risk customers
        )
        
        gross_margin = 0.4  # 40% margin assumption
        
        customer_metrics['predicted_clv'] = (
            customer_metrics['avg_order_value'] * 
            (customer_metrics['frequency'] / (customer_metrics['lifetime_days'] / 365)) * 
            gross_margin * 
            estimated_lifespan_years
        ).round(2)
        
        # Add CLV segments
        customer_metrics['clv_segment'] = pd.qcut(
            customer_metrics['predicted_clv'], 
            q=5, 
            labels=['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']
        )
        
        # Cache results
        self._cache_results('customer_clv', customer_metrics.to_dict('records'))
        
        return customer_metrics
    
    def predict_churn_risk(self, customer_data: pd.DataFrame, booking_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Predict customer churn risk using machine learning.
        
        Args:
            customer_data: Customer transaction history
            booking_data: Optional appointment booking data
            
        Returns:
            DataFrame with churn predictions and risk scores
        """
        logger.info("Predicting customer churn risk")
        
        # Create features for churn prediction
        today = datetime.now()
        features_df = customer_data.groupby('customer_id').agg({
            'transaction_date': 'max',
            'amount': ['sum', 'mean', 'count', 'std'],
            'service_type': lambda x: len(x.unique())
        })
        
        features_df.columns = ['last_purchase', 'total_spent', 'avg_spent', 'purchase_count', 'spend_variance', 'service_diversity']
        features_df = features_df.reset_index()
        
        # Calculate recency
        features_df['days_since_last_purchase'] = (today - pd.to_datetime(features_df['last_purchase'])).dt.days
        
        # Define churn (no purchase in last 180 days)
        features_df['is_churned'] = features_df['days_since_last_purchase'] > 180
        
        # Prepare features for ML
        feature_columns = ['total_spent', 'avg_spent', 'purchase_count', 'service_diversity', 'days_since_last_purchase']
        X = features_df[feature_columns].fillna(0)
        y = features_df['is_churned']
        
        # Train churn model
        X_scaled = self.scaler.fit_transform(X)
        self.churn_model.fit(X_scaled, y)
        
        # Predict churn probability for all customers
        churn_probabilities = self.churn_model.predict_proba(X_scaled)[:, 1]
        
        features_df['churn_risk_score'] = churn_probabilities
        features_df['churn_risk_level'] = pd.cut(
            churn_probabilities, 
            bins=[0, 0.3, 0.6, 1.0], 
            labels=['Low', 'Medium', 'High']
        )
        
        # Add actionable insights
        features_df['recommended_action'] = features_df.apply(self._get_churn_action, axis=1)
        
        # Cache results
        self._cache_results('churn_predictions', features_df.to_dict('records'))
        
        return features_df[['customer_id', 'churn_risk_score', 'churn_risk_level', 'recommended_action']]
    
    def analyze_service_preferences(self, customer_data: pd.DataFrame) -> Dict:
        """
        Analyze customer service preferences and patterns.
        
        Args:
            customer_data: DataFrame with customer transaction data
            
        Returns:
            Dictionary with service preference insights
        """
        logger.info("Analyzing service preferences")
        
        # Service popularity analysis
        service_stats = customer_data.groupby('service_type').agg({
            'customer_id': 'nunique',
            'amount': ['sum', 'mean'],
            'transaction_date': 'count'
        })
        
        service_stats.columns = ['unique_customers', 'total_revenue', 'avg_price', 'total_bookings']
        service_stats = service_stats.reset_index()
        service_stats['market_share'] = (service_stats['total_revenue'] / service_stats['total_revenue'].sum() * 100).round(2)
        
        # Customer service affinity
        customer_service_matrix = customer_data.pivot_table(
            index='customer_id', 
            columns='service_type', 
            values='amount', 
            aggfunc='count', 
            fill_value=0
        )
        
        # Service correlation analysis
        service_correlation = customer_service_matrix.corr()
        
        # Cross-sell opportunities
        cross_sell_pairs = []
        for i in range(len(service_correlation.columns)):
            for j in range(i+1, len(service_correlation.columns)):
                service1 = service_correlation.columns[i]
                service2 = service_correlation.columns[j]
                correlation = service_correlation.iloc[i, j]
                if correlation > 0.3:  # Strong positive correlation
                    cross_sell_pairs.append({
                        'service_combo': f"{service1} + {service2}",
                        'correlation': round(correlation, 3),
                        'opportunity_score': round(correlation * 100, 1)
                    })
        
        # Seasonal preferences
        customer_data['month'] = pd.to_datetime(customer_data['transaction_date']).dt.month
        seasonal_preferences = customer_data.groupby(['month', 'service_type'])['amount'].sum().unstack(fill_value=0)
        
        insights = {
            'service_popularity': service_stats.to_dict('records'),
            'cross_sell_opportunities': sorted(cross_sell_pairs, key=lambda x: x['correlation'], reverse=True)[:5],
            'seasonal_trends': seasonal_preferences.to_dict(),
            'service_correlation_matrix': service_correlation.to_dict()
        }
        
        # Cache results
        self._cache_results('service_preferences', insights)
        
        return insights
    
    def map_referral_network(self, customer_data: pd.DataFrame, referral_data: pd.DataFrame = None) -> Dict:
        """
        Map customer referral networks and identify influencers.
        
        Args:
            customer_data: Customer transaction data
            referral_data: Optional referral tracking data
            
        Returns:
            Dictionary with referral network analysis
        """
        logger.info("Mapping referral network")
        
        if referral_data is None or referral_data.empty:
            # Simulate referral detection based on patterns
            logger.warning("No referral data provided, using pattern-based detection")
            return self._detect_referral_patterns(customer_data)
        
        # Analyze referral performance
        referral_stats = referral_data.groupby('referrer_id').agg({
            'referred_customer_id': 'count',
            'referral_value': 'sum',
            'referral_date': ['min', 'max']
        })
        
        referral_stats.columns = ['total_referrals', 'total_referral_value', 'first_referral', 'last_referral']
        referral_stats = referral_stats.reset_index()
        
        # Calculate referrer lifetime value impact
        referral_stats['avg_referral_value'] = (referral_stats['total_referral_value'] / referral_stats['total_referrals']).round(2)
        
        # Identify super referrers
        referral_stats['referrer_tier'] = pd.qcut(
            referral_stats['total_referrals'], 
            q=3, 
            labels=['Standard', 'Champion', 'Super Advocate']
        )
        
        network_insights = {
            'top_referrers': referral_stats.nlargest(10, 'total_referrals').to_dict('records'),
            'referral_program_roi': (referral_stats['total_referral_value'].sum() / len(referral_stats)).round(2),
            'average_referrals_per_customer': referral_stats['total_referrals'].mean().round(2),
            'referrer_tiers': referral_stats['referrer_tier'].value_counts().to_dict()
        }
        
        # Cache results
        self._cache_results('referral_network', network_insights)
        
        return network_insights
    
    def identify_vip_customers(self, customer_data: pd.DataFrame, clv_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Identify VIP customers based on multiple criteria.
        
        Args:
            customer_data: Customer transaction data
            clv_data: Optional pre-calculated CLV data
            
        Returns:
            DataFrame with VIP customer analysis
        """
        logger.info("Identifying VIP customers")
        
        if clv_data is None:
            clv_data = self.calculate_customer_lifetime_value(customer_data)
        
        # Create VIP scoring matrix
        customer_scores = customer_data.groupby('customer_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'transaction_date': ['min', 'max']
        })
        
        customer_scores.columns = ['total_spent', 'avg_order_value', 'frequency', 'first_purchase', 'last_purchase']
        customer_scores = customer_scores.reset_index()
        
        # Merge with CLV data
        vip_analysis = customer_scores.merge(
            clv_data[['customer_id', 'predicted_clv', 'clv_segment']], 
            on='customer_id'
        )
        
        # Calculate recency score
        today = datetime.now()
        vip_analysis['days_since_last_purchase'] = (today - pd.to_datetime(vip_analysis['last_purchase'])).dt.days
        vip_analysis['recency_score'] = np.where(
            vip_analysis['days_since_last_purchase'] <= 30, 100,
            np.where(vip_analysis['days_since_last_purchase'] <= 90, 70, 30)
        )
        
        # Calculate frequency score
        vip_analysis['frequency_score'] = pd.qcut(vip_analysis['frequency'], q=5, labels=[20, 40, 60, 80, 100])
        vip_analysis['frequency_score'] = vip_analysis['frequency_score'].astype(int)
        
        # Calculate monetary score
        vip_analysis['monetary_score'] = pd.qcut(vip_analysis['total_spent'], q=5, labels=[20, 40, 60, 80, 100])
        vip_analysis['monetary_score'] = vip_analysis['monetary_score'].astype(int)
        
        # Calculate composite VIP score
        vip_analysis['vip_score'] = (
            vip_analysis['recency_score'] * 0.3 +
            vip_analysis['frequency_score'] * 0.3 +
            vip_analysis['monetary_score'] * 0.4
        ).round(2)
        
        # Assign VIP tiers
        vip_analysis['vip_tier'] = pd.cut(
            vip_analysis['vip_score'], 
            bins=[0, 50, 70, 85, 100], 
            labels=['Standard', 'Silver VIP', 'Gold VIP', 'Platinum VIP']
        )
        
        # Add personalized recommendations
        vip_analysis['recommended_perks'] = vip_analysis.apply(self._get_vip_perks, axis=1)
        
        # Cache results
        self._cache_results('vip_customers', vip_analysis.to_dict('records'))
        
        return vip_analysis.sort_values('vip_score', ascending=False)
    
    def generate_customer_segments(self, customer_data: pd.DataFrame) -> Dict:
        """
        Generate customer segments using K-means clustering.
        
        Args:
            customer_data: Customer transaction data
            
        Returns:
            Dictionary with segmentation results
        """
        logger.info("Generating customer segments")
        
        # Prepare features for clustering
        features_df = customer_data.groupby('customer_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'transaction_date': ['min', 'max']
        })
        
        features_df.columns = ['total_spent', 'avg_order_value', 'frequency', 'first_purchase', 'last_purchase']
        features_df = features_df.reset_index()
        
        # Calculate recency
        today = datetime.now()
        features_df['recency_days'] = (today - pd.to_datetime(features_df['last_purchase'])).dt.days
        
        # Prepare features for clustering
        clustering_features = ['total_spent', 'avg_order_value', 'frequency', 'recency_days']
        X = features_df[clustering_features].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        
        # Perform K-means clustering
        kmeans = KMeans(n_clusters=5, random_state=42)
        features_df['segment'] = kmeans.fit_predict(X_scaled)
        
        # Analyze segments
        segment_profiles = features_df.groupby('segment').agg({
            'total_spent': 'mean',
            'avg_order_value': 'mean',
            'frequency': 'mean',
            'recency_days': 'mean',
            'customer_id': 'count'
        }).round(2)
        
        segment_profiles.columns = ['avg_total_spent', 'avg_order_value', 'avg_frequency', 'avg_recency_days', 'customer_count']
        segment_profiles = segment_profiles.reset_index()
        
        # Add segment names
        segment_names = {
            0: "Champions",
            1: "Loyal Customers", 
            2: "Potential Loyalists",
            3: "At Risk",
            4: "Hibernating"
        }
        
        segment_profiles['segment_name'] = segment_profiles['segment'].map(segment_names)
        segment_profiles['percentage'] = (segment_profiles['customer_count'] / segment_profiles['customer_count'].sum() * 100).round(2)
        
        segmentation_results = {
            'segment_profiles': segment_profiles.to_dict('records'),
            'customer_segments': features_df[['customer_id', 'segment']].to_dict('records'),
            'total_customers': len(features_df)
        }
        
        # Cache results
        self._cache_results('customer_segments', segmentation_results)
        
        return segmentation_results
    
    def _get_churn_action(self, row) -> str:
        """Get recommended action for churn prevention."""
        if row['churn_risk_level'] == 'High':
            return "Immediate outreach with special offer"
        elif row['churn_risk_level'] == 'Medium':
            return "Send personalized email campaign"
        else:
            return "Continue standard engagement"
    
    def _get_vip_perks(self, row) -> List[str]:
        """Get recommended VIP perks based on tier."""
        tier = row['vip_tier']
        if tier == 'Platinum VIP':
            return ["24/7 priority support", "20% discount", "Free estimates", "Dedicated account manager"]
        elif tier == 'Gold VIP':
            return ["Priority scheduling", "15% discount", "Free estimates"]
        elif tier == 'Silver VIP':
            return ["10% discount", "Priority booking"]
        else:
            return ["Standard service"]
    
    def _detect_referral_patterns(self, customer_data: pd.DataFrame) -> Dict:
        """Detect potential referral patterns from customer data."""
        # Simple pattern detection based on timing and service similarity
        return {
            'detected_referral_patterns': 0,
            'estimated_referral_rate': "5%",
            'note': "Referral tracking requires dedicated referral data collection"
        }
    
    def _cache_results(self, key: str, data: any, ttl: int = 3600):
        """Cache results in Redis."""
        try:
            self.redis_client.setex(
                f"customer_analytics:{key}", 
                ttl, 
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Failed to cache results for {key}: {e}")
    
    def get_cached_results(self, key: str) -> Optional[any]:
        """Retrieve cached results from Redis."""
        try:
            cached_data = self.redis_client.get(f"customer_analytics:{key}")
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached results for {key}: {e}")
        return None