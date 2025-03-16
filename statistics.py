"""
Statistics Manager for Mortgage Calculator

This module provides functionality for tracking usage data and generating
statistics for the admin dashboard.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

logger = logging.getLogger(__name__)

class StatisticsManager:
    """Manages usage statistics for the mortgage calculator."""
    
    def __init__(self, stats_file='data/statistics.json'):
        """Initialize the statistics manager."""
        self.stats_file = stats_file
        self.stats_dir = os.path.dirname(stats_file)
        self._ensure_dir_exists()
        self.calculations = self._load_stats()
        
    def _ensure_dir_exists(self):
        """Ensure the statistics directory exists."""
        if not os.path.exists(self.stats_dir):
            try:
                os.makedirs(self.stats_dir)
                logger.info(f"Created statistics directory: {self.stats_dir}")
            except Exception as e:
                logger.error(f"Error creating statistics directory: {e}")
    
    def _load_stats(self):
        """Load statistics from the JSON file."""
        if not os.path.exists(self.stats_file):
            logger.info(f"Statistics file not found, creating new one: {self.stats_file}")
            return []
        
        try:
            with open(self.stats_file, 'r') as f:
                data = json.load(f)
                return data
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
            return []
    
    def _save_stats(self):
        """Save statistics to the JSON file."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.calculations, f, indent=2)
            logger.info(f"Saved statistics to {self.stats_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving statistics: {e}")
            return False
    
    def track_calculation(self, params, user_agent=None, ip_address=None):
        """
        Track a mortgage calculation.
        
        Args:
            params: Dictionary of calculation parameters
            user_agent: Optional user agent string
            ip_address: Optional IP address (will be anonymized)
        """
        # Create a record of the calculation
        timestamp = datetime.now().isoformat()
        
        # Only store essential parameters to reduce storage and protect privacy
        essential_params = {
            'loan_amount': params.get('loan_amount', params.get('purchase_price', 0) - params.get('down_payment', 0)),
            'purchase_price': params.get('purchase_price', 0),
            'down_payment': params.get('down_payment', 0),
            'annual_rate': params.get('annual_rate', 0),
            'loan_term': params.get('loan_term', 30),
            'loan_type': params.get('loan_type', 'conventional'),
            'credit_score': params.get('credit_score', 750)
        }
        
        # Anonymize IP if provided
        if ip_address:
            # Just keep first two octets and hash the rest
            parts = ip_address.split('.')
            if len(parts) == 4:
                ip_address = f"{parts[0]}.{parts[1]}.x.x"
        
        # Create the calculation record
        record = {
            'timestamp': timestamp,
            'params': essential_params,
            'user_agent_type': self._classify_user_agent(user_agent) if user_agent else 'unknown',
            'anonymized_ip': ip_address
        }
        
        # Add the record to our collection
        self.calculations.append(record)
        
        # Save stats after adding the new record
        return self._save_stats()
    
    def _classify_user_agent(self, user_agent):
        """Classify the user agent into device/browser categories."""
        if not user_agent:
            return 'unknown'
        
        user_agent = user_agent.lower()
        
        # Mobile detection
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent or 'ipad' in user_agent:
            if 'iphone' in user_agent or 'ipad' in user_agent:
                return 'ios'
            elif 'android' in user_agent:
                return 'android'
            return 'mobile'
        
        # Desktop browsers
        if 'chrome' in user_agent:
            return 'chrome'
        elif 'firefox' in user_agent:
            return 'firefox'
        elif 'safari' in user_agent:
            return 'safari'
        elif 'edge' in user_agent:
            return 'edge'
        
        return 'other'
    
    def get_summary_stats(self):
        """Get summary statistics for the admin dashboard."""
        if not self.calculations:
            return {
                'total_calculations': 0,
                'avg_loan_amount': 0,
                'loan_terms': {},
                'loan_types': {},
                'credit_score_ranges': {},
                'device_types': {},
                'calculations_by_date': {},
                'avg_interest_rate': 0
            }
        
        # Initialize summary data
        data = {
            'total_calculations': len(self.calculations),
            'loan_terms': defaultdict(int),
            'loan_types': defaultdict(int),
            'credit_score_ranges': defaultdict(int),
            'device_types': defaultdict(int),
            'calculations_by_date': defaultdict(int)
        }
        
        # Track totals for averages
        total_loan_amount = 0
        total_interest_rate = 0
        
        # Process each calculation
        for calc in self.calculations:
            params = calc.get('params', {})
            
            # Aggregate loan amount for average
            loan_amount = params.get('loan_amount', 0)
            total_loan_amount += loan_amount
            
            # Aggregate interest rate for average
            interest_rate = params.get('annual_rate', 0)
            total_interest_rate += interest_rate
            
            # Count loan terms
            loan_term = params.get('loan_term', 30)
            data['loan_terms'][str(loan_term)] += 1
            
            # Count loan types
            loan_type = params.get('loan_type', 'conventional')
            data['loan_types'][loan_type] += 1
            
            # Group credit scores into ranges
            credit_score = params.get('credit_score', 0)
            if credit_score < 580:
                score_range = 'Poor (< 580)'
            elif credit_score < 670:
                score_range = 'Fair (580-669)'
            elif credit_score < 740:
                score_range = 'Good (670-739)'
            elif credit_score < 800:
                score_range = 'Very Good (740-799)'
            else:
                score_range = 'Excellent (800+)'
            data['credit_score_ranges'][score_range] += 1
            
            # Track device types
            device_type = calc.get('user_agent_type', 'unknown')
            data['device_types'][device_type] += 1
            
            # Track calculations by date (just the date part of the timestamp)
            try:
                date_str = calc.get('timestamp', '').split('T')[0]
                data['calculations_by_date'][date_str] += 1
            except (IndexError, AttributeError):
                pass
        
        # Calculate averages
        data['avg_loan_amount'] = total_loan_amount / data['total_calculations'] if data['total_calculations'] > 0 else 0
        data['avg_interest_rate'] = total_interest_rate / data['total_calculations'] if data['total_calculations'] > 0 else 0
        
        # Sort and limit calculations by date to last 30 days
        last_30_days = {}
        today = datetime.now().date()
        for i in range(30):
            date = today - timedelta(days=i)
            date_str = date.isoformat()
            last_30_days[date_str] = data['calculations_by_date'].get(date_str, 0)
        
        # Sort by date (oldest to newest)
        data['calculations_by_date'] = dict(sorted(last_30_days.items()))
        
        return data
    
    def get_chart_data(self):
        """Generate chart data for the admin dashboard."""
        summary = self.get_summary_stats()
        
        charts = {}
        
        # Generate charts data
        charts['calculations_by_date'] = {
            'labels': list(summary['calculations_by_date'].keys()),
            'data': list(summary['calculations_by_date'].values())
        }
        
        charts['loan_types'] = {
            'labels': list(summary['loan_types'].keys()),
            'data': list(summary['loan_types'].values())
        }
        
        charts['loan_terms'] = {
            'labels': list(summary['loan_terms'].keys()),
            'data': list(summary['loan_terms'].values())
        }
        
        charts['credit_score_ranges'] = {
            'labels': list(summary['credit_score_ranges'].keys()),
            'data': list(summary['credit_score_ranges'].values())
        }
        
        charts['device_types'] = {
            'labels': list(summary['device_types'].keys()),
            'data': list(summary['device_types'].values())
        }
        
        return charts
    
    def generate_csv_report(self):
        """Generate a CSV report of all calculations."""
        if not self.calculations:
            return None
        
        # Flatten the data for a CSV report
        flattened_data = []
        for calc in self.calculations:
            record = {
                'timestamp': calc.get('timestamp', ''),
                'device_type': calc.get('user_agent_type', 'unknown'),
            }
            
            # Add the parameters
            params = calc.get('params', {})
            for key, value in params.items():
                record[key] = value
            
            flattened_data.append(record)
        
        # Convert to DataFrame
        df = pd.DataFrame(flattened_data)
        
        # Create a CSV string
        csv_data = df.to_csv(index=False)
        return csv_data
    
    def generate_insights(self):
        """Generate insights from the statistics data."""
        summary = self.get_summary_stats()
        
        insights = []
        
        # Check if we have enough data
        if summary['total_calculations'] < 10:
            insights.append({
                'title': 'Insufficient Data',
                'description': 'Not enough calculations to generate meaningful insights.',
                'type': 'info'
            })
            return insights
        
        # Most popular loan term
        if summary['loan_terms']:
            most_common_term = max(summary['loan_terms'].items(), key=lambda x: x[1])
            term_percentage = (most_common_term[1] / summary['total_calculations']) * 100
            insights.append({
                'title': 'Popular Loan Term',
                'description': f"{most_common_term[0]}-year mortgages are the most popular choice ({term_percentage:.1f}% of calculations).",
                'type': 'info'
            })
        
        # Most popular loan type
        if summary['loan_types']:
            most_common_type = max(summary['loan_types'].items(), key=lambda x: x[1])
            type_percentage = (most_common_type[1] / summary['total_calculations']) * 100
            insights.append({
                'title': 'Popular Loan Type',
                'description': f"{most_common_type[0].title()} loans are the most frequently calculated ({type_percentage:.1f}% of calculations).",
                'type': 'info'
            })
        
        # Average interest rate context
        current_avg_rate = summary['avg_interest_rate']
        if current_avg_rate > 0:
            if current_avg_rate > 6.5:
                insights.append({
                    'title': 'High Interest Rates',
                    'description': f"The average interest rate of {current_avg_rate:.2f}% is historically high.",
                    'type': 'warning'
                })
            elif current_avg_rate < 4.0:
                insights.append({
                    'title': 'Low Interest Rates',
                    'description': f"The average interest rate of {current_avg_rate:.2f}% is historically low.",
                    'type': 'success'
                })
        
        # Device usage patterns
        if summary['device_types']:
            mobile_types = ['mobile', 'ios', 'android']
            mobile_count = sum(summary['device_types'].get(t, 0) for t in mobile_types)
            mobile_percentage = (mobile_count / summary['total_calculations']) * 100
            
            if mobile_percentage > 50:
                insights.append({
                    'title': 'Mobile Usage',
                    'description': f"Most users ({mobile_percentage:.1f}%) access the calculator from mobile devices.",
                    'type': 'info'
                })
        
        return insights
    
    def purge_old_data(self, days=365):
        """Purge data older than the specified number of days."""
        if not self.calculations:
            return 0
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        original_count = len(self.calculations)
        
        self.calculations = [calc for calc in self.calculations 
                            if calc.get('timestamp', '') >= cutoff_date]
        
        # Save if any records were removed
        if len(self.calculations) < original_count:
            self._save_stats()
            return original_count - len(self.calculations)
        
        return 0
