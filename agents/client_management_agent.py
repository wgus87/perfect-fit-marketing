"""
Client Management Agent - Automated client onboarding and service delivery
This agent handles the complete client lifecycle from onboarding to ongoing service delivery
"""

import sqlite3
import json
import openai
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid
import random


class ClientStatus(Enum):
    """Client status types"""
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    PAUSED = "paused"
    CHURNED = "churned"
    CANCELLED = "cancelled"


class ServiceStatus(Enum):
    """Service delivery status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    ON_HOLD = "on_hold"


class TaskType(Enum):
    """Service task types"""
    SEO_AUDIT = "seo_audit"
    CONTENT_CREATION = "content_creation"
    AD_CAMPAIGN_SETUP = "ad_campaign_setup"
    SOCIAL_MEDIA_SETUP = "social_media_setup"
    WEBSITE_OPTIMIZATION = "website_optimization"
    REPORTING = "reporting"
    STRATEGY_REVIEW = "strategy_review"


@dataclass
class Client:
    """Client data structure"""
    lead_id: int
    client_id: str
    company_name: str
    contact_name: str
    contact_email: str
    package: str
    monthly_value: int
    start_date: datetime
    status: ClientStatus
    onboarding_completed: bool = False
    last_activity: Optional[datetime] = None
    satisfaction_score: float = 0.0
    notes: str = ""
    
    def __post_init__(self):
        if not self.client_id:
            self.client_id = str(uuid.uuid4())[:8]
        if self.last_activity is None:
            self.last_activity = datetime.now()


@dataclass
class ServiceTask:
    """Service delivery task"""
    client_id: str
    task_id: str
    task_type: TaskType
    title: str
    description: str
    assigned_to: str
    due_date: datetime
    status: ServiceStatus
    priority: int = 1  # 1=high, 2=medium, 3=low
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    deliverables: List[str] = None
    completion_date: Optional[datetime] = None
    notes: str = ""
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())[:8]
        if self.deliverables is None:
            self.deliverables = []


@dataclass
class ClientReport:
    """Client performance report"""
    client_id: str
    report_id: str
    report_period: str
    metrics: Dict[str, any]
    insights: List[str]
    recommendations: List[str]
    generated_date: datetime
    sent_date: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.report_id:
            self.report_id = str(uuid.uuid4())[:8]
        if self.metrics is None:
            self.metrics = {}
        if self.insights is None:
            self.insights = []
        if self.recommendations is None:
            self.recommendations = []


class ClientManagementAgent:
    """
    AI-powered client management and service delivery agent
    """
    
    def __init__(self, database_path: str = "leads.db"):
        self.database_path = database_path
        self.setup_database()
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI()
        
        # Service delivery templates
        self.onboarding_templates = self.initialize_onboarding_templates()
        self.task_templates = self.initialize_task_templates()
        
        # Team assignments (in production, this would be dynamic)
        self.team_assignments = {
            'seo_specialist': 'Sarah Chen',
            'content_manager': 'Mike Rodriguez',
            'ads_manager': 'Jessica Kim',
            'social_media_manager': 'Alex Thompson',
            'account_manager': 'David Wilson'
        }
    
    def setup_database(self):
        """Initialize database tables for client management"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                client_id TEXT UNIQUE,
                company_name TEXT,
                contact_name TEXT,
                contact_email TEXT,
                package TEXT,
                monthly_value INTEGER,
                start_date TEXT,
                status TEXT,
                onboarding_completed BOOLEAN,
                last_activity TEXT,
                satisfaction_score REAL,
                notes TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT,
                task_id TEXT UNIQUE,
                task_type TEXT,
                title TEXT,
                description TEXT,
                assigned_to TEXT,
                due_date TEXT,
                status TEXT,
                priority INTEGER,
                estimated_hours REAL,
                actual_hours REAL,
                deliverables TEXT,
                completion_date TEXT,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT,
                report_id TEXT UNIQUE,
                report_period TEXT,
                metrics TEXT,
                insights TEXT,
                recommendations TEXT,
                generated_date TEXT,
                sent_date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_communications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT,
                communication_type TEXT,
                subject TEXT,
                content TEXT,
                sent_date TEXT,
                response_received BOOLEAN,
                response_date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def initialize_onboarding_templates(self) -> Dict[str, str]:
        """Initialize client onboarding email templates"""
        return {
            'welcome': """
Subject: Welcome to AI Marketing Solutions! Let's get started 🚀

Hi {contact_name},

Welcome to AI Marketing Solutions! We're thrilled to have {company_name} as our newest client.

Your {package} package is now active, and we're ready to transform your digital marketing results.

WHAT HAPPENS NEXT:
1. Account Setup (Week 1): We'll set up all necessary accounts and access
2. Strategy Development (Week 1-2): Our team will create your custom marketing strategy
3. Implementation (Week 2-3): We'll launch your campaigns and optimization efforts
4. Monitoring & Optimization (Ongoing): Continuous improvement and reporting

Your dedicated account manager is {account_manager}, and they'll be your primary point of contact throughout this journey.

We'll send you a detailed onboarding checklist within 24 hours with everything we need to get started.

Looking forward to driving amazing results for {company_name}!

Best regards,
The AI Marketing Solutions Team
            """,
            
            'onboarding_checklist': """
Subject: {company_name} Onboarding Checklist - Action Required

Hi {contact_name},

To ensure we can deliver the best results for {company_name}, we need access to a few key accounts and information.

REQUIRED ACCESS:
□ Google Analytics (Admin access)
□ Google Ads account (Admin access)
□ Facebook Business Manager (Admin access)
□ Website admin/FTP access
□ Current marketing materials and brand guidelines

INFORMATION NEEDED:
□ Target audience demographics
□ Key competitors
□ Current marketing challenges
□ Success metrics and goals
□ Budget allocation preferences

Please reply to this email with the requested access and information, or schedule a call with your account manager {account_manager} to go through everything together.

Timeline: We aim to complete onboarding within 5 business days of receiving all required access.

Questions? Reply to this email or call us at (555) 123-4567.

Best regards,
{account_manager}
Account Manager, AI Marketing Solutions
            """,
            
            'first_month_update': """
Subject: {company_name} - First Month Progress Update

Hi {contact_name},

We've completed your first month with AI Marketing Solutions! Here's what we've accomplished:

COMPLETED ACTIVITIES:
{completed_activities}

KEY METRICS (First 30 Days):
{key_metrics}

UPCOMING FOCUS AREAS:
{upcoming_focus}

Your dedicated team has been working hard to establish a strong foundation for your digital marketing success. We're excited about the momentum we're building!

Your detailed monthly report is attached, and we'd love to schedule a brief call to discuss these results and answer any questions.

Available times for a 15-minute call:
- {time_slot_1}
- {time_slot_2}
- {time_slot_3}

Just reply with your preferred time, or suggest an alternative that works better.

Best regards,
{account_manager}
            """
        }
    
    def initialize_task_templates(self) -> Dict[TaskType, Dict]:
        """Initialize service task templates"""
        return {
            TaskType.SEO_AUDIT: {
                'title': 'Complete SEO Audit for {company_name}',
                'description': 'Comprehensive SEO audit including technical, on-page, and off-page analysis',
                'estimated_hours': 8.0,
                'deliverables': [
                    'Technical SEO audit report',
                    'Keyword research and analysis',
                    'Competitor analysis',
                    'SEO strategy recommendations'
                ],
                'assigned_to': 'seo_specialist'
            },
            
            TaskType.CONTENT_CREATION: {
                'title': 'Content Creation - {content_type}',
                'description': 'Create high-quality content aligned with SEO and marketing strategy',
                'estimated_hours': 4.0,
                'deliverables': [
                    'Content pieces (blog posts, web copy, etc.)',
                    'SEO optimization',
                    'Content calendar updates'
                ],
                'assigned_to': 'content_manager'
            },
            
            TaskType.AD_CAMPAIGN_SETUP: {
                'title': 'Set up {platform} advertising campaigns',
                'description': 'Create and launch targeted advertising campaigns',
                'estimated_hours': 6.0,
                'deliverables': [
                    'Campaign structure and setup',
                    'Ad creative development',
                    'Targeting configuration',
                    'Tracking implementation'
                ],
                'assigned_to': 'ads_manager'
            },
            
            TaskType.SOCIAL_MEDIA_SETUP: {
                'title': 'Social Media Profile Optimization',
                'description': 'Optimize social media profiles and establish posting strategy',
                'estimated_hours': 3.0,
                'deliverables': [
                    'Profile optimization',
                    'Content calendar',
                    'Posting schedule setup'
                ],
                'assigned_to': 'social_media_manager'
            },
            
            TaskType.REPORTING: {
                'title': 'Monthly Performance Report',
                'description': 'Compile and analyze monthly performance data',
                'estimated_hours': 2.0,
                'deliverables': [
                    'Performance report',
                    'Insights and recommendations',
                    'Next month strategy'
                ],
                'assigned_to': 'account_manager'
            }
        }
    
    def onboard_new_client(self, lead_id: int, deal_data: Dict) -> Client:
        """Onboard a new client from a closed deal"""
        
        # Get lead data
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
        lead_row = cursor.fetchone()
        
        if not lead_row:
            conn.close()
            return None
        
        lead_columns = [desc[0] for desc in cursor.description]
        lead_data = dict(zip(lead_columns, lead_row))
        
        conn.close()
        
        # Create client record
        client = Client(
            lead_id=lead_id,
            client_id=str(uuid.uuid4())[:8],
            company_name=lead_data['company_name'],
            contact_name=lead_data['contact_name'],
            contact_email=lead_data['contact_email'],
            package=deal_data.get('package', 'growth'),
            monthly_value=deal_data.get('monthly_value', 5000),
            start_date=datetime.now(),
            status=ClientStatus.ONBOARDING
        )
        
        # Save client
        self.save_client(client)
        
        # Send welcome email
        self.send_onboarding_email(client, 'welcome')
        
        # Create initial onboarding tasks
        self.create_onboarding_tasks(client)
        
        return client
    
    def save_client(self, client: Client):
        """Save client to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO clients (
                lead_id, client_id, company_name, contact_name, contact_email,
                package, monthly_value, start_date, status, onboarding_completed,
                last_activity, satisfaction_score, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            client.lead_id, client.client_id, client.company_name,
            client.contact_name, client.contact_email, client.package,
            client.monthly_value, client.start_date.isoformat(),
            client.status.value, client.onboarding_completed,
            client.last_activity.isoformat(), client.satisfaction_score,
            client.notes
        ))
        
        conn.commit()
        conn.close()
    
    def send_onboarding_email(self, client: Client, template_name: str):
        """Send onboarding email to client"""
        template = self.onboarding_templates.get(template_name, '')
        
        # Personalize template
        personalized_content = template.format(
            contact_name=client.contact_name,
            company_name=client.company_name,
            package=client.package.title(),
            account_manager=self.team_assignments['account_manager'],
            completed_activities="• SEO audit completed\\n• Google Ads campaigns launched\\n• Social media profiles optimized",
            key_metrics="• Website traffic: +45%\\n• Lead generation: +60%\\n• Cost per lead: -30%",
            upcoming_focus="• Content marketing expansion\\n• Conversion rate optimization\\n• Advanced targeting refinement",
            time_slot_1="Tuesday, 2:00 PM EST",
            time_slot_2="Wednesday, 10:00 AM EST",
            time_slot_3="Thursday, 3:00 PM EST"
        )
        
        # In production, this would send actual emails
        print(f"[EMAIL SIMULATION] Sending {template_name} email to {client.contact_email}")
        print(f"Content preview: {personalized_content[:200]}...")
        
        # Log communication
        self.log_client_communication(
            client.client_id,
            'email',
            f"Onboarding - {template_name}",
            personalized_content
        )
    
    def create_onboarding_tasks(self, client: Client):
        """Create initial onboarding tasks for new client"""
        
        # Define onboarding task sequence based on package
        if client.package == 'starter':
            task_sequence = [
                (TaskType.SEO_AUDIT, 3),
                (TaskType.AD_CAMPAIGN_SETUP, 5),
                (TaskType.SOCIAL_MEDIA_SETUP, 7),
                (TaskType.REPORTING, 30)
            ]
        elif client.package == 'growth':
            task_sequence = [
                (TaskType.SEO_AUDIT, 2),
                (TaskType.AD_CAMPAIGN_SETUP, 3),
                (TaskType.SOCIAL_MEDIA_SETUP, 4),
                (TaskType.CONTENT_CREATION, 7),
                (TaskType.WEBSITE_OPTIMIZATION, 10),
                (TaskType.REPORTING, 30)
            ]
        else:  # enterprise
            task_sequence = [
                (TaskType.SEO_AUDIT, 1),
                (TaskType.AD_CAMPAIGN_SETUP, 2),
                (TaskType.SOCIAL_MEDIA_SETUP, 3),
                (TaskType.CONTENT_CREATION, 5),
                (TaskType.WEBSITE_OPTIMIZATION, 7),
                (TaskType.STRATEGY_REVIEW, 14),
                (TaskType.REPORTING, 30)
            ]
        
        # Create tasks
        for task_type, days_offset in task_sequence:
            self.create_service_task(
                client.client_id,
                task_type,
                due_date=client.start_date + timedelta(days=days_offset)
            )
    
    def create_service_task(self, client_id: str, task_type: TaskType, due_date: datetime, **kwargs) -> ServiceTask:
        """Create a service delivery task"""
        
        # Get client data
        client = self.get_client(client_id)
        if not client:
            return None
        
        # Get task template
        template = self.task_templates.get(task_type, {})
        
        # Create task
        task = ServiceTask(
            client_id=client_id,
            task_id=str(uuid.uuid4())[:8],
            task_type=task_type,
            title=template.get('title', '').format(
                company_name=client.company_name,
                content_type=kwargs.get('content_type', 'Blog Posts'),
                platform=kwargs.get('platform', 'Google Ads')
            ),
            description=template.get('description', ''),
            assigned_to=self.team_assignments.get(template.get('assigned_to', 'account_manager')),
            due_date=due_date,
            status=ServiceStatus.PENDING,
            estimated_hours=template.get('estimated_hours', 2.0),
            deliverables=template.get('deliverables', [])
        )
        
        # Save task
        self.save_service_task(task)
        
        return task
    
    def save_service_task(self, task: ServiceTask):
        """Save service task to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO service_tasks (
                client_id, task_id, task_type, title, description, assigned_to,
                due_date, status, priority, estimated_hours, actual_hours,
                deliverables, completion_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.client_id, task.task_id, task.task_type.value, task.title,
            task.description, task.assigned_to, task.due_date.isoformat(),
            task.status.value, task.priority, task.estimated_hours,
            task.actual_hours, json.dumps(task.deliverables),
            task.completion_date.isoformat() if task.completion_date else None,
            task.notes
        ))
        
        conn.commit()
        conn.close()
    
    def get_client(self, client_id: str) -> Optional[Client]:
        """Get client by ID"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM clients WHERE client_id = ?', (client_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        
        conn.close()
        
        # Convert to Client object
        return Client(
            lead_id=data['lead_id'],
            client_id=data['client_id'],
            company_name=data['company_name'],
            contact_name=data['contact_name'],
            contact_email=data['contact_email'],
            package=data['package'],
            monthly_value=data['monthly_value'],
            start_date=datetime.fromisoformat(data['start_date']),
            status=ClientStatus(data['status']),
            onboarding_completed=bool(data['onboarding_completed']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            satisfaction_score=data['satisfaction_score'],
            notes=data['notes']
        )
    
    def generate_monthly_report(self, client_id: str) -> ClientReport:
        """Generate monthly performance report for client"""
        
        client = self.get_client(client_id)
        if not client:
            return None
        
        # Simulate performance metrics (in production, this would pull from actual analytics)
        metrics = {
            'website_traffic': {
                'sessions': random.randint(5000, 15000),
                'users': random.randint(3000, 10000),
                'growth': random.uniform(0.15, 0.45)
            },
            'lead_generation': {
                'total_leads': random.randint(50, 200),
                'qualified_leads': random.randint(20, 80),
                'conversion_rate': random.uniform(0.02, 0.08)
            },
            'advertising': {
                'impressions': random.randint(100000, 500000),
                'clicks': random.randint(2000, 10000),
                'ctr': random.uniform(0.02, 0.06),
                'cost_per_click': random.uniform(1.50, 4.00)
            },
            'social_media': {
                'followers_growth': random.randint(50, 300),
                'engagement_rate': random.uniform(0.03, 0.08),
                'reach': random.randint(10000, 50000)
            }
        }
        
        # Generate insights using AI
        insights = self.generate_performance_insights(client, metrics)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(client, metrics)
        
        # Create report
        report = ClientReport(
            client_id=client_id,
            report_id=str(uuid.uuid4())[:8],
            report_period=datetime.now().strftime('%B %Y'),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            generated_date=datetime.now()
        )
        
        # Save report
        self.save_client_report(report)
        
        return report
    
    def generate_performance_insights(self, client: Client, metrics: Dict) -> List[str]:
        """Generate AI-powered performance insights"""
        
        insights_prompt = f"""
        Analyze these digital marketing performance metrics for {client.company_name} and provide 3-5 key insights:
        
        Website Traffic:
        - Sessions: {metrics['website_traffic']['sessions']:,}
        - Users: {metrics['website_traffic']['users']:,}
        - Growth: {metrics['website_traffic']['growth']:.1%}
        
        Lead Generation:
        - Total Leads: {metrics['lead_generation']['total_leads']}
        - Qualified Leads: {metrics['lead_generation']['qualified_leads']}
        - Conversion Rate: {metrics['lead_generation']['conversion_rate']:.2%}
        
        Advertising:
        - Impressions: {metrics['advertising']['impressions']:,}
        - Clicks: {metrics['advertising']['clicks']:,}
        - CTR: {metrics['advertising']['ctr']:.2%}
        - CPC: ${metrics['advertising']['cost_per_click']:.2f}
        
        Social Media:
        - Followers Growth: {metrics['social_media']['followers_growth']}
        - Engagement Rate: {metrics['social_media']['engagement_rate']:.2%}
        - Reach: {metrics['social_media']['reach']:,}
        
        Package: {client.package}
        
        Provide actionable insights about performance trends, opportunities, and areas for improvement.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a digital marketing analyst. Provide clear, actionable insights based on performance data."},
                    {"role": "user", "content": insights_prompt}
                ],
                temperature=0.7
            )
            
            insights_text = response.choices[0].message.content
            # Split into individual insights
            insights = [insight.strip() for insight in insights_text.split('\n') if insight.strip() and not insight.strip().startswith('#')]
            return insights[:5]  # Limit to 5 insights
            
        except Exception as e:
            print(f"Error generating insights: {str(e)}")
            return [
                f"Website traffic grew by {metrics['website_traffic']['growth']:.1%} this month",
                f"Lead conversion rate of {metrics['lead_generation']['conversion_rate']:.2%} is performing well",
                f"Advertising CTR of {metrics['advertising']['ctr']:.2%} shows good ad relevance",
                "Social media engagement is building brand awareness effectively"
            ]
    
    def generate_recommendations(self, client: Client, metrics: Dict) -> List[str]:
        """Generate strategic recommendations"""
        
        recommendations = []
        
        # Traffic-based recommendations
        if metrics['website_traffic']['growth'] < 0.2:
            recommendations.append("Increase content marketing efforts to drive more organic traffic")
        
        # Conversion-based recommendations
        if metrics['lead_generation']['conversion_rate'] < 0.03:
            recommendations.append("Optimize landing pages and forms to improve conversion rates")
        
        # Advertising recommendations
        if metrics['advertising']['cost_per_click'] > 3.0:
            recommendations.append("Refine ad targeting to reduce cost per click and improve ROI")
        
        # Social media recommendations
        if metrics['social_media']['engagement_rate'] < 0.05:
            recommendations.append("Develop more engaging social media content to increase audience interaction")
        
        # Package-specific recommendations
        if client.package == 'starter':
            recommendations.append("Consider upgrading to Growth package for expanded content marketing")
        elif client.package == 'growth':
            recommendations.append("Implement advanced automation to scale current success")
        
        return recommendations[:4]  # Limit to 4 recommendations
    
    def save_client_report(self, report: ClientReport):
        """Save client report to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO client_reports (
                client_id, report_id, report_period, metrics, insights,
                recommendations, generated_date, sent_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report.client_id, report.report_id, report.report_period,
            json.dumps(report.metrics), json.dumps(report.insights),
            json.dumps(report.recommendations), report.generated_date.isoformat(),
            report.sent_date.isoformat() if report.sent_date else None
        ))
        
        conn.commit()
        conn.close()
    
    def log_client_communication(self, client_id: str, comm_type: str, subject: str, content: str):
        """Log client communication"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO client_communications (
                client_id, communication_type, subject, content, sent_date,
                response_received, response_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            client_id, comm_type, subject, content, datetime.now().isoformat(),
            False, None
        ))
        
        conn.commit()
        conn.close()
    
    def get_active_clients(self) -> List[Client]:
        """Get all active clients"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM clients 
            WHERE status IN ('onboarding', 'active')
            ORDER BY start_date DESC
        ''')
        
        clients = []
        for row in cursor.fetchall():
            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row))
            
            client = Client(
                lead_id=data['lead_id'],
                client_id=data['client_id'],
                company_name=data['company_name'],
                contact_name=data['contact_name'],
                contact_email=data['contact_email'],
                package=data['package'],
                monthly_value=data['monthly_value'],
                start_date=datetime.fromisoformat(data['start_date']),
                status=ClientStatus(data['status']),
                onboarding_completed=bool(data['onboarding_completed']),
                last_activity=datetime.fromisoformat(data['last_activity']),
                satisfaction_score=data['satisfaction_score'],
                notes=data['notes']
            )
            clients.append(client)
        
        conn.close()
        return clients
    
    def get_client_metrics_summary(self) -> Dict[str, any]:
        """Get summary metrics for all clients"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Total clients and revenue
        cursor.execute('''
            SELECT 
                COUNT(*) as total_clients,
                SUM(monthly_value) as monthly_revenue,
                AVG(satisfaction_score) as avg_satisfaction
            FROM clients 
            WHERE status IN ('onboarding', 'active')
        ''')
        
        summary = cursor.fetchone()
        
        # Client distribution by package
        cursor.execute('''
            SELECT package, COUNT(*) as count
            FROM clients 
            WHERE status IN ('onboarding', 'active')
            GROUP BY package
        ''')
        
        package_distribution = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_clients': summary[0] or 0,
            'monthly_revenue': summary[1] or 0,
            'average_satisfaction': summary[2] or 0.0,
            'package_distribution': package_distribution
        }


