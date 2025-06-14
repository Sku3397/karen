"""
Revenue Intelligence Module

Provides comprehensive revenue analytics including:
- Quote-to-booking conversion rates
- Service profitability analysis  
- Seasonal revenue patterns
- Price optimization suggestions
- Payment delay patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import redis
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

class RevenueIntelligence:
    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, db=0)
        self.price_optimizer = RandomForestRegressor(n_estimators=100, random_state=42)
        
    def analyze_conversion_rates(self, quote_data: pd.DataFrame, booking_data: pd.DataFrame) -> Dict:
        """
        Analyze quote-to-booking conversion rates across different dimensions.
        
        Args:
            quote_data: DataFrame with columns [quote_id, customer_id, service_type, quote_amount, quote_date, status]
            booking_data: DataFrame with columns [booking_id, quote_id, booking_date, final_amount]
            
        Returns:
            Dictionary with conversion rate analysis
        """
        logger.info("Analyzing quote-to-booking conversion rates")
        
        # Merge quote and booking data
        conversion_df = quote_data.merge(booking_data, on='quote_id', how='left')
        conversion_df['converted'] = ~conversion_df['booking_id'].isna()
        
        # Overall conversion rate
        overall_conversion = conversion_df['converted'].mean() * 100
        
        # Conversion by service type
        service_conversion = conversion_df.groupby('service_type').agg({
            'converted': ['count', 'sum', 'mean'],
            'quote_amount': 'mean',
            'final_amount': 'mean'
        })
        
        service_conversion.columns = ['total_quotes', 'converted_quotes', 'conversion_rate', 'avg_quote_amount', 'avg_final_amount']
        service_conversion['conversion_rate'] = (service_conversion['conversion_rate'] * 100).round(2)
        service_conversion['price_variance'] = ((service_conversion['avg_final_amount'] - service_conversion['avg_quote_amount']) / service_conversion['avg_quote_amount'] * 100).round(2)
        service_conversion = service_conversion.reset_index()
        
        # Conversion by quote amount ranges
        conversion_df['quote_range'] = pd.cut(
            conversion_df['quote_amount'], 
            bins=[0, 200, 500, 1000, 2000, float('inf')], 
            labels=['$0-200', '$200-500', '$500-1000', '$1000-2000', '$2000+']
        )
        
        amount_conversion = conversion_df.groupby('quote_range')['converted'].agg(['count', 'sum', 'mean']).reset_index()
        amount_conversion.columns = ['quote_range', 'total_quotes', 'converted_quotes', 'conversion_rate']
        amount_conversion['conversion_rate'] = (amount_conversion['conversion_rate'] * 100).round(2)
        
        # Time-to-decision analysis
        conversion_df['quote_date'] = pd.to_datetime(conversion_df['quote_date'])
        conversion_df['booking_date'] = pd.to_datetime(conversion_df['booking_date'])
        converted_quotes = conversion_df[conversion_df['converted']]
        
        if not converted_quotes.empty:
            converted_quotes['decision_days'] = (converted_quotes['booking_date'] - converted_quotes['quote_date']).dt.days
            avg_decision_time = converted_quotes['decision_days'].mean()
            
            # Decision time distribution
            decision_distribution = converted_quotes['decision_days'].describe()
        else:
            avg_decision_time = 0
            decision_distribution = pd.Series()
        
        # Seasonal conversion patterns
        conversion_df['quote_month'] = conversion_df['quote_date'].dt.month
        monthly_conversion = conversion_df.groupby('quote_month')['converted'].agg(['count', 'mean']).reset_index()
        monthly_conversion.columns = ['month', 'total_quotes', 'conversion_rate']
        monthly_conversion['conversion_rate'] = (monthly_conversion['conversion_rate'] * 100).round(2)
        
        # Lost opportunity analysis
        lost_quotes = conversion_df[~conversion_df['converted']]
        lost_revenue = lost_quotes['quote_amount'].sum()
        
        conversion_insights = {
            'overall_conversion_rate': round(overall_conversion, 2),
            'total_quotes': len(conversion_df),
            'converted_quotes': conversion_df['converted'].sum(),
            'service_conversion_rates': service_conversion.to_dict('records'),
            'amount_range_conversion': amount_conversion.to_dict('records'),
            'average_decision_time_days': round(avg_decision_time, 1) if avg_decision_time else 0,
            'decision_time_distribution': decision_distribution.to_dict() if not decision_distribution.empty else {},
            'monthly_conversion_patterns': monthly_conversion.to_dict('records'),
            'lost_revenue_opportunity': round(lost_revenue, 2),
            'conversion_optimization_tips': self._generate_conversion_tips(service_conversion, amount_conversion)
        }
        
        # Cache results
        self._cache_results('conversion_rates', conversion_insights)
        
        return conversion_insights
    
    def analyze_service_profitability(self, transaction_data: pd.DataFrame, cost_data: pd.DataFrame = None) -> Dict:
        """
        Analyze profitability of different services.
        
        Args:
            transaction_data: DataFrame with revenue data
            cost_data: Optional cost breakdown data
            
        Returns:
            Dictionary with profitability analysis
        """
        logger.info("Analyzing service profitability")
        
        # Revenue analysis by service
        revenue_analysis = transaction_data.groupby('service_type').agg({
            'amount': ['sum', 'mean', 'count'],
            'transaction_date': ['min', 'max']
        })
        
        revenue_analysis.columns = ['total_revenue', 'avg_revenue_per_job', 'job_count', 'first_service', 'last_service']
        revenue_analysis = revenue_analysis.reset_index()
        
        # Calculate market share
        revenue_analysis['market_share_pct'] = (revenue_analysis['total_revenue'] / revenue_analysis['total_revenue'].sum() * 100).round(2)
        
        # Estimate costs if not provided
        if cost_data is None or cost_data.empty:
            logger.warning("No cost data provided, using estimated cost structure")
            cost_data = self._estimate_service_costs(revenue_analysis)
        
        # Merge with cost data
        profitability_df = revenue_analysis.merge(
            cost_data.groupby('service_type').agg({'cost_amount': ['sum', 'mean']}).reset_index(),
            on='service_type',
            how='left'
        )
        
        if 'cost_amount' in profitability_df.columns:
            profitability_df.columns = list(profitability_df.columns[:-2]) + ['total_costs', 'avg_cost_per_job']
            
            # Calculate profitability metrics
            profitability_df['gross_profit'] = profitability_df['total_revenue'] - profitability_df['total_costs']
            profitability_df['profit_margin_pct'] = (profitability_df['gross_profit'] / profitability_df['total_revenue'] * 100).round(2)
            profitability_df['profit_per_job'] = (profitability_df['gross_profit'] / profitability_df['job_count']).round(2)
        else:
            # Use estimated margins
            estimated_margins = {
                'Plumbing': 0.45,
                'Electrical': 0.50,
                'HVAC': 0.40,
                'General Handyman': 0.55,
                'Painting': 0.35,
                'Flooring': 0.30
            }
            
            profitability_df['estimated_margin_pct'] = profitability_df['service_type'].map(estimated_margins).fillna(0.45) * 100
            profitability_df['estimated_gross_profit'] = (profitability_df['total_revenue'] * profitability_df['estimated_margin_pct'] / 100).round(2)
        
        # Service performance ranking
        if 'profit_margin_pct' in profitability_df.columns:
            profitability_df['performance_score'] = (
                profitability_df['profit_margin_pct'] * 0.4 +
                profitability_df['market_share_pct'] * 0.3 +
                np.log(profitability_df['job_count']) * 10 * 0.3
            ).round(2)
        else:
            profitability_df['performance_score'] = (
                profitability_df['estimated_margin_pct'] * 0.4 +
                profitability_df['market_share_pct'] * 0.3 +
                np.log(profitability_df['job_count']) * 10 * 0.3
            ).round(2)
        
        # Identify opportunities
        high_volume_low_margin = profitability_df[
            (profitability_df['job_count'] > profitability_df['job_count'].median()) &
            (profitability_df.get('profit_margin_pct', profitability_df['estimated_margin_pct']) < 30)
        ]
        
        low_volume_high_margin = profitability_df[
            (profitability_df['job_count'] < profitability_df['job_count'].median()) &
            (profitability_df.get('profit_margin_pct', profitability_df['estimated_margin_pct']) > 50)
        ]
        
        profitability_insights = {
            'service_profitability': profitability_df.sort_values('performance_score', ascending=False).to_dict('records'),
            'total_revenue': profitability_df['total_revenue'].sum(),
            'total_jobs': profitability_df['job_count'].sum(),
            'avg_job_value': round(profitability_df['total_revenue'].sum() / profitability_df['job_count'].sum(), 2),
            'price_optimization_opportunities': high_volume_low_margin[['service_type', 'job_count', 'avg_revenue_per_job']].to_dict('records'),
            'growth_opportunities': low_volume_high_margin[['service_type', 'avg_revenue_per_job']].to_dict('records'),
            'top_performers': profitability_df.nlargest(3, 'performance_score')[['service_type', 'performance_score']].to_dict('records')
        }
        
        # Cache results
        self._cache_results('service_profitability', profitability_insights)
        
        return profitability_insights
    
    def analyze_seasonal_patterns(self, transaction_data: pd.DataFrame) -> Dict:
        """
        Analyze seasonal revenue patterns and trends.
        
        Args:
            transaction_data: DataFrame with transaction data
            
        Returns:
            Dictionary with seasonal analysis
        """
        logger.info("Analyzing seasonal revenue patterns")
        
        # Prepare data
        transaction_data['transaction_date'] = pd.to_datetime(transaction_data['transaction_date'])
        transaction_data['month'] = transaction_data['transaction_date'].dt.month
        transaction_data['quarter'] = transaction_data['transaction_date'].dt.quarter
        transaction_data['day_of_week'] = transaction_data['transaction_date'].dt.day_name()
        transaction_data['week_of_year'] = transaction_data['transaction_date'].dt.isocalendar().week
        
        # Monthly patterns
        monthly_revenue = transaction_data.groupby('month').agg({
            'amount': ['sum', 'mean', 'count']
        })
        monthly_revenue.columns = ['total_revenue', 'avg_job_value', 'job_count']
        monthly_revenue = monthly_revenue.reset_index()
        monthly_revenue['month_name'] = pd.to_datetime(monthly_revenue['month'], format='%m').dt.month_name()
        
        # Quarterly patterns
        quarterly_revenue = transaction_data.groupby('quarter').agg({
            'amount': ['sum', 'mean', 'count']
        })
        quarterly_revenue.columns = ['total_revenue', 'avg_job_value', 'job_count']
        quarterly_revenue = quarterly_revenue.reset_index()
        
        # Day of week patterns
        dow_revenue = transaction_data.groupby('day_of_week').agg({
            'amount': ['sum', 'mean', 'count']
        })
        dow_revenue.columns = ['total_revenue', 'avg_job_value', 'job_count']
        dow_revenue = dow_revenue.reset_index()
        
        # Service type seasonal patterns
        service_seasonal = transaction_data.groupby(['service_type', 'month'])['amount'].sum().unstack(fill_value=0)
        
        # Calculate seasonality index (compared to annual average)
        annual_avg = transaction_data.groupby('month')['amount'].sum().mean()
        monthly_revenue['seasonality_index'] = (monthly_revenue['total_revenue'] / annual_avg).round(2)
        
        # Identify peak and off-peak periods
        peak_months = monthly_revenue.nlargest(3, 'total_revenue')['month_name'].tolist()
        slow_months = monthly_revenue.nsmallest(3, 'total_revenue')['month_name'].tolist()
        
        # Revenue growth trends
        transaction_data['year_month'] = transaction_data['transaction_date'].dt.to_period('M')
        monthly_trends = transaction_data.groupby('year_month')['amount'].sum().reset_index()
        monthly_trends['growth_rate'] = monthly_trends['amount'].pct_change() * 100
        
        # Weather correlation analysis (simplified)
        weather_impact_months = {
            'Winter Storm Season': [12, 1, 2],
            'Spring Maintenance': [3, 4, 5],
            'Summer Peak': [6, 7, 8],
            'Fall Preparation': [9, 10, 11]
        }
        
        seasonal_insights = {
            'monthly_patterns': monthly_revenue.to_dict('records'),
            'quarterly_patterns': quarterly_revenue.to_dict('records'),
            'day_of_week_patterns': dow_revenue.to_dict('records'),
            'peak_months': peak_months,
            'slow_months': slow_months,
            'service_seasonal_matrix': service_seasonal.to_dict(),
            'revenue_growth_trends': monthly_trends.tail(12).to_dict('records'),
            'seasonal_recommendations': self._generate_seasonal_recommendations(monthly_revenue, peak_months, slow_months),
            'weather_impact_periods': weather_impact_months
        }
        
        # Cache results
        self._cache_results('seasonal_patterns', seasonal_insights)
        
        return seasonal_insights
    
    def optimize_pricing(self, transaction_data: pd.DataFrame, market_data: pd.DataFrame = None) -> Dict:
        """
        Generate pricing optimization suggestions.
        
        Args:
            transaction_data: Historical transaction data
            market_data: Optional market pricing data
            
        Returns:
            Dictionary with pricing recommendations
        """
        logger.info("Generating pricing optimization suggestions")
        
        # Current pricing analysis
        current_pricing = transaction_data.groupby('service_type').agg({
            'amount': ['mean', 'median', 'std', 'min', 'max', 'count']
        })
        current_pricing.columns = ['avg_price', 'median_price', 'price_std', 'min_price', 'max_price', 'job_count']
        current_pricing = current_pricing.reset_index()
        
        # Price elasticity analysis
        price_elasticity = self._analyze_price_elasticity(transaction_data)
        
        # Competitive positioning (if market data available)
        if market_data is not None and not market_data.empty:
            competitive_analysis = self._analyze_competitive_position(current_pricing, market_data)
        else:
            competitive_analysis = self._estimate_market_position(current_pricing)
        
        # Dynamic pricing recommendations
        pricing_recommendations = []
        
        for _, service in current_pricing.iterrows():
            service_type = service['service_type']
            current_avg = service['avg_price']
            
            # Base recommendations on job volume and price variance
            if service['job_count'] > current_pricing['job_count'].median():
                # High volume service
                if service['price_std'] / service['avg_price'] > 0.3:  # High variance
                    recommendation = {
                        'service_type': service_type,
                        'current_avg_price': current_avg,
                        'recommendation': 'Standardize pricing tiers',
                        'suggested_action': 'Create 3 pricing tiers: Basic, Standard, Premium',
                        'potential_impact': '+15% revenue'
                    }
                else:
                    recommendation = {
                        'service_type': service_type,
                        'current_avg_price': current_avg,
                        'recommendation': 'Gradual price increase',
                        'suggested_action': f'Increase by ${round(current_avg * 0.1)}',
                        'potential_impact': '+8% revenue'
                    }
            else:
                # Low volume service
                recommendation = {
                    'service_type': service_type,
                    'current_avg_price': current_avg,
                    'recommendation': 'Premium positioning',
                    'suggested_action': f'Increase by ${round(current_avg * 0.2)}',
                    'potential_impact': '+25% per job revenue'
                }
            
            pricing_recommendations.append(recommendation)
        
        # Value-based pricing opportunities
        value_opportunities = self._identify_value_pricing_opportunities(transaction_data)
        
        pricing_insights = {
            'current_pricing_summary': current_pricing.to_dict('records'),
            'pricing_recommendations': pricing_recommendations,
            'price_elasticity_insights': price_elasticity,
            'competitive_positioning': competitive_analysis,
            'value_pricing_opportunities': value_opportunities,
            'dynamic_pricing_strategy': self._generate_dynamic_pricing_strategy(transaction_data)
        }
        
        # Cache results
        self._cache_results('pricing_optimization', pricing_insights)
        
        return pricing_insights
    
    def analyze_payment_patterns(self, payment_data: pd.DataFrame) -> Dict:
        """
        Analyze payment delay patterns and cash flow impact.
        
        Args:
            payment_data: DataFrame with payment data [invoice_date, payment_date, amount, customer_id, payment_method]
            
        Returns:
            Dictionary with payment analysis
        """
        logger.info("Analyzing payment patterns")
        
        # Calculate payment delays
        payment_data['invoice_date'] = pd.to_datetime(payment_data['invoice_date'])
        payment_data['payment_date'] = pd.to_datetime(payment_data['payment_date'])
        payment_data['days_to_payment'] = (payment_data['payment_date'] - payment_data['invoice_date']).dt.days
        
        # Overall payment metrics
        avg_payment_delay = payment_data['days_to_payment'].mean()
        median_payment_delay = payment_data['days_to_payment'].median()
        
        # Payment delay distribution
        payment_buckets = pd.cut(
            payment_data['days_to_payment'],
            bins=[-1, 0, 7, 14, 30, 60, float('inf')],
            labels=['Same Day', '1-7 days', '8-14 days', '15-30 days', '31-60 days', '60+ days']
        )
        
        delay_distribution = payment_buckets.value_counts().reset_index()
        delay_distribution.columns = ['payment_period', 'count']
        delay_distribution['percentage'] = (delay_distribution['count'] / len(payment_data) * 100).round(2)
        
        # Payment method analysis
        payment_method_stats = payment_data.groupby('payment_method').agg({
            'days_to_payment': 'mean',
            'amount': ['sum', 'count'],
        })
        payment_method_stats.columns = ['avg_days_to_payment', 'total_amount', 'transaction_count']
        payment_method_stats = payment_method_stats.reset_index()
        
        # Customer payment behavior
        customer_payment_behavior = payment_data.groupby('customer_id').agg({
            'days_to_payment': ['mean', 'std'],
            'amount': 'sum'
        })
        customer_payment_behavior.columns = ['avg_payment_delay', 'payment_consistency', 'total_amount']
        customer_payment_behavior = customer_payment_behavior.reset_index()
        
        # Identify payment risk customers
        risk_threshold = payment_data['days_to_payment'].quantile(0.8)
        risk_customers = customer_payment_behavior[
            customer_payment_behavior['avg_payment_delay'] > risk_threshold
        ].sort_values('total_amount', ascending=False)
        
        # Cash flow impact analysis
        outstanding_amount = payment_data[payment_data['days_to_payment'] > 30]['amount'].sum()
        
        # Seasonal payment patterns
        payment_data['payment_month'] = payment_data['payment_date'].dt.month
        monthly_payment_patterns = payment_data.groupby('payment_month')['days_to_payment'].mean().reset_index()
        
        payment_insights = {
            'overall_metrics': {
                'average_payment_delay_days': round(avg_payment_delay, 1),
                'median_payment_delay_days': round(median_payment_delay, 1),
                'total_transactions': len(payment_data),
                'outstanding_amount_30plus_days': round(outstanding_amount, 2)
            },
            'payment_delay_distribution': delay_distribution.to_dict('records'),
            'payment_method_performance': payment_method_stats.to_dict('records'),
            'payment_risk_customers': risk_customers.head(10).to_dict('records'),
            'monthly_payment_patterns': monthly_payment_patterns.to_dict('records'),
            'cash_flow_recommendations': self._generate_cash_flow_recommendations(delay_distribution, payment_method_stats)
        }
        
        # Cache results
        self._cache_results('payment_patterns', payment_insights)
        
        return payment_insights
    
    def _generate_conversion_tips(self, service_conversion: pd.DataFrame, amount_conversion: pd.DataFrame) -> List[str]:
        """Generate actionable tips to improve conversion rates."""
        tips = []
        
        # Service-specific tips
        low_conversion_services = service_conversion[service_conversion['conversion_rate'] < 50]
        for _, service in low_conversion_services.iterrows():
            tips.append(f"Improve {service['service_type']} conversion with better value demonstration")
        
        # Price-specific tips
        low_conversion_amounts = amount_conversion[amount_conversion['conversion_rate'] < 40]
        for _, amount_range in low_conversion_amounts.iterrows():
            tips.append(f"For {amount_range['quote_range']} quotes, consider offering payment plans")
        
        return tips[:5]  # Return top 5 tips
    
    def _estimate_service_costs(self, revenue_data: pd.DataFrame) -> pd.DataFrame:
        """Estimate service costs based on industry standards."""
        cost_estimates = {
            'Plumbing': 0.55,  # 55% of revenue as cost
            'Electrical': 0.50,
            'HVAC': 0.60,
            'General Handyman': 0.45,
            'Painting': 0.65,
            'Flooring': 0.70
        }
        
        cost_data = []
        for _, row in revenue_data.iterrows():
            service_type = row['service_type']
            cost_ratio = cost_estimates.get(service_type, 0.55)
            
            for _ in range(int(row['job_count'])):
                cost_data.append({
                    'service_type': service_type,
                    'cost_amount': row['avg_revenue_per_job'] * cost_ratio
                })
        
        return pd.DataFrame(cost_data)
    
    def _generate_seasonal_recommendations(self, monthly_data: pd.DataFrame, peak_months: List, slow_months: List) -> List[str]:
        """Generate seasonal business recommendations."""
        recommendations = []
        
        recommendations.append(f"Focus marketing efforts in {', '.join(slow_months)} to boost off-season revenue")
        recommendations.append(f"Staff up during {', '.join(peak_months)} to maximize {peak_months[0]} opportunities")
        recommendations.append("Consider seasonal service packages (winterization, spring maintenance)")
        recommendations.append("Implement weather-triggered marketing campaigns")
        
        return recommendations
    
    def _analyze_price_elasticity(self, transaction_data: pd.DataFrame) -> Dict:
        """Analyze price elasticity for services."""
        # Simplified elasticity analysis
        elasticity_insights = {}
        
        for service_type in transaction_data['service_type'].unique():
            service_data = transaction_data[transaction_data['service_type'] == service_type]
            
            if len(service_data) > 10:
                # Calculate correlation between price and volume
                monthly_data = service_data.groupby(service_data['transaction_date'].dt.to_period('M')).agg({
                    'amount': ['mean', 'count']
                })
                
                if len(monthly_data) > 3:
                    price_volume_corr = monthly_data[('amount', 'mean')].corr(monthly_data[('amount', 'count')])
                    elasticity_insights[service_type] = {
                        'price_sensitivity': 'High' if price_volume_corr < -0.5 else 'Medium' if price_volume_corr < -0.2 else 'Low',
                        'correlation': round(price_volume_corr, 3) if not pd.isna(price_volume_corr) else 0
                    }
        
        return elasticity_insights
    
    def _analyze_competitive_position(self, current_pricing: pd.DataFrame, market_data: pd.DataFrame) -> Dict:
        """Analyze competitive positioning."""
        # Merge current pricing with market data
        competitive_df = current_pricing.merge(market_data, on='service_type', how='left')
        
        competitive_analysis = []
        for _, row in competitive_df.iterrows():
            if not pd.isna(row.get('market_avg_price')):
                position = 'Below Market' if row['avg_price'] < row['market_avg_price'] * 0.9 else \
                          'Above Market' if row['avg_price'] > row['market_avg_price'] * 1.1 else \
                          'Market Rate'
                
                competitive_analysis.append({
                    'service_type': row['service_type'],
                    'our_price': row['avg_price'],
                    'market_price': row['market_avg_price'],
                    'position': position,
                    'opportunity': 'Increase prices' if position == 'Below Market' else 'Consider value adds' if position == 'Above Market' else 'Monitor competition'
                })
        
        return competitive_analysis
    
    def _estimate_market_position(self, current_pricing: pd.DataFrame) -> Dict:
        """Estimate market position without market data."""
        return {
            'note': 'Market data not available',
            'recommendation': 'Conduct competitive analysis to optimize pricing strategy'
        }
    
    def _identify_value_pricing_opportunities(self, transaction_data: pd.DataFrame) -> List[Dict]:
        """Identify opportunities for value-based pricing."""
        opportunities = []
        
        # Services with high customer satisfaction or emergency nature
        premium_services = ['Emergency Plumbing', 'Electrical Repair', 'HVAC Emergency']
        
        for service in transaction_data['service_type'].unique():
            if any(premium in service for premium in premium_services):
                opportunities.append({
                    'service_type': service,
                    'opportunity': 'Emergency premium pricing',
                    'suggested_markup': '25-50%',
                    'rationale': 'High urgency and customer value'
                })
        
        return opportunities
    
    def _generate_dynamic_pricing_strategy(self, transaction_data: pd.DataFrame) -> Dict:
        """Generate dynamic pricing strategy recommendations."""
        return {
            'time_based_pricing': {
                'weekends': '+15% premium for weekend service',
                'evenings': '+20% premium for after-hours service',
                'holidays': '+25% premium for holiday service'
            },
            'demand_based_pricing': {
                'peak_season': '+10% during high-demand months',
                'emergency_calls': '+30% for same-day emergency service'
            },
            'customer_based_pricing': {
                'new_customers': '10% discount for first-time customers',
                'repeat_customers': '5% loyalty discount after 5th service',
                'referrals': '15% discount for successful referrals'
            }
        }
    
    def _generate_cash_flow_recommendations(self, delay_distribution: pd.DataFrame, payment_methods: pd.DataFrame) -> List[str]:
        """Generate cash flow improvement recommendations."""
        recommendations = []
        
        # Analyze payment delays
        slow_payments = delay_distribution[delay_distribution['payment_period'].isin(['31-60 days', '60+ days'])]
        if not slow_payments.empty and slow_payments['percentage'].sum() > 20:
            recommendations.append("Implement stricter payment terms and follow-up procedures")
        
        # Payment method recommendations
        if not payment_methods.empty:
            fastest_method = payment_methods.loc[payment_methods['avg_days_to_payment'].idxmin(), 'payment_method']
            recommendations.append(f"Encourage {fastest_method} payments with small discount")
        
        recommendations.extend([
            "Offer early payment discounts (2% if paid within 10 days)",
            "Implement automated payment reminders",
            "Consider requiring deposits for large jobs"
        ])
        
        return recommendations
    
    def _cache_results(self, key: str, data: any, ttl: int = 3600):
        """Cache results in Redis."""
        try:
            self.redis_client.setex(
                f"revenue_intelligence:{key}",
                ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Failed to cache results for {key}: {e}")
    
    def get_cached_results(self, key: str) -> Optional[any]:
        """Retrieve cached results from Redis."""
        try:
            cached_data = self.redis_client.get(f"revenue_intelligence:{key}")
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached results for {key}: {e}")
        return None