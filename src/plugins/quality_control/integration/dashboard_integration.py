"""
Dashboard Integration for Quality Control Plugin

Provides real-time quality metrics display and integration with the SIDHE dashboard system.
Updates quality status, trends, and reports for monitoring and visualization.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict

logger = logging.getLogger(__name__)

class DashboardIntegration:
    """
    Quality Control Dashboard Integration
    
    Manages real-time quality status updates, trend tracking,
    and integration with the SIDHE monitoring dashboard.
    """
    
    def __init__(self):
        """Initialize dashboard integration"""
        self.quality_history = []
        self.current_status = None
        logger.info("Dashboard integration initialized")
    
    async def update_quality_status(self, quality_report) -> Dict[str, Any]:
        """
        Update dashboard with latest quality status
        
        Args:
            quality_report: QualityReport from quality control analysis
            
        Returns:
            Dashboard update confirmation
        """
        logger.info("Updating dashboard with quality status")
        
        try:
            # Convert report to dashboard format
            dashboard_data = self._format_for_dashboard(quality_report)
            
            # Store current status
            self.current_status = dashboard_data
            
            # Add to history for trend analysis
            self.quality_history.append({
                'timestamp': quality_report.timestamp,
                'overall_score': quality_report.overall_score,
                'component_scores': self._extract_component_scores(quality_report),
                'issue_count': len(quality_report.issues)
            })
            
            # Keep only last 100 entries for performance
            if len(self.quality_history) > 100:
                self.quality_history = self.quality_history[-100:]
            
            # Send update to dashboard (would integrate with actual dashboard system)
            await self._send_dashboard_update(dashboard_data)
            
            logger.info("Dashboard update completed successfully")
            return {
                'status': 'success',
                'updated_at': datetime.now().isoformat(),
                'data_points': len(self.quality_history)
            }
            
        except Exception as e:
            logger.error(f"Dashboard update failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def get_quality_dashboard_data(self) -> Dict[str, Any]:
        """
        Get current quality dashboard data
        
        Returns:
            Complete dashboard data for quality metrics
        """
        if not self.current_status:
            return {
                'status': 'no_data',
                'message': 'No quality data available'
            }
        
        # Calculate trends
        trends = self._calculate_quality_trends()
        
        # Get recent issues
        recent_issues = self._get_recent_issues()
        
        # Compile dashboard data
        dashboard_data = {
            'current_status': self.current_status,
            'trends': trends,
            'recent_issues': recent_issues,
            'history_length': len(self.quality_history),
            'last_updated': self.current_status.get('timestamp'),
            'components': self._get_component_status()
        }
        
        return dashboard_data
    
    async def get_quality_trends(self, timeframe: str = '24h') -> Dict[str, Any]:
        """
        Get quality trends for specified timeframe
        
        Args:
            timeframe: Time period ('1h', '24h', '7d', '30d')
            
        Returns:
            Quality trend analysis
        """
        logger.info(f"Calculating quality trends for {timeframe}")
        
        # Filter history based on timeframe
        filtered_history = self._filter_history_by_timeframe(timeframe)
        
        if len(filtered_history) < 2:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least 2 data points for trend analysis'
            }
        
        # Calculate trend metrics
        trends = {
            'overall_score': self._calculate_score_trend(filtered_history),
            'component_trends': self._calculate_component_trends(filtered_history),
            'issue_trends': self._calculate_issue_trends(filtered_history),
            'velocity': self._calculate_quality_velocity(filtered_history)
        }
        
        return {
            'status': 'success',
            'timeframe': timeframe,
            'data_points': len(filtered_history),
            'trends': trends
        }
    
    async def generate_quality_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive quality summary for dashboard
        
        Returns:
            Quality summary with key metrics and insights
        """
        if not self.current_status:
            return {'status': 'no_data'}
        
        current_score = self.current_status.get('overall_score', 0)
        
        # Determine quality level
        if current_score >= 90:
            quality_level = 'excellent'
            quality_color = 'green'
        elif current_score >= 80:
            quality_level = 'good'
            quality_color = 'blue'
        elif current_score >= 70:
            quality_level = 'acceptable'
            quality_color = 'yellow'
        elif current_score >= 60:
            quality_level = 'poor'
            quality_color = 'orange'
        else:
            quality_level = 'critical'
            quality_color = 'red'
        
        # Get component breakdown
        components = self.current_status.get('components', {})
        
        # Calculate statistics
        total_issues = len(self.current_status.get('issues', []))
        high_priority_issues = len([
            issue for issue in self.current_status.get('issues', [])
            if issue.get('severity') in ['high', 'critical']
        ])
        
        summary = {
            'overall_score': current_score,
            'quality_level': quality_level,
            'quality_color': quality_color,
            'total_issues': total_issues,
            'high_priority_issues': high_priority_issues,
            'components': components,
            'last_updated': self.current_status.get('timestamp'),
            'recommendations': self.current_status.get('recommendations', [])[:3],  # Top 3
            'gate_status': self.current_status.get('gate_status', {})
        }
        
        return summary
    
    def _format_for_dashboard(self, quality_report) -> Dict[str, Any]:
        """Format quality report for dashboard display"""
        return {
            'timestamp': quality_report.timestamp,
            'overall_score': quality_report.overall_score,
            'components': {
                'linting': self._extract_linting_summary(quality_report.linting_results),
                'coverage': self._extract_coverage_summary(quality_report.coverage_results),
                'quality': self._extract_quality_summary(quality_report.quality_metrics)
            },
            'issues': quality_report.issues[:10],  # Top 10 issues for dashboard
            'recommendations': quality_report.recommendations,
            'gate_status': quality_report.gate_status,
            'metrics': {
                'total_files_checked': self._count_files_checked(quality_report),
                'total_issues': len(quality_report.issues),
                'critical_issues': len([i for i in quality_report.issues if i.get('severity') == 'critical']),
                'warnings': len([i for i in quality_report.issues if i.get('severity') == 'warning'])
            }
        }
    
    def _extract_component_scores(self, quality_report) -> Dict[str, float]:
        """Extract component-level scores from quality report"""
        scores = {}
        
        # Linting scores
        linting_results = quality_report.linting_results
        if linting_results:
            for lang, results in linting_results.items():
                if isinstance(results, dict):
                    errors = results.get('errors', 0)
                    warnings = results.get('warnings', 0)
                    score = max(0, 100 - (errors * 10 + warnings * 5))
                    scores[f'linting_{lang}'] = score
        
        # Coverage score
        coverage_results = quality_report.coverage_results
        if coverage_results and 'overall_coverage' in coverage_results:
            scores['coverage'] = coverage_results['overall_coverage']
        
        # Quality metrics score
        quality_metrics = quality_report.quality_metrics
        if quality_metrics and 'quality_score' in quality_metrics:
            scores['quality'] = quality_metrics['quality_score']
        
        return scores
    
    def _extract_linting_summary(self, linting_results: Dict) -> Dict[str, Any]:
        """Extract linting summary for dashboard"""
        if not linting_results:
            return {'status': 'no_data'}
        
        total_errors = 0
        total_warnings = 0
        languages = []
        
        for lang, results in linting_results.items():
            if isinstance(results, dict):
                languages.append(lang)
                total_errors += results.get('errors', 0)
                total_warnings += results.get('warnings', 0)
        
        return {
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'languages': languages,
            'status': 'clean' if total_errors == 0 else 'issues'
        }
    
    def _extract_coverage_summary(self, coverage_results: Dict) -> Dict[str, Any]:
        """Extract coverage summary for dashboard"""
        if not coverage_results:
            return {'status': 'no_data'}
        
        overall_coverage = coverage_results.get('overall_coverage', 0)
        
        return {
            'overall_coverage': overall_coverage,
            'status': 'good' if overall_coverage >= 80 else 'needs_improvement',
            'missing_coverage_files': len(coverage_results.get('missing_coverage', []))
        }
    
    def _extract_quality_summary(self, quality_metrics: Dict) -> Dict[str, Any]:
        """Extract quality metrics summary for dashboard"""
        if not quality_metrics:
            return {'status': 'no_data'}
        
        overall_metrics = quality_metrics.get('overall_metrics', {})
        
        return {
            'average_complexity': overall_metrics.get('average_complexity', 0),
            'documentation_coverage': overall_metrics.get('documentation_coverage', 0),
            'total_files': overall_metrics.get('total_files', 0),
            'quality_score': quality_metrics.get('quality_score', 0)
        }
    
    def _count_files_checked(self, quality_report) -> int:
        """Count total files checked in quality report"""
        total = 0
        
        linting_results = quality_report.linting_results
        for lang_results in linting_results.values():
            if isinstance(lang_results, dict):
                total += lang_results.get('files_checked', 0)
        
        return total
    
    async def _send_dashboard_update(self, dashboard_data: Dict[str, Any]) -> None:
        """Send update to dashboard system"""
        # This would integrate with actual dashboard/monitoring system
        # For now, we'll log the update
        logger.info(f"Dashboard update: Score {dashboard_data.get('overall_score', 0):.1f}")
    
    def _calculate_quality_trends(self) -> Dict[str, Any]:
        """Calculate quality trends from history"""
        if len(self.quality_history) < 2:
            return {'status': 'insufficient_data'}
        
        recent = self.quality_history[-10:]  # Last 10 entries
        scores = [entry['overall_score'] for entry in recent]
        
        # Calculate trend direction
        if len(scores) >= 2:
            trend = 'improving' if scores[-1] > scores[0] else 'declining' if scores[-1] < scores[0] else 'stable'
            change = scores[-1] - scores[0]
        else:
            trend = 'stable'
            change = 0
        
        return {
            'direction': trend,
            'change': change,
            'current_score': scores[-1] if scores else 0,
            'previous_score': scores[-2] if len(scores) >= 2 else 0
        }
    
    def _get_recent_issues(self) -> List[Dict[str, Any]]:
        """Get recent quality issues"""
        if not self.current_status:
            return []
        
        issues = self.current_status.get('issues', [])
        
        # Sort by severity and return top 5
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.get('severity', 'low'), 3))
        
        return sorted_issues[:5]
    
    def _get_component_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for each component"""
        if not self.current_status:
            return {}
        
        components = self.current_status.get('components', {})
        status = {}
        
        for component, data in components.items():
            if isinstance(data, dict):
                # Determine status based on component data
                if 'total_errors' in data:
                    status[component] = {
                        'status': 'healthy' if data['total_errors'] == 0 else 'issues',
                        'details': data
                    }
                elif 'overall_coverage' in data:
                    status[component] = {
                        'status': 'healthy' if data['overall_coverage'] >= 80 else 'needs_improvement',
                        'details': data
                    }
                else:
                    status[component] = {
                        'status': 'unknown',
                        'details': data
                    }
        
        return status
    
    def _filter_history_by_timeframe(self, timeframe: str) -> List[Dict[str, Any]]:
        """Filter quality history by timeframe"""
        # Simplified filtering - in production would use proper datetime filtering
        if timeframe == '1h':
            return self.quality_history[-10:]
        elif timeframe == '24h':
            return self.quality_history[-50:]
        elif timeframe == '7d':
            return self.quality_history[-100:]
        else:
            return self.quality_history
    
    def _calculate_score_trend(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall score trend"""
        scores = [entry['overall_score'] for entry in history]
        
        if len(scores) < 2:
            return {'trend': 'insufficient_data'}
        
        # Simple linear trend calculation
        start_score = scores[0]
        end_score = scores[-1]
        change = end_score - start_score
        
        return {
            'start_score': start_score,
            'end_score': end_score,
            'change': change,
            'trend': 'improving' if change > 2 else 'declining' if change < -2 else 'stable'
        }
    
    def _calculate_component_trends(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate component-specific trends"""
        # Simplified component trend calculation
        return {'status': 'not_implemented'}
    
    def _calculate_issue_trends(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate issue count trends"""
        issue_counts = [entry['issue_count'] for entry in history]
        
        if len(issue_counts) < 2:
            return {'trend': 'insufficient_data'}
        
        start_count = issue_counts[0]
        end_count = issue_counts[-1]
        change = end_count - start_count
        
        return {
            'start_count': start_count,
            'end_count': end_count,
            'change': change,
            'trend': 'improving' if change < 0 else 'declining' if change > 0 else 'stable'
        }
    
    def _calculate_quality_velocity(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate rate of quality improvement/decline"""
        if len(history) < 3:
            return {'velocity': 'insufficient_data'}
        
        # Calculate average change per time period
        scores = [entry['overall_score'] for entry in history]
        changes = [scores[i] - scores[i-1] for i in range(1, len(scores))]
        avg_change = sum(changes) / len(changes) if changes else 0
        
        return {
            'average_change_per_period': avg_change,
            'velocity': 'accelerating' if avg_change > 1 else 'decelerating' if avg_change < -1 else 'steady'
        }