def main():
    """Main function to demonstrate the client management agent"""
    agent = ClientManagementAgent()
    
    # Simulate onboarding a new client
    print("Simulating client onboarding...")
    
    # Mock deal data
    deal_data = {
        'package': 'growth',
        'monthly_value': 5000
    }
    
    # Onboard client (using lead ID 1)
    client = agent.onboard_new_client(1, deal_data)
    
    if client:
        print(f"Client onboarded: {client.company_name} (ID: {client.client_id})")
        print(f"Package: {client.package}")
        print(f"Monthly Value: ${client.monthly_value:,}")
        
        # Generate monthly report
        print(f"\nGenerating monthly report for {client.company_name}...")
        report = agent.generate_monthly_report(client.client_id)
        
        if report:
            print(f"Report generated for {report.report_period}")
            print(f"Key insights: {len(report.insights)} insights")
            print(f"Recommendations: {len(report.recommendations)} recommendations")
    
    # Get client metrics
    metrics = agent.get_client_metrics_summary()
    print(f"\nClient Portfolio Summary:")
    print(f"- Total Active Clients: {metrics['total_clients']}")
    print(f"- Monthly Recurring Revenue: ${metrics['monthly_revenue']:,}")
    print(f"- Average Satisfaction: {metrics['average_satisfaction']:.1f}/5.0")
    print(f"- Package Distribution: {metrics['package_distribution']}")


if __name__ == "__main__":
    main()

