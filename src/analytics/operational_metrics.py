"""
Operational Metrics Module
Tracks efficiency and performance metrics
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path

class OperationalMetrics:
    def __init__(self):
        self.metrics_file = Path("data/operational_metrics.json")
        self.metrics_file.parent.mkdir(exist_ok=True)
        
    def calculate_response_times(self, interactions_df: pd.DataFrame) -> Dict:
        """Calculate average response times by channel"""
        response_times = {
            'email': self._calculate_email_response_time(interactions_df),
            'sms': self._calculate_sms_response_time(interactions_df),
            'phone': self._calculate_phone_response_time(interactions_df)
        }
        return response_times
    
    def _calculate_email_response_time(self, df: pd.DataFrame) -> float:
        """Calculate average email response time in minutes"""
        email_df = df[df['channel'] == 'email']
        if email_df.empty:
            return 0.0
        
        email_df['response_time'] = (
            pd.to_datetime(email_df['response_timestamp']) - 
            pd.to_datetime(email_df['received_timestamp'])
        ).dt.total_seconds() / 60
        
        return email_df['response_time'].mean()
    
    def _calculate_sms_response_time(self, df: pd.DataFrame) -> float:
        """Calculate average SMS response time in minutes"""
        sms_df = df[df['channel'] == 'sms']
        if sms_df.empty:
            return 0.0
        
        sms_df['response_time'] = (
            pd.to_datetime(sms_df['response_timestamp']) - 
            pd.to_datetime(sms_df['received_timestamp'])
        ).dt.total_seconds() / 60
        
        return sms_df['response_time'].mean()
    
    def _calculate_phone_response_time(self, df: pd.DataFrame) -> float:
        """Calculate average phone response time in minutes"""
        phone_df = df[df['channel'] == 'phone']
        if phone_df.empty:
            return 0.0
        
        phone_df['response_time'] = (
            pd.to_datetime(phone_df['call_answered_timestamp']) - 
            pd.to_datetime(phone_df['call_received_timestamp'])
        ).dt.total_seconds() / 60
        
        return phone_df['response_time'].mean()
    
    def analyze_appointment_efficiency(self, calendar_df: pd.DataFrame) -> Dict:
        """Analyze appointment scheduling efficiency"""
        return {
            'avg_booking_time': self._avg_time_to_book(calendar_df),
            'utilization_rate': self._calculate_utilization(calendar_df),
            'travel_efficiency': self._calculate_travel_efficiency(calendar_df),
            'no_show_rate': self._calculate_no_show_rate(calendar_df)
        }
    
    def _avg_time_to_book(self, df: pd.DataFrame) -> float:
        """Calculate average time from initial contact to confirmed booking"""
        if df.empty:
            return 0.0
        
        df['booking_time'] = (
            pd.to_datetime(df['confirmed_timestamp']) - 
            pd.to_datetime(df['initial_contact_timestamp'])
        ).dt.total_seconds() / 3600  # Convert to hours
        
        return df['booking_time'].mean()
    
    def _calculate_utilization(self, df: pd.DataFrame) -> float:
        """Calculate crew utilization rate"""
        if df.empty:
            return 0.0
        
        total_available_hours = df['available_hours'].sum()
        total_booked_hours = df['booked_hours'].sum()
        
        return (total_booked_hours / total_available_hours) * 100 if total_available_hours > 0 else 0.0
    
    def _calculate_travel_efficiency(self, df: pd.DataFrame) -> float:
        """Calculate travel efficiency (job time vs travel time ratio)"""
        if df.empty or 'travel_time' not in df.columns or 'job_duration' not in df.columns:
            return 0.0
        
        total_job_time = df['job_duration'].sum()
        total_travel_time = df['travel_time'].sum()
        
        return (total_job_time / (total_job_time + total_travel_time)) * 100 if (total_job_time + total_travel_time) > 0 else 0.0
    
    def _calculate_no_show_rate(self, df: pd.DataFrame) -> float:
        """Calculate no-show rate for appointments"""
        if df.empty:
            return 0.0
        
        total_appointments = len(df)
        no_shows = len(df[df['status'] == 'no_show'])
        
        return (no_shows / total_appointments) * 100 if total_appointments > 0 else 0.0
    
    def analyze_crew_utilization(self, crew_df: pd.DataFrame) -> Dict:
        """Analyze individual crew member utilization"""
        if crew_df.empty:
            return {}
        
        utilization_by_crew = {}
        for crew_id in crew_df['crew_id'].unique():
            crew_data = crew_df[crew_df['crew_id'] == crew_id]
            utilization_by_crew[crew_id] = {
                'utilization_rate': self._calculate_utilization(crew_data),
                'avg_jobs_per_day': crew_data.groupby('date')['job_id'].count().mean(),
                'avg_revenue_per_day': crew_data.groupby('date')['revenue'].sum().mean()
            }
        
        return utilization_by_crew
    
    def calculate_customer_satisfaction_metrics(self, feedback_df: pd.DataFrame) -> Dict:
        """Calculate customer satisfaction metrics"""
        if feedback_df.empty:
            return {
                'avg_rating': 0.0,
                'response_rate': 0.0,
                'nps_score': 0.0
            }
        
        return {
            'avg_rating': feedback_df['rating'].mean(),
            'response_rate': (len(feedback_df) / feedback_df['total_customers'].iloc[0]) * 100,
            'nps_score': self._calculate_nps(feedback_df)
        }
    
    def _calculate_nps(self, df: pd.DataFrame) -> float:
        """Calculate Net Promoter Score"""
        if 'nps_rating' not in df.columns:
            return 0.0
        
        promoters = len(df[df['nps_rating'] >= 9])
        detractors = len(df[df['nps_rating'] <= 6])
        total_responses = len(df)
        
        return ((promoters - detractors) / total_responses) * 100 if total_responses > 0 else 0.0
    
    def generate_efficiency_report(self, 
                                 interactions_df: Optional[pd.DataFrame] = None,
                                 calendar_df: Optional[pd.DataFrame] = None,
                                 crew_df: Optional[pd.DataFrame] = None,
                                 feedback_df: Optional[pd.DataFrame] = None) -> Dict:
        """Generate comprehensive efficiency report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'response_times': {},
            'appointment_efficiency': {},
            'crew_utilization': {},
            'customer_satisfaction': {}
        }
        
        # Calculate response times if interaction data available
        if interactions_df is not None and not interactions_df.empty:
            report['response_times'] = self.calculate_response_times(interactions_df)
        
        # Calculate appointment efficiency if calendar data available
        if calendar_df is not None and not calendar_df.empty:
            report['appointment_efficiency'] = self.analyze_appointment_efficiency(calendar_df)
        
        # Calculate crew utilization if crew data available
        if crew_df is not None and not crew_df.empty:
            report['crew_utilization'] = self.analyze_crew_utilization(crew_df)
        
        # Calculate customer satisfaction if feedback data available
        if feedback_df is not None and not feedback_df.empty:
            report['customer_satisfaction'] = self.calculate_customer_satisfaction_metrics(feedback_df)
        
        # Save report to file
        self._save_report(report)
        
        return report
    
    def _save_report(self, report: Dict):
        """Save efficiency report to JSON file"""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving metrics report: {e}")
    
    def load_latest_report(self) -> Optional[Dict]:
        """Load the latest efficiency report"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Error loading metrics report: {e}")
            return None
    
    def get_trend_analysis(self, days_back: int = 30) -> Dict:
        """Analyze trends over specified time period"""
        # This would typically connect to a database to get historical data
        # For now, return a placeholder structure
        return {
            'period': f"Last {days_back} days",
            'trends': {
                'response_time_trend': 'improving',
                'utilization_trend': 'stable',
                'satisfaction_trend': 'improving'
            },
            'recommendations': [
                "Continue current response time optimization",
                "Consider adding crew during peak hours",
                "Implement customer feedback loop improvements"
            ]
        }