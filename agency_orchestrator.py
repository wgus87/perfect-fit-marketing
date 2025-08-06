"""
AI Agency Orchestrator - Master control system for all AI agents
This script coordinates and manages all AI agents to run the automated marketing agency
"""

import asyncio
import schedule
import time
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import threading
import subprocess
import sys
import os

# Import all agent modules
sys.path.append(os.path.dirname(__file__))
from agents.lead_generation_agent import LeadGenerationAgent
from agents.prospect_research_agent import ProspectResearchAgent
from agents.lead_scoring_agent import LeadScoringAgent
from agents.lead_qualification_agent import LeadQualificationAgent
from agents.outreach_automation_agent import OutreachAutomationAgent
from agents.sales_automation_agent import SalesAutomationAgent
from agents.client_management_agent import ClientManagementAgent
from agents.data_management_agent import DataManagementAgent
from agents.customer_service_agent import CustomerServiceAgent


@dataclass
class AgentStatus:
    """Agent status tracking"""
    name: str
    status: str  # active, idle, error, disabled
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    error_count: int = 0
    performance_score: float = 0.0
    tasks_completed: int = 0


@dataclass
class SystemMetrics:
    """System-wide performance metrics"""
    leads_generated_today: int = 0
    leads_qualified_today: int = 0
    outreach_sent_today: int = 0
    proposals_created_today: int = 0
    deals_closed_today: int = 0
    revenue_generated_today: float = 0.0
    system_uptime: float = 0.0
    error_rate: float = 0.0


