"""
Data Management and Optimization Agent
Handles data validation, error detection, and database optimization for the AI Marketing Agency
"""

import sqlite3
import logging
import json
import os
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd
from collections import defaultdict, Counter
import sys

# Add parent directory to path to import API modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class DataQualityIssue:
    """Represents a data quality issue found in the database"""
    table_name: str
    column_name: str
    issue_type: str
    issue_description: str
    affected_rows: int
    severity: str  # 'low', 'medium', 'high', 'critical'
    suggested_fix: str
    timestamp: datetime


@dataclass
class ErrorPattern:
    """Represents a pattern of errors found in logs"""
    error_type: str
    error_message: str
    frequency: int
    first_occurrence: datetime
    last_occurrence: datetime
    affected_components: List[str]
    severity: str


@dataclass
class DatabaseMetrics:
    """Database performance and health metrics"""
    total_records: int
    table_sizes: Dict[str, int]
    index_usage: Dict[str, float]
    query_performance: Dict[str, float]
    storage_usage: float
    fragmentation_level: float
    last_optimization: Optional[datetime]


class DataManagementAgent:
    """
    AI-powered data management agent that ensures data quality, 
    detects errors, and optimizes database performance
    """
    
    def __init__(self, database_path: str = "leads.db", log_directory: str = "logs"):
        self.database_path = database_path
        self.log_directory = log_directory
        self.logger = logging.getLogger(__name__)
        
        # Data quality thresholds
        self.quality_thresholds = {
            'missing_data_percentage': 10.0,  # Max % of missing data allowed
            'duplicate_percentage': 5.0,      # Max % of duplicates allowed
            'invalid_email_percentage': 15.0, # Max % of invalid emails allowed
            'stale_data_days': 30,            # Days before data is considered stale
            'error_rate_threshold': 5.0       # Max error rate percentage
        }
        
        # Database optimization settings
        self.optimization_settings = {
            'vacuum_threshold_mb': 100,       # Run VACUUM when DB grows by this much
            'analyze_frequency_hours': 24,    # Run ANALYZE every N hours
            'index_rebuild_threshold': 0.3,   # Rebuild index if fragmentation > 30%
            'archive_threshold_days': 90      # Archive data older than N days
        }
        
        self.setup_logging()
        self.setup_data_quality_tables()
    
    def setup_logging(self):
        """Setup logging for the data management agent"""
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)
        
        log_file = os.path.join(self.log_directory, "data_management.log")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def setup_data_quality_tables(self):
        """Setup tables for tracking data quality issues and metrics"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Data quality issues table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_quality_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                column_name TEXT,
                issue_type TEXT NOT NULL,
                issue_description TEXT,
                affected_rows INTEGER,
                severity TEXT,
                suggested_fix TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT
            )
        ''')
        
        # Database metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS database_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_date TEXT NOT NULL,
                total_records INTEGER,
                table_sizes TEXT,
                storage_usage_mb REAL,
                fragmentation_level REAL,
                optimization_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Error patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT NOT NULL,
                error_message TEXT,
                frequency INTEGER,
                first_occurrence TEXT,
                last_occurrence TEXT,
                affected_components TEXT,
                severity TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def run_data_quality_check(self) -> List[DataQualityIssue]:
        """
        Comprehensive data quality check across all tables
        """
        self.logger.info("Starting comprehensive data quality check...")
        issues = []
        
        conn = sqlite3.connect(self.database_path)
        
        try:
            # Check leads table
            issues.extend(self._check_leads_table_quality(conn))
            
            # Check API usage tables
            issues.extend(self._check_api_tables_quality(conn))
            
            # Check for orphaned records
            issues.extend(self._check_referential_integrity(conn))
            
            # Check for data freshness
            issues.extend(self._check_data_freshness(conn))
            
            # Store issues in database
            self._store_quality_issues(conn, issues)
            
        except Exception as e:
            self.logger.error(f"Error during data quality check: {str(e)}")
        finally:
            conn.close()
        
        self.logger.info(f"Data quality check completed. Found {len(issues)} issues.")
        return issues
    
    def _check_leads_table_quality(self, conn: sqlite3.Connection) -> List[DataQualityIssue]:
        """Check data quality in the leads table"""
        issues = []
        cursor = conn.cursor()
        
        # Get total record count
        cursor.execute("SELECT COUNT(*) FROM leads")
        total_records = cursor.fetchone()[0]
        
        if total_records == 0:
            return issues
        
        # Check for missing company names
        cursor.execute("SELECT COUNT(*) FROM leads WHERE company_name IS NULL OR company_name = ''")
        missing_company_names = cursor.fetchone()[0]
        if missing_company_names > 0:
            percentage = (missing_company_names / total_records) * 100
            severity = 'high' if percentage > self.quality_thresholds['missing_data_percentage'] else 'medium'
            issues.append(DataQualityIssue(
                table_name='leads',
                column_name='company_name',
                issue_type='missing_data',
                issue_description=f'{missing_company_names} records missing company name ({percentage:.1f}%)',
                affected_rows=missing_company_names,
                severity=severity,
                suggested_fix='Update records with valid company names or remove invalid entries',
                timestamp=datetime.now()
            ))
        
        # Check for invalid email formats
        cursor.execute("""
            SELECT COUNT(*) FROM leads 
            WHERE contact_email IS NOT NULL 
            AND contact_email != ''
            AND contact_email NOT LIKE '%@%.%'
        """)
        invalid_emails = cursor.fetchone()[0]
        if invalid_emails > 0:
            percentage = (invalid_emails / total_records) * 100
            severity = 'high' if percentage > self.quality_thresholds['invalid_email_percentage'] else 'medium'
            issues.append(DataQualityIssue(
                table_name='leads',
                column_name='contact_email',
                issue_type='invalid_format',
                issue_description=f'{invalid_emails} records with invalid email format ({percentage:.1f}%)',
                affected_rows=invalid_emails,
                severity=severity,
                suggested_fix='Validate and correct email formats using email validation API',
                timestamp=datetime.now()
            ))
        
        # Check for duplicate companies
        cursor.execute("""
            SELECT company_name, COUNT(*) as count 
            FROM leads 
            WHERE company_name IS NOT NULL AND company_name != ''
            GROUP BY LOWER(company_name) 
            HAVING count > 1
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            total_duplicates = sum(count - 1 for _, count in duplicates)
            percentage = (total_duplicates / total_records) * 100
            severity = 'medium' if percentage > self.quality_thresholds['duplicate_percentage'] else 'low'
            issues.append(DataQualityIssue(
                table_name='leads',
                column_name='company_name',
                issue_type='duplicates',
                issue_description=f'{total_duplicates} duplicate company records ({percentage:.1f}%)',
                affected_rows=total_duplicates,
                severity=severity,
                suggested_fix='Merge duplicate records or implement deduplication logic',
                timestamp=datetime.now()
            ))
        
        # Check for missing contact information
        cursor.execute("""
            SELECT COUNT(*) FROM leads 
            WHERE (contact_email IS NULL OR contact_email = '') 
            AND (phone IS NULL OR phone = '')
        """)
        missing_contact = cursor.fetchone()[0]
        if missing_contact > 0:
            percentage = (missing_contact / total_records) * 100
            severity = 'high' if percentage > 20 else 'medium'
            issues.append(DataQualityIssue(
                table_name='leads',
                column_name='contact_info',
                issue_type='missing_data',
                issue_description=f'{missing_contact} records missing all contact information ({percentage:.1f}%)',
                affected_rows=missing_contact,
                severity=severity,
                suggested_fix='Enrich records with contact information using data enrichment APIs',
                timestamp=datetime.now()
            ))
        
        return issues
    
    def _check_api_tables_quality(self, conn: sqlite3.Connection) -> List[DataQualityIssue]:
        """Check data quality in API-related tables"""
        issues = []
        cursor = conn.cursor()
        
        # Check for API usage anomalies
        try:
            cursor.execute("SELECT COUNT(*) FROM api_usage")
            if cursor.fetchone()[0] > 0:
                # Check for unusually high error rates
                cursor.execute("""
                    SELECT api_name, 
                           SUM(errors_count) as total_errors,
                           SUM(requests_count) as total_requests
                    FROM api_usage 
                    WHERE date >= date('now', '-7 days')
                    GROUP BY api_name
                """)
                
                for api_name, errors, requests in cursor.fetchall():
                    if requests > 0:
                        error_rate = (errors / requests) * 100
                        if error_rate > self.quality_thresholds['error_rate_threshold']:
                            issues.append(DataQualityIssue(
                                table_name='api_usage',
                                column_name='errors_count',
                                issue_type='high_error_rate',
                                issue_description=f'API {api_name} has {error_rate:.1f}% error rate',
                                affected_rows=errors,
                                severity='high' if error_rate > 20 else 'medium',
                                suggested_fix=f'Investigate {api_name} API issues and implement error handling',
                                timestamp=datetime.now()
                            ))
        except sqlite3.OperationalError:
            # API tables don't exist yet
            pass
        
        return issues
    
    def _check_referential_integrity(self, conn: sqlite3.Connection) -> List[DataQualityIssue]:
        """Check for referential integrity issues"""
        issues = []
        # Add referential integrity checks as the schema evolves
        return issues
    
    def _check_data_freshness(self, conn: sqlite3.Connection) -> List[DataQualityIssue]:
        """Check for stale data"""
        issues = []
        cursor = conn.cursor()
        
        # Check for old leads that haven't been updated
        stale_threshold = datetime.now() - timedelta(days=self.quality_thresholds['stale_data_days'])
        cursor.execute("""
            SELECT COUNT(*) FROM leads 
            WHERE created_date < ? AND last_contact_date IS NULL
        """, (stale_threshold.isoformat(),))
        
        stale_leads = cursor.fetchone()[0]
        if stale_leads > 0:
            issues.append(DataQualityIssue(
                table_name='leads',
                column_name='last_contact_date',
                issue_type='stale_data',
                issue_description=f'{stale_leads} leads older than {self.quality_thresholds["stale_data_days"]} days with no contact',
                affected_rows=stale_leads,
                severity='medium',
                suggested_fix='Archive old leads or attempt re-engagement',
                timestamp=datetime.now()
            ))
        
        return issues
    
    def _store_quality_issues(self, conn: sqlite3.Connection, issues: List[DataQualityIssue]):
        """Store data quality issues in the database"""
        cursor = conn.cursor()
        
        for issue in issues:
            cursor.execute('''
                INSERT INTO data_quality_issues (
                    table_name, column_name, issue_type, issue_description,
                    affected_rows, severity, suggested_fix
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                issue.table_name, issue.column_name, issue.issue_type,
                issue.issue_description, issue.affected_rows, issue.severity,
                issue.suggested_fix
            ))
        
        conn.commit()
    
    def analyze_error_logs(self) -> List[ErrorPattern]:
        """
        Analyze error logs to identify patterns and recurring issues
        """
        self.logger.info("Analyzing error logs for patterns...")
        patterns = []
        
        # Analyze orchestrator logs
        orchestrator_log = os.path.join(self.log_directory, "orchestrator.log")
        if os.path.exists(orchestrator_log):
            patterns.extend(self._analyze_log_file(orchestrator_log, "orchestrator"))
        
        # Analyze data management logs
        data_log = os.path.join(self.log_directory, "data_management.log")
        if os.path.exists(data_log):
            patterns.extend(self._analyze_log_file(data_log, "data_management"))
        
        # Store patterns in database
        self._store_error_patterns(patterns)
        
        self.logger.info(f"Error log analysis completed. Found {len(patterns)} patterns.")
        return patterns
    
    def _analyze_log_file(self, log_file: str, component: str) -> List[ErrorPattern]:
        """Analyze a specific log file for error patterns"""
        patterns = []
        error_counts = defaultdict(int)
        error_details = defaultdict(lambda: {'first': None, 'last': None, 'messages': []})
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if 'ERROR' in line or 'CRITICAL' in line:
                        # Extract timestamp and error message
                        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if timestamp_match:
                            timestamp_str = timestamp_match.group(1)
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            
                            # Extract error type and message
                            error_msg = line.split(' - ')[-1].strip()
                            error_type = self._classify_error(error_msg)
                            
                            error_counts[error_type] += 1
                            
                            if error_details[error_type]['first'] is None:
                                error_details[error_type]['first'] = timestamp
                            error_details[error_type]['last'] = timestamp
                            error_details[error_type]['messages'].append(error_msg)
        
        except Exception as e:
            self.logger.error(f"Error analyzing log file {log_file}: {str(e)}")
        
        # Create error patterns
        for error_type, count in error_counts.items():
            if count >= 3:  # Only report patterns with 3+ occurrences
                severity = self._determine_error_severity(error_type, count)
                patterns.append(ErrorPattern(
                    error_type=error_type,
                    error_message=error_details[error_type]['messages'][0],
                    frequency=count,
                    first_occurrence=error_details[error_type]['first'],
                    last_occurrence=error_details[error_type]['last'],
                    affected_components=[component],
                    severity=severity
                ))
        
        return patterns
    
    def _classify_error(self, error_message: str) -> str:
        """Classify error message into categories"""
        error_message_lower = error_message.lower()
        
        if 'database' in error_message_lower or 'sqlite' in error_message_lower:
            return 'database_error'
        elif 'api' in error_message_lower or 'request' in error_message_lower:
            return 'api_error'
        elif 'connection' in error_message_lower or 'timeout' in error_message_lower:
            return 'connection_error'
        elif 'permission' in error_message_lower or 'access' in error_message_lower:
            return 'permission_error'
        elif 'memory' in error_message_lower or 'resource' in error_message_lower:
            return 'resource_error'
        else:
            return 'general_error'
    
    def _determine_error_severity(self, error_type: str, frequency: int) -> str:
        """Determine error severity based on type and frequency"""
        if frequency > 50:
            return 'critical'
        elif frequency > 20:
            return 'high'
        elif frequency > 10:
            return 'medium'
        else:
            return 'low'
    
    def _store_error_patterns(self, patterns: List[ErrorPattern]):
        """Store error patterns in the database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        for pattern in patterns:
            cursor.execute('''
                INSERT OR REPLACE INTO error_patterns (
                    error_type, error_message, frequency, first_occurrence,
                    last_occurrence, affected_components, severity
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.error_type, pattern.error_message, pattern.frequency,
                pattern.first_occurrence.isoformat(), pattern.last_occurrence.isoformat(),
                json.dumps(pattern.affected_components), pattern.severity
            ))
        
        conn.commit()
        conn.close()
    
    def optimize_database(self) -> Dict[str, Any]:
        """
        Perform database optimization tasks
        """
        self.logger.info("Starting database optimization...")
        optimization_results = {}
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            # Get database size before optimization
            initial_size = os.path.getsize(self.database_path) / (1024 * 1024)  # MB
            
            # Run VACUUM to reclaim space
            self.logger.info("Running VACUUM...")
            start_time = time.time()
            cursor.execute("VACUUM")
            vacuum_time = time.time() - start_time
            optimization_results['vacuum_time'] = vacuum_time
            
            # Run ANALYZE to update statistics
            self.logger.info("Running ANALYZE...")
            start_time = time.time()
            cursor.execute("ANALYZE")
            analyze_time = time.time() - start_time
            optimization_results['analyze_time'] = analyze_time
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Optimize SQLite settings
            cursor.execute("PRAGMA optimize")
            
            # Get database size after optimization
            final_size = os.path.getsize(self.database_path) / (1024 * 1024)  # MB
            space_saved = initial_size - final_size
            
            optimization_results.update({
                'initial_size_mb': initial_size,
                'final_size_mb': final_size,
                'space_saved_mb': space_saved,
                'optimization_timestamp': datetime.now().isoformat()
            })
            
            # Store optimization metrics
            self._store_database_metrics(conn, optimization_results)
            
        except Exception as e:
            self.logger.error(f"Error during database optimization: {str(e)}")
            optimization_results['error'] = str(e)
        finally:
            conn.close()
        
        self.logger.info(f"Database optimization completed. Saved {optimization_results.get('space_saved_mb', 0):.2f} MB")
        return optimization_results
    
    def _store_database_metrics(self, conn: sqlite3.Connection, metrics: Dict[str, Any]):
        """Store database optimization metrics"""
        cursor = conn.cursor()
        
        # Get table sizes
        table_sizes = {}
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            table_sizes[table_name] = count
        
        cursor.execute('''
            INSERT INTO database_metrics (
                metric_date, total_records, table_sizes, storage_usage_mb,
                fragmentation_level, optimization_score
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().date().isoformat(),
            sum(table_sizes.values()),
            json.dumps(table_sizes),
            metrics.get('final_size_mb', 0),
            0.0,  # Fragmentation calculation would need more complex analysis
            85.0  # Placeholder optimization score
        ))
        
        conn.commit()
    
    def generate_data_quality_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive data quality report
        """
        self.logger.info("Generating data quality report...")
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'summary': {},
            'issues_by_severity': {},
            'error_patterns': {},
            'database_health': {},
            'recommendations': []
        }
        
        try:
            # Get summary of data quality issues
            cursor.execute('''
                SELECT severity, COUNT(*) 
                FROM data_quality_issues 
                WHERE status = 'open'
                GROUP BY severity
            ''')
            
            for severity, count in cursor.fetchall():
                report['issues_by_severity'][severity] = count
            
            # Get recent error patterns
            cursor.execute('''
                SELECT error_type, frequency, severity
                FROM error_patterns 
                WHERE status = 'active'
                ORDER BY frequency DESC
                LIMIT 10
            ''')
            
            error_patterns = []
            for error_type, frequency, severity in cursor.fetchall():
                error_patterns.append({
                    'type': error_type,
                    'frequency': frequency,
                    'severity': severity
                })
            report['error_patterns'] = error_patterns
            
            # Get database health metrics
            cursor.execute('''
                SELECT storage_usage_mb, optimization_score
                FROM database_metrics 
                ORDER BY created_at DESC 
                LIMIT 1
            ''')
            
            metrics = cursor.fetchone()
            if metrics:
                report['database_health'] = {
                    'storage_usage_mb': metrics[0],
                    'optimization_score': metrics[1]
                }
            
            # Generate recommendations
            report['recommendations'] = self._generate_recommendations(report)
            
            # Calculate overall health score
            report['summary']['overall_health_score'] = self._calculate_health_score(report)
            
        except Exception as e:
            self.logger.error(f"Error generating data quality report: {str(e)}")
            report['error'] = str(e)
        finally:
            conn.close()
        
        return report
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on the report"""
        recommendations = []
        
        # Check for critical issues
        critical_issues = report['issues_by_severity'].get('critical', 0)
        if critical_issues > 0:
            recommendations.append(f"Address {critical_issues} critical data quality issues immediately")
        
        # Check for high error rates
        high_frequency_errors = [p for p in report['error_patterns'] if p['frequency'] > 20]
        if high_frequency_errors:
            recommendations.append("Investigate and fix high-frequency error patterns")
        
        # Check database health
        db_health = report['database_health']
        if db_health.get('storage_usage_mb', 0) > 500:
            recommendations.append("Consider archiving old data to reduce database size")
        
        if db_health.get('optimization_score', 100) < 70:
            recommendations.append("Run database optimization to improve performance")
        
        return recommendations
    
    def _calculate_health_score(self, report: Dict[str, Any]) -> float:
        """Calculate overall system health score (0-100)"""
        score = 100.0
        
        # Deduct points for issues
        issues = report['issues_by_severity']
        score -= issues.get('critical', 0) * 20
        score -= issues.get('high', 0) * 10
        score -= issues.get('medium', 0) * 5
        score -= issues.get('low', 0) * 1
        
        # Deduct points for error patterns
        for pattern in report['error_patterns']:
            if pattern['severity'] == 'critical':
                score -= 15
            elif pattern['severity'] == 'high':
                score -= 10
            elif pattern['severity'] == 'medium':
                score -= 5
        
        return max(0.0, min(100.0, score))
    
    def run_maintenance_cycle(self) -> Dict[str, Any]:
        """
        Run a complete maintenance cycle including all checks and optimizations
        """
        self.logger.info("Starting complete maintenance cycle...")
        
        maintenance_results = {
            'start_time': datetime.now().isoformat(),
            'data_quality_issues': [],
            'error_patterns': [],
            'optimization_results': {},
            'report': {}
        }
        
        try:
            # Run data quality checks
            maintenance_results['data_quality_issues'] = self.run_data_quality_check()
            
            # Analyze error logs
            maintenance_results['error_patterns'] = self.analyze_error_logs()
            
            # Optimize database
            maintenance_results['optimization_results'] = self.optimize_database()
            
            # Generate report
            maintenance_results['report'] = self.generate_data_quality_report()
            
            maintenance_results['end_time'] = datetime.now().isoformat()
            maintenance_results['status'] = 'completed'
            
        except Exception as e:
            self.logger.error(f"Error during maintenance cycle: {str(e)}")
            maintenance_results['status'] = 'failed'
            maintenance_results['error'] = str(e)
        
        self.logger.info("Maintenance cycle completed")
        return maintenance_results


if __name__ == "__main__":
    # Test the data management agent
    agent = DataManagementAgent()
    
    print("Running data management agent test...")
    
    # Run a complete maintenance cycle
    results = agent.run_maintenance_cycle()
    
    print(f"Maintenance cycle status: {results['status']}")
    print(f"Data quality issues found: {len(results['data_quality_issues'])}")
    print(f"Error patterns identified: {len(results['error_patterns'])}")
    
    if results['report']:
        health_score = results['report']['summary'].get('overall_health_score', 0)
        print(f"Overall health score: {health_score:.1f}/100")
        
        recommendations = results['report'].get('recommendations', [])
        if recommendations:
            print("Recommendations:")
            for rec in recommendations:
                print(f"  - {rec}")
    
    print("Data management agent test completed.")

