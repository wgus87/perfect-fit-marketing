"""
Outreach Automation Agent - Multi-channel automated outreach system
This agent handles email, social media, and phone outreach with personalization
"""

import sqlite3
import json
import openai
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import re
import random


class OutreachChannel(Enum):
    """Outreach channels"""
    EMAIL = "email"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    PHONE = "phone"
    FACEBOOK = "facebook"


class OutreachStatus(Enum):
    """Outreach status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"


@dataclass
class OutreachTemplate:
    """Template for outreach messages"""
    name: str
    channel: OutreachChannel
    subject_template: str
    message_template: str
    follow_up_templates: List[str] = None
    personalization_fields: List[str] = None
    
    def __post_init__(self):
        if self.follow_up_templates is None:
            self.follow_up_templates = []
        if self.personalization_fields is None:
            self.personalization_fields = []


@dataclass
class OutreachMessage:
    """Individual outreach message"""
    lead_id: int
    channel: OutreachChannel
    template_name: str
    subject: str
    message: str
    recipient_email: str = ""
    recipient_name: str = ""
    status: OutreachStatus = OutreachStatus.PENDING
    sent_date: Optional[datetime] = None
    response_date: Optional[datetime] = None
    response_content: str = ""
    tracking_id: str = ""
    
    def __post_init__(self):
        if not self.tracking_id:
            self.tracking_id = f"msg_{self.lead_id}_{int(time.time())}"


class OutreachAutomationAgent:
    """
    AI-powered outreach automation agent for multi-channel campaigns
    """
    
    def __init__(self, database_path: str = "leads.db"):
        self.database_path = database_path
        self.setup_database()
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI()
        
        # Email configuration (would be set from environment variables in production)
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': 'your-agency@gmail.com',  # Replace with actual email
            'password': 'your-app-password',   # Replace with actual app password
            'from_name': 'AI Marketing Agency'
        }
        
        # Initialize outreach templates
        self.templates = self.initialize_templates()
        
        # Outreach timing configuration
        self.timing_config = {
            'initial_delay_hours': 0,
            'follow_up_delays_days': [3, 7, 14],
            'max_follow_ups': 3,
            'daily_send_limit': 50,
            'hourly_send_limit': 10
        }
    
    def setup_database(self):
        """Initialize database tables for outreach data"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outreach_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                channel TEXT,
                template_name TEXT,
                subject TEXT,
                message TEXT,
                recipient_email TEXT,
                recipient_name TEXT,
                status TEXT,
                sent_date TEXT,
                response_date TEXT,
                response_content TEXT,
                tracking_id TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outreach_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                target_criteria TEXT,
                channels TEXT,
                templates TEXT,
                start_date TEXT,
                end_date TEXT,
                status TEXT,
                created_date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outreach_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER,
                channel TEXT,
                total_sent INTEGER,
                total_delivered INTEGER,
                total_opened INTEGER,
                total_clicked INTEGER,
                total_replied INTEGER,
                total_bounced INTEGER,
                date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def initialize_templates(self) -> Dict[str, OutreachTemplate]:
        """Initialize outreach message templates"""
        templates = {}
        
        # Email templates
        templates['initial_email'] = OutreachTemplate(
            name="initial_email",
            channel=OutreachChannel.EMAIL,
            subject_template="Quick question about {company_name}'s marketing goals",
            message_template="""Hi {contact_name},

I came across {company_name} and was impressed by {company_specific_detail}. 

I specialize in helping {industry} companies like yours {specific_benefit}. I noticed that {pain_point_observation}, which is something we've helped similar companies overcome.

Would you be open to a brief 15-minute conversation about your current marketing challenges and goals? I'd love to share some insights that could be valuable for {company_name}.

Best regards,
{sender_name}
{sender_title}
{agency_name}

P.S. {personalized_ps}""",
            personalization_fields=['company_name', 'contact_name', 'industry', 'company_specific_detail', 'specific_benefit', 'pain_point_observation', 'personalized_ps']
        )
        
        templates['follow_up_1'] = OutreachTemplate(
            name="follow_up_1",
            channel=OutreachChannel.EMAIL,
            subject_template="Re: {company_name}'s marketing goals - quick follow-up",
            message_template="""Hi {contact_name},

I wanted to follow up on my previous email about {company_name}'s marketing strategy.

I understand you're probably busy, but I thought you might be interested in a case study of how we helped {similar_company} in the {industry} industry increase their {metric} by {percentage}% in just {timeframe}.

The approach we used could be particularly relevant for {company_name} given {specific_reason}.

Would you have 10 minutes this week for a quick call? I promise to keep it brief and valuable.

Best regards,
{sender_name}""",
            personalization_fields=['company_name', 'contact_name', 'similar_company', 'industry', 'metric', 'percentage', 'timeframe', 'specific_reason']
        )
        
        templates['follow_up_2'] = OutreachTemplate(
            name="follow_up_2",
            channel=OutreachChannel.EMAIL,
            subject_template="Last attempt - {value_proposition} for {company_name}",
            message_template="""Hi {contact_name},

This will be my last email, as I don't want to be a bother.

I genuinely believe {company_name} could benefit from our {service_type} services, especially given {specific_opportunity}.

If you're not interested, no worries at all. But if you'd like to explore how we could help {company_name} {specific_goal}, I'm here.

Just reply with "interested" and I'll send over some relevant case studies.

Best of luck with your marketing efforts!

{sender_name}""",
            personalization_fields=['company_name', 'contact_name', 'value_proposition', 'service_type', 'specific_opportunity', 'specific_goal']
        )
        
        # LinkedIn templates
        templates['linkedin_connection'] = OutreachTemplate(
            name="linkedin_connection",
            channel=OutreachChannel.LINKEDIN,
            subject_template="",
            message_template="""Hi {contact_name}, I'd love to connect! I help {industry} companies with digital marketing strategy and noticed some interesting opportunities for {company_name}. Would love to share some insights if you're open to it.""",
            personalization_fields=['contact_name', 'industry', 'company_name']
        )
        
        templates['linkedin_message'] = OutreachTemplate(
            name="linkedin_message",
            channel=OutreachChannel.LINKEDIN,
            subject_template="",
            message_template="""Hi {contact_name},

Thanks for connecting! I've been working with {industry} companies to help them {specific_benefit}.

I took a quick look at {company_name} and noticed {specific_observation}. This is actually something we've helped other companies in your space address successfully.

Would you be open to a brief conversation about your current marketing priorities? I'd be happy to share some insights that could be valuable.

Best,
{sender_name}""",
            personalization_fields=['contact_name', 'industry', 'specific_benefit', 'company_name', 'specific_observation']
        )
        
        return templates
    
    def personalize_message(self, template: OutreachTemplate, lead_data: Dict, intelligence_data: Dict = None) -> Tuple[str, str]:
        """Personalize message template with lead-specific data"""
        
        # Prepare personalization data
        personalization_data = {
            'company_name': lead_data.get('company_name', 'your company'),
            'contact_name': lead_data.get('contact_name', 'there'),
            'industry': lead_data.get('industry', 'business'),
            'sender_name': 'Alex Johnson',
            'sender_title': 'Digital Marketing Strategist',
            'agency_name': 'AI Marketing Solutions'
        }
        
        # Add intelligence-based personalization
        if intelligence_data:
            personalization_data.update({
                'company_specific_detail': self.generate_company_specific_detail(intelligence_data),
                'specific_benefit': self.generate_specific_benefit(intelligence_data),
                'pain_point_observation': self.generate_pain_point_observation(intelligence_data),
                'personalized_ps': self.generate_personalized_ps(intelligence_data),
                'similar_company': self.get_similar_company(intelligence_data),
                'metric': self.get_relevant_metric(intelligence_data),
                'percentage': str(random.randint(25, 85)),
                'timeframe': random.choice(['3 months', '6 months', '4 months']),
                'specific_reason': self.generate_specific_reason(intelligence_data),
                'value_proposition': self.generate_value_proposition(intelligence_data),
                'service_type': self.get_relevant_service_type(intelligence_data),
                'specific_opportunity': self.generate_specific_opportunity(intelligence_data),
                'specific_goal': self.generate_specific_goal(intelligence_data),
                'specific_observation': self.generate_specific_observation(intelligence_data)
            })
        else:
            # Default personalization when no intelligence data
            personalization_data.update({
                'company_specific_detail': 'your innovative approach to business',
                'specific_benefit': 'increase their online presence and generate more qualified leads',
                'pain_point_observation': 'there might be opportunities to optimize your digital marketing strategy',
                'personalized_ps': 'I\'d love to share some industry insights that could be valuable.',
                'similar_company': 'a similar company',
                'metric': 'lead generation',
                'percentage': '45',
                'timeframe': '4 months',
                'specific_reason': 'your industry focus',
                'value_proposition': 'proven digital marketing strategies',
                'service_type': 'digital marketing',
                'specific_opportunity': 'your growth potential',
                'specific_goal': 'achieve your marketing objectives',
                'specific_observation': 'some interesting growth opportunities'
            })
        
        # Personalize subject and message
        subject = template.subject_template.format(**personalization_data)
        message = template.message_template.format(**personalization_data)
        
        return subject, message
    
    def generate_company_specific_detail(self, intelligence_data: Dict) -> str:
        """Generate company-specific detail for personalization"""
        details = [
            "your strong online presence",
            "your innovative approach to the industry",
            "your company's growth trajectory",
            "your focus on customer experience",
            "your market positioning"
        ]
        
        # Use intelligence data to make it more specific
        if intelligence_data.get('technologies_used'):
            return f"your use of modern technologies like {intelligence_data['technologies_used'][0]}"
        
        return random.choice(details)
    
    def generate_specific_benefit(self, intelligence_data: Dict) -> str:
        """Generate specific benefit based on intelligence"""
        industry = intelligence_data.get('industry', '').lower()
        
        industry_benefits = {
            'technology': 'reach technical decision-makers and showcase their innovations',
            'e-commerce': 'increase online sales and improve conversion rates',
            'healthcare': 'build trust and generate qualified patient leads',
            'finance': 'establish credibility and attract high-value clients',
            'professional_services': 'build thought leadership and generate referrals'
        }
        
        return industry_benefits.get(industry, 'grow their business and reach their target audience')
    
    def generate_pain_point_observation(self, intelligence_data: Dict) -> str:
        """Generate pain point observation based on intelligence"""
        pain_points = intelligence_data.get('pain_points', [])
        
        if 'low_traffic' in pain_points:
            return "your website could benefit from increased organic traffic"
        elif 'poor_conversion' in pain_points:
            return "there might be opportunities to improve your conversion rates"
        elif 'brand_awareness' in pain_points:
            return "you could expand your brand visibility in the market"
        else:
            return "there are opportunities to optimize your digital marketing strategy"
    
    def generate_personalized_ps(self, intelligence_data: Dict) -> str:
        """Generate personalized P.S. based on intelligence"""
        ps_options = [
            "I recently helped a similar company increase their ROI by 60%.",
            "I have some insights specific to your industry that might interest you.",
            "I'd love to share a case study that's directly relevant to your situation.",
            "I have some ideas that could help you stand out from competitors."
        ]
        
        return random.choice(ps_options)
    
    def get_similar_company(self, intelligence_data: Dict) -> str:
        """Get similar company name for case studies"""
        industry = intelligence_data.get('industry', '').lower()
        
        similar_companies = {
            'technology': 'TechFlow Solutions',
            'e-commerce': 'Digital Commerce Hub',
            'healthcare': 'MedCare Partners',
            'finance': 'Financial Growth Group',
            'professional_services': 'Strategic Consulting Pro'
        }
        
        return similar_companies.get(industry, 'a similar company')
    
    def get_relevant_metric(self, intelligence_data: Dict) -> str:
        """Get relevant metric based on intelligence"""
        pain_points = intelligence_data.get('pain_points', [])
        
        if 'low_traffic' in pain_points:
            return 'website traffic'
        elif 'poor_conversion' in pain_points:
            return 'conversion rate'
        elif 'brand_awareness' in pain_points:
            return 'brand visibility'
        else:
            return 'lead generation'
    
    def generate_specific_reason(self, intelligence_data: Dict) -> str:
        """Generate specific reason for relevance"""
        return f"your focus on {intelligence_data.get('industry', 'business growth')}"
    
    def generate_value_proposition(self, intelligence_data: Dict) -> str:
        """Generate value proposition based on intelligence"""
        industry = intelligence_data.get('industry', '').lower()
        
        value_props = {
            'technology': 'cutting-edge digital marketing for tech companies',
            'e-commerce': 'e-commerce optimization and growth strategies',
            'healthcare': 'compliant healthcare marketing solutions',
            'finance': 'trust-building financial marketing strategies'
        }
        
        return value_props.get(industry, 'proven digital marketing strategies')
    
    def get_relevant_service_type(self, intelligence_data: Dict) -> str:
        """Get relevant service type based on intelligence"""
        pain_points = intelligence_data.get('pain_points', [])
        
        if 'low_traffic' in pain_points:
            return 'SEO and content marketing'
        elif 'poor_conversion' in pain_points:
            return 'conversion optimization'
        elif 'brand_awareness' in pain_points:
            return 'brand marketing'
        else:
            return 'digital marketing'
    
    def generate_specific_opportunity(self, intelligence_data: Dict) -> str:
        """Generate specific opportunity based on intelligence"""
        growth_indicators = intelligence_data.get('growth_indicators', [])
        
        if 'high_digital_maturity' in growth_indicators:
            return "your advanced digital infrastructure"
        elif 'strong_social_presence' in growth_indicators:
            return "your existing social media engagement"
        else:
            return "your market position"
    
    def generate_specific_goal(self, intelligence_data: Dict) -> str:
        """Generate specific goal based on intelligence"""
        return f"dominate the {intelligence_data.get('industry', 'market')} space"
    
    def generate_specific_observation(self, intelligence_data: Dict) -> str:
        """Generate specific observation for LinkedIn"""
        return f"some interesting opportunities in the {intelligence_data.get('industry', 'business')} space"
    
    def create_outreach_message(self, lead_id: int, template_name: str, channel: OutreachChannel) -> Optional[OutreachMessage]:
        """Create personalized outreach message for a lead"""
        
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
        
        # Get intelligence data
        cursor.execute('''
            SELECT * FROM company_intelligence 
            WHERE company_name = ? AND website = ?
        ''', (lead_data['company_name'], lead_data['website']))
        
        intelligence_row = cursor.fetchone()
        intelligence_data = None
        
        if intelligence_row:
            intelligence_columns = [desc[0] for desc in cursor.description]
            intelligence_data = dict(zip(intelligence_columns, intelligence_row))
            
            # Parse JSON fields
            if intelligence_data.get('pain_points'):
                intelligence_data['pain_points'] = json.loads(intelligence_data['pain_points'])
            if intelligence_data.get('growth_indicators'):
                intelligence_data['growth_indicators'] = json.loads(intelligence_data['growth_indicators'])
        
        conn.close()
        
        # Get template
        template = self.templates.get(template_name)
        if not template:
            return None
        
        # Personalize message
        subject, message = self.personalize_message(template, lead_data, intelligence_data)
        
        # Create outreach message
        outreach_message = OutreachMessage(
            lead_id=lead_id,
            channel=channel,
            template_name=template_name,
            subject=subject,
            message=message,
            recipient_email=lead_data.get('contact_email', ''),
            recipient_name=lead_data.get('contact_name', '')
        )
        
        return outreach_message
    
    def send_email(self, message: OutreachMessage) -> bool:
        """Send email message (simulation for demo)"""
        try:
            # In production, this would use actual SMTP
            print(f"[EMAIL SIMULATION] Sending to {message.recipient_email}")
            print(f"Subject: {message.subject}")
            print(f"Message: {message.message[:100]}...")
            
            # Simulate sending
            time.sleep(1)
            
            # Update message status
            message.status = OutreachStatus.SENT
            message.sent_date = datetime.now()
            
            # Save to database
            self.save_outreach_message(message)
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            message.status = OutreachStatus.FAILED
            self.save_outreach_message(message)
            return False
    
    def send_linkedin_message(self, message: OutreachMessage) -> bool:
        """Send LinkedIn message (simulation for demo)"""
        try:
            print(f"[LINKEDIN SIMULATION] Sending to {message.recipient_name}")
            print(f"Message: {message.message[:100]}...")
            
            # Simulate sending
            time.sleep(2)
            
            message.status = OutreachStatus.SENT
            message.sent_date = datetime.now()
            self.save_outreach_message(message)
            
            return True
            
        except Exception as e:
            print(f"Error sending LinkedIn message: {str(e)}")
            message.status = OutreachStatus.FAILED
            self.save_outreach_message(message)
            return False
    
    def save_outreach_message(self, message: OutreachMessage):
        """Save outreach message to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO outreach_messages (
                lead_id, channel, template_name, subject, message,
                recipient_email, recipient_name, status, sent_date,
                response_date, response_content, tracking_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            message.lead_id, message.channel.value, message.template_name,
            message.subject, message.message, message.recipient_email,
            message.recipient_name, message.status.value,
            message.sent_date.isoformat() if message.sent_date else None,
            message.response_date.isoformat() if message.response_date else None,
            message.response_content, message.tracking_id
        ))
        
        conn.commit()
        conn.close()
    
    def execute_outreach_campaign(self, qualified_leads: List[Dict]) -> Dict[str, int]:
        """Execute outreach campaign for qualified leads"""
        results = {
            'total_leads': len(qualified_leads),
            'emails_sent': 0,
            'linkedin_sent': 0,
            'failed': 0
        }
        
        for lead in qualified_leads:
            lead_id = lead['id']
            
            # Send initial email
            email_message = self.create_outreach_message(lead_id, 'initial_email', OutreachChannel.EMAIL)
            if email_message and email_message.recipient_email:
                if self.send_email(email_message):
                    results['emails_sent'] += 1
                else:
                    results['failed'] += 1
            
            # Send LinkedIn connection request if we have contact name
            if lead.get('contact_name'):
                linkedin_message = self.create_outreach_message(lead_id, 'linkedin_connection', OutreachChannel.LINKEDIN)
                if linkedin_message:
                    if self.send_linkedin_message(linkedin_message):
                        results['linkedin_sent'] += 1
                    else:
                        results['failed'] += 1
            
            # Rate limiting
            time.sleep(2)
        
        return results
    
    def schedule_follow_ups(self, lead_id: int):
        """Schedule follow-up messages for a lead"""
        follow_up_templates = ['follow_up_1', 'follow_up_2']
        
        for i, template_name in enumerate(follow_up_templates):
            # Calculate send date
            delay_days = self.timing_config['follow_up_delays_days'][i]
            send_date = datetime.now() + timedelta(days=delay_days)
            
            # Create follow-up message
            message = self.create_outreach_message(lead_id, template_name, OutreachChannel.EMAIL)
            if message:
                # In production, this would be scheduled in a task queue
                print(f"Scheduled {template_name} for lead {lead_id} on {send_date.strftime('%Y-%m-%d')}")
    
    def get_outreach_analytics(self) -> Dict[str, int]:
        """Get outreach performance analytics"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                channel,
                status,
                COUNT(*) as count
            FROM outreach_messages
            GROUP BY channel, status
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        analytics = {}
        for channel, status, count in results:
            if channel not in analytics:
                analytics[channel] = {}
            analytics[channel][status] = count
        
        return analytics
    
    def generate_outreach_report(self) -> str:
        """Generate outreach performance report"""
        analytics = self.get_outreach_analytics()
        
        report = f"""
OUTREACH PERFORMANCE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CHANNEL PERFORMANCE:
"""
        
        for channel, stats in analytics.items():
            report += f"\n{channel.upper()}:\n"
            for status, count in stats.items():
                report += f"  - {status.title()}: {count}\n"
        
        return report


def main():
    """Main function to demonstrate the outreach automation agent"""
    agent = OutreachAutomationAgent()
    
    # Get qualified leads
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT l.* FROM leads l
        JOIN lead_qualifications lq ON l.id = lq.lead_id
        WHERE lq.status IN ('qualified', 'highly_qualified')
        LIMIT 3
    ''')
    
    columns = [desc[0] for desc in cursor.description]
    qualified_leads = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    if not qualified_leads:
        print("No qualified leads found. Please run qualification first.")
        return
    
    # Execute outreach campaign
    print(f"Starting outreach campaign for {len(qualified_leads)} qualified leads...")
    results = agent.execute_outreach_campaign(qualified_leads)
    
    print(f"Campaign Results:")
    print(f"- Total Leads: {results['total_leads']}")
    print(f"- Emails Sent: {results['emails_sent']}")
    print(f"- LinkedIn Messages Sent: {results['linkedin_sent']}")
    print(f"- Failed: {results['failed']}")
    
    # Schedule follow-ups
    for lead in qualified_leads:
        agent.schedule_follow_ups(lead['id'])
    
    # Generate report
    report = agent.generate_outreach_report()
    print(report)


if __name__ == "__main__":
    main()