class AgencyOrchestrator:
    """
    Master orchestrator for the AI marketing agency
    Coordinates all agents and manages the complete automation workflow
    """
    
    def __init__(self, database_path: str = "leads.db"):
        self.database_path = database_path
        self.setup_logging()
        self.setup_database()
        
        # Initialize all agents
        self.agents = self.initialize_agents()
        
        # Agent status tracking
        self.agent_status = {name: AgentStatus(name=name, status="idle") for name in self.agents.keys()}
        
        # System metrics
        self.metrics = SystemMetrics()
        self.start_time = datetime.now()
        
        # Configuration
        self.config = self.load_configuration()
        
        # Scheduling
        self.setup_schedules()
        
        # Health monitoring
        self.health_check_interval = 300  # 5 minutes
        self.max_error_threshold = 5
        
        # Running state
        self.is_running = False
        self.shutdown_requested = False
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('agency_orchestrator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_database(self):
        """Setup orchestrator database tables"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orchestrator_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                agent_name TEXT,
                action TEXT,
                status TEXT,
                details TEXT,
                execution_time REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                leads_generated INTEGER,
                leads_qualified INTEGER,
                outreach_sent INTEGER,
                proposals_created INTEGER,
                deals_closed INTEGER,
                revenue_generated REAL,
                system_uptime REAL,
                error_rate REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def initialize_agents(self) -> Dict[str, object]:
        """Initialize all AI agents"""
        agents = {}
        
        try:
            agents['lead_generation'] = LeadGenerationAgent(self.database_path)
            agents['prospect_research'] = ProspectResearchAgent(self.database_path)
            agents['lead_scoring'] = LeadScoringAgent(self.database_path)
            agents['lead_qualification'] = LeadQualificationAgent(self.database_path)
            agents['outreach_automation'] = OutreachAutomationAgent(self.database_path)
            agents['sales_automation'] = SalesAutomationAgent(self.database_path)
            agents['client_management'] = ClientManagementAgent(self.database_path)
            agents['data_management'] = DataManagementAgent(self.database_path)
            agents['customer_service'] = CustomerServiceAgent(self.database_path)
            
            self.logger.info(f"Initialized {len(agents)} AI agents successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing agents: {str(e)}")
        
        return agents
    
    def load_configuration(self) -> Dict:
        """Load system configuration"""
        default_config = {
            'lead_generation': {
                'enabled': True,
                'schedule': 'daily',
                'target_leads_per_day': 20,
                'max_concurrent_searches': 3
            },
            'prospect_research': {
                'enabled': True,
                'schedule': 'hourly',
                'batch_size': 10
            },
            'lead_scoring': {
                'enabled': True,
                'schedule': 'hourly',
                'batch_size': 50
            },
            'lead_qualification': {
                'enabled': True,
                'schedule': 'every_2_hours',
                'batch_size': 20
            },
            'outreach_automation': {
                'enabled': True,
                'schedule': 'daily',
                'max_outreach_per_day': 100
            },
            'sales_automation': {
                'enabled': True,
                'schedule': 'daily',
                'follow_up_frequency': 3
            },
            'client_management': {
                'enabled': True,
                'schedule': 'daily',
                'report_frequency': 'monthly'
            },
            'data_management': {
                'enabled': True,
                'schedule': 'daily',
                'maintenance_frequency': 'daily',
                'optimization_frequency': 'weekly'
            },
            'customer_service': {
                'enabled': True,
                'schedule': 'hourly',
                'response_time_target_minutes': 240,
                'gratitude_message_frequency': 'daily'
            }
        }
        
        # Try to load from file, fallback to default
        try:
            with open('agency_config.json', 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for agent, settings in default_config.items():
                    if agent not in config:
                        config[agent] = settings
                return config
        except FileNotFoundError:
            # Save default config
            with open('agency_config.json', 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def setup_schedules(self):
        """Setup automated schedules for all agents"""
        
        # Lead Generation - Daily at 9 AM
        schedule.every().day.at("09:00").do(self.run_lead_generation)
        
        # Prospect Research - Every 2 hours
        schedule.every(2).hours.do(self.run_prospect_research)
        
        # Lead Scoring - Every hour
        schedule.every().hour.do(self.run_lead_scoring)
        
        # Lead Qualification - Every 3 hours
        schedule.every(3).hours.do(self.run_lead_qualification)
        
        # Outreach Automation - Daily at 10 AM
        schedule.every().day.at("10:00").do(self.run_outreach_automation)
        
        # Sales Automation - Daily at 2 PM
        schedule.every().day.at("14:00").do(self.run_sales_automation)
        
        # Client Management - Daily at 5 PM
        schedule.every().day.at("17:00").do(self.run_client_management)
        
        # Data Management - Daily at 11 PM (maintenance cycle)
        schedule.every().day.at("23:00").do(self.run_data_management)
        
        # Customer Service - Every hour for request processing
        schedule.every().hour.do(self.run_customer_service)
        
        # System health check - Every 5 minutes
        schedule.every(5).minutes.do(self.health_check)
        
        # Daily metrics collection - Daily at midnight
        schedule.every().day.at("00:00").do(self.collect_daily_metrics)
        
        self.logger.info("Scheduled all agent tasks")
    
    def run_agent_task(self, agent_name: str, task_function, *args, **kwargs):
        """Run an agent task with error handling and logging"""
        start_time = time.time()
        
        try:
            self.agent_status[agent_name].status = "active"
            self.agent_status[agent_name].last_run = datetime.now()
            
            self.logger.info(f"Starting {agent_name} task")
            
            # Execute the task
            result = task_function(*args, **kwargs)
            
            # Update status
            execution_time = time.time() - start_time
            self.agent_status[agent_name].status = "idle"
            self.agent_status[agent_name].last_success = datetime.now()
            self.agent_status[agent_name].tasks_completed += 1
            self.agent_status[agent_name].error_count = 0  # Reset error count on success
            
            # Log success
            self.log_agent_activity(agent_name, "task_completed", "success", 
                                  f"Completed in {execution_time:.2f}s", execution_time)
            
            self.logger.info(f"Completed {agent_name} task in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.agent_status[agent_name].status = "error"
            self.agent_status[agent_name].error_count += 1
            
            error_msg = f"Error in {agent_name}: {str(e)}"
            self.logger.error(error_msg)
            
            # Log error
            self.log_agent_activity(agent_name, "task_failed", "error", error_msg, execution_time)
            
            # Disable agent if too many errors
            if self.agent_status[agent_name].error_count >= self.max_error_threshold:
                self.agent_status[agent_name].status = "disabled"
                self.logger.critical(f"Disabled {agent_name} due to excessive errors")
            
            return None
    
    def run_lead_generation(self):
        """Run lead generation agent"""
        if not self.config['lead_generation']['enabled']:
            return
        
        agent = self.agents.get('lead_generation')
        if agent:
            target_leads = self.config['lead_generation']['target_leads_per_day']
            self.run_agent_task('lead_generation', agent.generate_leads_batch, target_leads)
    
    def run_prospect_research(self):
        """Run prospect research agent"""
        if not self.config['prospect_research']['enabled']:
            return
        
        agent = self.agents.get('prospect_research')
        if agent:
            batch_size = self.config['prospect_research']['batch_size']
            self.run_agent_task('prospect_research', agent.research_leads_batch, batch_size)
    
    def run_lead_scoring(self):
        """Run lead scoring agent"""
        if not self.config['lead_scoring']['enabled']:
            return
        
        agent = self.agents.get('lead_scoring')
        if agent:
            batch_size = self.config['lead_scoring']['batch_size']
            self.run_agent_task('lead_scoring', agent.score_leads_batch, batch_size)
    
    def run_lead_qualification(self):
        """Run lead qualification agent"""
        if not self.config['lead_qualification']['enabled']:
            return
        
        agent = self.agents.get('lead_qualification')
        if agent:
            batch_size = self.config['lead_qualification']['batch_size']
            self.run_agent_task('lead_qualification', agent.qualify_leads_batch, batch_size)
    
    def run_outreach_automation(self):
        """Run outreach automation agent"""
        if not self.config['outreach_automation']['enabled']:
            return
        
        agent = self.agents.get('outreach_automation')
        if agent:
            max_outreach = self.config['outreach_automation']['max_outreach_per_day']
            self.run_agent_task('outreach_automation', agent.run_outreach_campaign, max_outreach)
    
    def run_sales_automation(self):
        """Run sales automation agent"""
        if not self.config['sales_automation']['enabled']:
            return
        
        agent = self.agents.get('sales_automation')
        if agent:
            self.run_agent_task('sales_automation', agent.process_qualified_leads)
    
    def run_client_management(self):
        """Run client management agent"""
        if not self.config['client_management']['enabled']:
            return
        
        agent = self.agents.get('client_management')
        if agent:
            self.run_agent_task('client_management', agent.process_client_activities)
    
    def run_data_management(self):
        """Run data management agent maintenance cycle"""
        if not self.config['data_management']['enabled']:
            return
        
        agent = self.agents.get('data_management')
        if agent:
            self.run_agent_task('data_management', agent.run_maintenance_cycle)
    
    def run_customer_service(self):
        """Run customer service agent processing cycle"""
        if not self.config['customer_service']['enabled']:
            return
        
        agent = self.agents.get('customer_service')
        if agent:
            self.run_agent_task('customer_service', agent.run_customer_service_cycle)
    
    def health_check(self):
        """Perform system health check"""
        try:
            # Check database connectivity
            conn = sqlite3.connect(self.database_path)
            conn.execute('SELECT 1')
            conn.close()
            
            # Check agent status
            active_agents = sum(1 for status in self.agent_status.values() if status.status != "disabled")
            total_agents = len(self.agent_status)
            
            # Update system metrics
            self.metrics.system_uptime = (datetime.now() - self.start_time).total_seconds() / 3600  # hours
            
            # Calculate error rate
            total_errors = sum(status.error_count for status in self.agent_status.values())
            total_tasks = sum(status.tasks_completed for status in self.agent_status.values())
            self.metrics.error_rate = (total_errors / max(total_tasks, 1)) * 100
            
            self.logger.info(f"Health check: {active_agents}/{total_agents} agents active, "
                           f"uptime: {self.metrics.system_uptime:.1f}h, "
                           f"error rate: {self.metrics.error_rate:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
    
    def collect_daily_metrics(self):
        """Collect and store daily performance metrics"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get today's metrics
            today = datetime.now().date()
            
            # Count leads generated today
            cursor.execute('SELECT COUNT(*) FROM leads WHERE DATE(created_date) = ?', (today,))
            self.metrics.leads_generated_today = cursor.fetchone()[0]
            
            # Count qualified leads today
            cursor.execute('SELECT COUNT(*) FROM lead_qualifications WHERE DATE(qualification_date) = ? AND status = "qualified"', (today,))
            self.metrics.leads_qualified_today = cursor.fetchone()[0]
            
            # Count outreach sent today
            cursor.execute('SELECT COUNT(*) FROM outreach_messages WHERE DATE(sent_date) = ?', (today,))
            self.metrics.outreach_sent_today = cursor.fetchone()[0]
            
            # Count proposals created today
            cursor.execute('SELECT COUNT(*) FROM sales_proposals WHERE DATE(proposal_date) = ?', (today,))
            self.metrics.proposals_created_today = cursor.fetchone()[0]
            
            # Count deals closed today
            cursor.execute('SELECT COUNT(*), SUM(value) FROM sales_deals WHERE DATE(last_activity) = ? AND stage = "closed_won"', (today,))
            result = cursor.fetchone()
            self.metrics.deals_closed_today = result[0] or 0
            self.metrics.revenue_generated_today = result[1] or 0.0
            
            # Store metrics
            cursor.execute('''
                INSERT INTO system_metrics (
                    date, leads_generated, leads_qualified, outreach_sent,
                    proposals_created, deals_closed, revenue_generated,
                    system_uptime, error_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                today.isoformat(),
                self.metrics.leads_generated_today,
                self.metrics.leads_qualified_today,
                self.metrics.outreach_sent_today,
                self.metrics.proposals_created_today,
                self.metrics.deals_closed_today,
                self.metrics.revenue_generated_today,
                self.metrics.system_uptime,
                self.metrics.error_rate
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Daily metrics collected: {self.metrics.leads_generated_today} leads, "
                           f"{self.metrics.deals_closed_today} deals, "
                           f"${self.metrics.revenue_generated_today:.2f} revenue")
            
        except Exception as e:
            self.logger.error(f"Error collecting daily metrics: {str(e)}")
    
    def log_agent_activity(self, agent_name: str, action: str, status: str, details: str, execution_time: float):
        """Log agent activity to database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO orchestrator_logs (
                    timestamp, agent_name, action, status, details, execution_time
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                agent_name,
                action,
                status,
                details,
                execution_time
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error logging activity: {str(e)}")
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            'agents': {name: {
                'status': status.status,
                'last_run': status.last_run.isoformat() if status.last_run else None,
                'last_success': status.last_success.isoformat() if status.last_success else None,
                'error_count': status.error_count,
                'tasks_completed': status.tasks_completed
            } for name, status in self.agent_status.items()},
            'metrics': {
                'leads_generated_today': self.metrics.leads_generated_today,
                'leads_qualified_today': self.metrics.leads_qualified_today,
                'outreach_sent_today': self.metrics.outreach_sent_today,
                'proposals_created_today': self.metrics.proposals_created_today,
                'deals_closed_today': self.metrics.deals_closed_today,
                'revenue_generated_today': self.metrics.revenue_generated_today,
                'system_uptime': self.metrics.system_uptime,
                'error_rate': self.metrics.error_rate
            },
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat()
        }
    
    def start(self):
        """Start the orchestrator"""
        self.logger.info("Starting AI Agency Orchestrator")
        self.is_running = True
        
        # Run initial health check
        self.health_check()
        
        # Start scheduler loop
        while not self.shutdown_requested:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Received shutdown signal")
                self.shutdown()
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                time.sleep(5)  # Wait before retrying
    
    def shutdown(self):
        """Gracefully shutdown the orchestrator"""
        self.logger.info("Shutting down AI Agency Orchestrator")
        self.shutdown_requested = True
        self.is_running = False
        
        # Update agent status
        for status in self.agent_status.values():
            if status.status == "active":
                status.status = "idle"
        
        # Final metrics collection
        self.collect_daily_metrics()
        
        self.logger.info("Orchestrator shutdown complete")
    
    def run_manual_task(self, agent_name: str, task_name: str = None):
        """Manually run a specific agent task"""
        if agent_name not in self.agents:
            self.logger.error(f"Unknown agent: {agent_name}")
            return False
        
        if agent_name == 'lead_generation':
            self.run_lead_generation()
        elif agent_name == 'prospect_research':
            self.run_prospect_research()
        elif agent_name == 'lead_scoring':
            self.run_lead_scoring()
        elif agent_name == 'lead_qualification':
            self.run_lead_qualification()
        elif agent_name == 'outreach_automation':
            self.run_outreach_automation()
        elif agent_name == 'sales_automation':
            self.run_sales_automation()
        elif agent_name == 'client_management':
            self.run_client_management()
        else:
            self.logger.error(f"No manual task defined for agent: {agent_name}")
            return False
        
        return True


def main():
    """Main function to run the orchestrator"""
    orchestrator = AgencyOrchestrator()
    
    try:
        # Check if running in manual mode
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "status":
                status = orchestrator.get_system_status()
                print(json.dumps(status, indent=2))
                
            elif command == "run" and len(sys.argv) > 2:
                agent_name = sys.argv[2]
                success = orchestrator.run_manual_task(agent_name)
                if success:
                    print(f"Successfully ran {agent_name} task")
                else:
                    print(f"Failed to run {agent_name} task")
                    
            elif command == "health":
                orchestrator.health_check()
                print("Health check completed")
                
            else:
                print("Usage: python agency_orchestrator.py [status|run <agent_name>|health]")
        else:
            # Run in continuous mode
            orchestrator.start()
            
    except Exception as e:
        orchestrator.logger.error(f"Fatal error: {str(e)}")
        orchestrator.shutdown()


if __name__ == "__main__":
    main()

