"""
Sales Automation Agent - Automated sales process and deal closing
This agent handles proposal generation, pricing, contracts, and deal closing
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


class DealStage(Enum):
    """Sales deal stages"""
    INITIAL_CONTACT = "initial_contact"
    DISCOVERY = "discovery"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    CONTRACT_SENT = "contract_sent"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class ServicePackage(Enum):
    """Service package types"""
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


@dataclass
class ServiceOffering:
    """Service offering configuration"""
    name: str
    package: ServicePackage
    monthly_price: int
    setup_fee: int
    services_included: List[str]
    deliverables: List[str]
    timeline: str
    ideal_for: List[str]
    
    def __post_init__(self):
        if not self.services_included:
            self.services_included = []
        if not self.deliverables:
            self.deliverables = []
        if not self.ideal_for:
            self.ideal_for = []


@dataclass
class SalesProposal:
    """Sales proposal data structure"""
    lead_id: int
    proposal_id: str
    package: ServicePackage
    monthly_price: int
    setup_fee: int
    total_first_month: int
    services_included: List[str]
    deliverables: List[str]
    timeline: str
    custom_notes: str = ""
    discount_percentage: float = 0.0
    proposal_date: datetime = None
    expiry_date: datetime = None
    status: str = "draft"
    
    def __post_init__(self):
        if self.proposal_date is None:
            self.proposal_date = datetime.now()
        if self.expiry_date is None:
            self.expiry_date = self.proposal_date + timedelta(days=14)
        if not self.proposal_id:
            self.proposal_id = str(uuid.uuid4())[:8]


@dataclass
class SalesDeal:
    """Sales deal tracking"""
    lead_id: int
    deal_id: str
    stage: DealStage
    proposal_id: Optional[str] = None
    value: int = 0
    probability: float = 0.0
    expected_close_date: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    notes: str = ""
    
    def __post_init__(self):
        if not self.deal_id:
            self.deal_id = str(uuid.uuid4())[:8]
        if self.last_activity is None:
            self.last_activity = datetime.now()


class SalesAutomationAgent:
    """
    AI-powered sales automation agent for deal closing
    """
    
    def __init__(self, database_path: str = "leads.db"):
        self.database_path = database_path
        self.setup_database()
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI()
        
        # Service packages configuration
        self.service_packages = self.initialize_service_packages()
        
        # Pricing rules
        self.pricing_rules = {
            'volume_discount': {
                'threshold': 10000,  # Monthly spend threshold
                'discount': 0.15     # 15% discount
            },
            'annual_discount': 0.20,  # 20% discount for annual payment
            'startup_discount': 0.25, # 25% discount for startups
            'enterprise_markup': 0.30 # 30% markup for enterprise
        }
        
        # Contract templates
        self.contract_templates = {
            'standard': 'standard_service_agreement.pdf',
            'enterprise': 'enterprise_service_agreement.pdf',
            'custom': 'custom_service_agreement.pdf'
        }
    
    def setup_database(self):
        """Initialize database tables for sales data"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                proposal_id TEXT UNIQUE,
                package TEXT,
                monthly_price INTEGER,
                setup_fee INTEGER,
                total_first_month INTEGER,
                services_included TEXT,
                deliverables TEXT,
                timeline TEXT,
                custom_notes TEXT,
                discount_percentage REAL,
                proposal_date TEXT,
                expiry_date TEXT,
                status TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                deal_id TEXT UNIQUE,
                stage TEXT,
                proposal_id TEXT,
                value INTEGER,
                probability REAL,
                expected_close_date TEXT,
                last_activity TEXT,
                notes TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id TEXT,
                activity_type TEXT,
                description TEXT,
                activity_date TEXT,
                outcome TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def initialize_service_packages(self) -> Dict[ServicePackage, ServiceOffering]:
        """Initialize service package configurations"""
        packages = {}
        
        packages[ServicePackage.STARTER] = ServiceOffering(
            name="Digital Marketing Starter",
            package=ServicePackage.STARTER,
            monthly_price=2500,
            setup_fee=500,
            services_included=[
                "SEO optimization",
                "Google Ads management",
                "Social media setup",
                "Monthly reporting",
                "Email support"
            ],
            deliverables=[
                "SEO audit and optimization",
                "Google Ads campaign setup",
                "Social media profiles optimization",
                "Monthly performance report"
            ],
            timeline="2-4 weeks setup, ongoing monthly management",
            ideal_for=["small businesses", "startups", "local companies"]
        )
        
        packages[ServicePackage.GROWTH] = ServiceOffering(
            name="Digital Marketing Growth",
            package=ServicePackage.GROWTH,
            monthly_price=5000,
            setup_fee=1000,
            services_included=[
                "Comprehensive SEO",
                "Google & Facebook Ads",
                "Content marketing",
                "Social media management",
                "Email marketing automation",
                "Conversion optimization",
                "Weekly reporting",
                "Phone & email support"
            ],
            deliverables=[
                "Complete SEO strategy and implementation",
                "Multi-platform ad campaigns",
                "Content calendar and creation",
                "Marketing automation setup",
                "Weekly performance reports"
            ],
            timeline="3-6 weeks setup, ongoing monthly management",
            ideal_for=["growing businesses", "e-commerce", "professional services"]
        )
        
        packages[ServicePackage.ENTERPRISE] = ServiceOffering(
            name="Enterprise Digital Marketing",
            package=ServicePackage.ENTERPRISE,
            monthly_price=10000,
            setup_fee=2500,
            services_included=[
                "Advanced SEO & technical optimization",
                "Multi-platform advertising",
                "Content marketing & PR",
                "Marketing automation",
                "CRM integration",
                "Advanced analytics & attribution",
                "Dedicated account manager",
                "Priority support"
            ],
            deliverables=[
                "Enterprise SEO strategy",
                "Omnichannel advertising campaigns",
                "Content marketing program",
                "Marketing technology stack setup",
                "Custom analytics dashboard"
            ],
            timeline="4-8 weeks setup, ongoing monthly management",
            ideal_for=["large companies", "enterprises", "high-growth businesses"]
        )
        
        return packages
    
    def analyze_lead_for_package_recommendation(self, lead_data: Dict, qualification_data: Dict) -> ServicePackage:
        """Analyze lead to recommend appropriate service package"""
        
        # Extract budget information
        budget_range = qualification_data.get('budget_range', '')
        budget_amount = self.extract_budget_amount(budget_range)
        
        # Extract company size
        employee_count = lead_data.get('employee_count', 0)
        
        # Extract industry
        industry = lead_data.get('industry', '').lower()
        
        # Package recommendation logic
        if budget_amount and budget_amount >= 8000:
            return ServicePackage.ENTERPRISE
        elif budget_amount and budget_amount >= 4000:
            return ServicePackage.GROWTH
        elif employee_count and employee_count > 100:
            return ServicePackage.ENTERPRISE
        elif employee_count and employee_count > 25:
            return ServicePackage.GROWTH
        elif industry in ['enterprise', 'finance', 'healthcare']:
            return ServicePackage.ENTERPRISE
        else:
            return ServicePackage.STARTER
    
    def extract_budget_amount(self, budget_range: str) -> Optional[int]:
        """Extract numeric budget amount from budget range string"""
        if not budget_range:
            return None
        
        import re
        # Extract numbers from budget string
        numbers = re.findall(r'\\d+(?:,\\d{3})*', budget_range.replace('$', '').replace(',', ''))
        if numbers:
            amount = int(numbers[0])
            
            # Convert yearly to monthly if needed
            if '/year' in budget_range or 'yearly' in budget_range:
                amount = amount // 12
            
            return amount
        
        return None
    
    def calculate_custom_pricing(self, base_package: ServicePackage, lead_data: Dict, qualification_data: Dict) -> Tuple[int, int, float]:
        """Calculate custom pricing based on lead characteristics"""
        
        base_offering = self.service_packages[base_package]
        monthly_price = base_offering.monthly_price
        setup_fee = base_offering.setup_fee
        discount = 0.0
        
        # Industry-based adjustments
        industry = lead_data.get('industry', '').lower()
        if industry in ['finance', 'healthcare', 'enterprise']:
            monthly_price = int(monthly_price * (1 + self.pricing_rules['enterprise_markup']))
        
        # Company size adjustments
        employee_count = lead_data.get('employee_count', 0)
        if employee_count and employee_count < 10:
            discount = max(discount, self.pricing_rules['startup_discount'])
        
        # Budget-based adjustments
        budget_range = qualification_data.get('budget_range', '')
        budget_amount = self.extract_budget_amount(budget_range)
        
        if budget_amount and budget_amount >= self.pricing_rules['volume_discount']['threshold']:
            discount = max(discount, self.pricing_rules['volume_discount']['discount'])
        
        # Apply discount
        if discount > 0:
            monthly_price = int(monthly_price * (1 - discount))
            setup_fee = int(setup_fee * (1 - discount))
        
        return monthly_price, setup_fee, discount
    
    def generate_proposal_content(self, lead_data: Dict, qualification_data: Dict, proposal: SalesProposal) -> str:
        """Generate personalized proposal content using AI"""
        
        company_name = lead_data.get('company_name', 'Your Company')
        contact_name = lead_data.get('contact_name', 'there')
        industry = lead_data.get('industry', 'business')
        pain_points = qualification_data.get('pain_points', [])
        
        # Parse pain points if they're JSON string
        if isinstance(pain_points, str):
            try:
                pain_points = json.loads(pain_points)
            except:
                pain_points = []
        
        pain_points_text = ', '.join(pain_points) if pain_points else 'digital marketing challenges'
        
        proposal_prompt = f"""
        Create a professional digital marketing proposal for:
        
        Company: {company_name}
        Contact: {contact_name}
        Industry: {industry}
        Pain Points: {pain_points_text}
        Package: {proposal.package.value}
        Monthly Price: ${proposal.monthly_price:,}
        Setup Fee: ${proposal.setup_fee:,}
        Services: {', '.join(proposal.services_included)}
        
        Write a compelling proposal that:
        1. Addresses their specific pain points
        2. Explains how our services solve their challenges
        3. Highlights the value and ROI they can expect
        4. Includes industry-specific benefits
        5. Creates urgency for decision making
        
        Keep it professional but personable, around 800-1000 words.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert sales proposal writer for digital marketing services. Create compelling, personalized proposals that address client needs and drive conversions."},
                    {"role": "user", "content": proposal_prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating proposal content: {str(e)}")
            return self.generate_fallback_proposal(lead_data, proposal)
    
    def generate_fallback_proposal(self, lead_data: Dict, proposal: SalesProposal) -> str:
        """Generate fallback proposal content without AI"""
        
        company_name = lead_data.get('company_name', 'Your Company')
        contact_name = lead_data.get('contact_name', 'there')
        
        return f"""
        Dear {contact_name},
        
        Thank you for your interest in our digital marketing services for {company_name}.
        
        Based on our conversation, I've prepared a customized proposal that addresses your specific needs and goals.
        
        PROPOSED SOLUTION: {proposal.package.value.title()} Package
        
        Monthly Investment: ${proposal.monthly_price:,}
        Setup Fee: ${proposal.setup_fee:,}
        Total First Month: ${proposal.total_first_month:,}
        
        SERVICES INCLUDED:
        {chr(10).join(f'• {service}' for service in proposal.services_included)}
        
        DELIVERABLES:
        {chr(10).join(f'• {deliverable}' for deliverable in proposal.deliverables)}
        
        Timeline: {proposal.timeline}
        
        This proposal is valid until {proposal.expiry_date.strftime('%B %d, %Y')}.
        
        I'm confident this solution will help {company_name} achieve significant growth in your digital presence and lead generation.
        
        Would you like to schedule a call to discuss this proposal in detail?
        
        Best regards,
        Alex Johnson
        Digital Marketing Strategist
        AI Marketing Solutions
        """
    
    def create_proposal(self, lead_id: int) -> Optional[SalesProposal]:
        """Create a sales proposal for a qualified lead"""
        
        # Get lead and qualification data
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
        lead_row = cursor.fetchone()
        
        if not lead_row:
            conn.close()
            return None
        
        lead_columns = [desc[0] for desc in cursor.description]
        lead_data = dict(zip(lead_columns, lead_row))
        
        cursor.execute('SELECT * FROM lead_qualifications WHERE lead_id = ?', (lead_id,))
        qual_row = cursor.fetchone()
        
        if not qual_row:
            conn.close()
            return None
        
        qual_columns = [desc[0] for desc in cursor.description]
        qualification_data = dict(zip(qual_columns, qual_row))
        
        conn.close()
        
        # Recommend package
        recommended_package = self.analyze_lead_for_package_recommendation(lead_data, qualification_data)
        
        # Calculate custom pricing
        monthly_price, setup_fee, discount = self.calculate_custom_pricing(
            recommended_package, lead_data, qualification_data
        )
        
        # Get package details
        package_offering = self.service_packages[recommended_package]
        
        # Create proposal
        proposal = SalesProposal(
            lead_id=lead_id,
            proposal_id=str(uuid.uuid4())[:8],
            package=recommended_package,
            monthly_price=monthly_price,
            setup_fee=setup_fee,
            total_first_month=monthly_price + setup_fee,
            services_included=package_offering.services_included,
            deliverables=package_offering.deliverables,
            timeline=package_offering.timeline,
            discount_percentage=discount
        )
        
        # Generate proposal content
        proposal_content = self.generate_proposal_content(lead_data, qualification_data, proposal)
        proposal.custom_notes = proposal_content
        
        # Save proposal
        self.save_proposal(proposal)
        
        return proposal
    
    def save_proposal(self, proposal: SalesProposal):
        """Save proposal to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sales_proposals (
                lead_id, proposal_id, package, monthly_price, setup_fee,
                total_first_month, services_included, deliverables, timeline,
                custom_notes, discount_percentage, proposal_date, expiry_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            proposal.lead_id, proposal.proposal_id, proposal.package.value,
            proposal.monthly_price, proposal.setup_fee, proposal.total_first_month,
            json.dumps(proposal.services_included), json.dumps(proposal.deliverables),
            proposal.timeline, proposal.custom_notes, proposal.discount_percentage,
            proposal.proposal_date.isoformat(), proposal.expiry_date.isoformat(),
            proposal.status
        ))
        
        conn.commit()
        conn.close()
    
    def create_deal(self, lead_id: int, proposal_id: str) -> SalesDeal:
        """Create a sales deal for tracking"""
        
        # Get proposal data
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM sales_proposals WHERE proposal_id = ?', (proposal_id,))
        proposal_row = cursor.fetchone()
        
        if not proposal_row:
            conn.close()
            return None
        
        proposal_columns = [desc[0] for desc in cursor.description]
        proposal_data = dict(zip(proposal_columns, proposal_row))
        
        conn.close()
        
        # Create deal
        deal = SalesDeal(
            lead_id=lead_id,
            deal_id=str(uuid.uuid4())[:8],
            stage=DealStage.PROPOSAL_SENT,
            proposal_id=proposal_id,
            value=proposal_data['monthly_price'] * 12,  # Annual value
            probability=0.3,  # Initial probability
            expected_close_date=datetime.now() + timedelta(days=30)
        )
        
        # Save deal
        self.save_deal(deal)
        
        return deal
    
    def save_deal(self, deal: SalesDeal):
        """Save deal to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sales_deals (
                lead_id, deal_id, stage, proposal_id, value, probability,
                expected_close_date, last_activity, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            deal.lead_id, deal.deal_id, deal.stage.value, deal.proposal_id,
            deal.value, deal.probability,
            deal.expected_close_date.isoformat() if deal.expected_close_date else None,
            deal.last_activity.isoformat(), deal.notes
        ))
        
        conn.commit()
        conn.close()
    
    def handle_objection(self, objection: str, deal_context: Dict) -> str:
        """Handle sales objections using AI"""
        
        objection_prompt = f"""
        Handle this sales objection for a digital marketing services proposal:
        
        Objection: "{objection}"
        
        Deal Context:
        - Package: {deal_context.get('package', 'Unknown')}
        - Monthly Price: ${deal_context.get('monthly_price', 0):,}
        - Industry: {deal_context.get('industry', 'Unknown')}
        
        Provide a professional, empathetic response that:
        1. Acknowledges their concern
        2. Provides a logical counter-argument
        3. Offers alternatives or compromises if appropriate
        4. Reinforces the value proposition
        5. Moves toward closing
        
        Keep the response conversational and under 200 words.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert sales professional specializing in digital marketing services. Handle objections professionally and persuasively."},
                    {"role": "user", "content": objection_prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error handling objection: {str(e)}")
            return self.generate_fallback_objection_response(objection)
    
    def generate_fallback_objection_response(self, objection: str) -> str:
        """Generate fallback objection response"""
        
        common_responses = {
            'price': "I understand budget is a concern. Let's look at the ROI - our clients typically see a 3-5x return on their marketing investment within 6 months. Would you like to discuss a smaller package or payment plan?",
            'time': "I appreciate that timing is important. We can actually start with a smaller scope and scale up as you see results. What timeline would work better for you?",
            'results': "That's a valid concern. We provide detailed monthly reports and guarantee specific KPIs. If we don't meet our commitments in the first 90 days, we'll work for free until we do.",
            'competition': "It's smart to compare options. What specific concerns do you have about our approach compared to others you're considering?"
        }
        
        objection_lower = objection.lower()
        
        if any(word in objection_lower for word in ['price', 'cost', 'expensive', 'budget']):
            return common_responses['price']
        elif any(word in objection_lower for word in ['time', 'timing', 'busy', 'schedule']):
            return common_responses['time']
        elif any(word in objection_lower for word in ['results', 'guarantee', 'proof', 'work']):
            return common_responses['results']
        elif any(word in objection_lower for word in ['competitor', 'other', 'compare', 'shopping']):
            return common_responses['competition']
        else:
            return "I understand your concern. Could you tell me more about what's holding you back so I can address it properly?"
    
    def update_deal_stage(self, deal_id: str, new_stage: DealStage, notes: str = ""):
        """Update deal stage and probability"""
        
        # Stage probability mapping
        stage_probabilities = {
            DealStage.INITIAL_CONTACT: 0.1,
            DealStage.DISCOVERY: 0.2,
            DealStage.PROPOSAL_SENT: 0.3,
            DealStage.NEGOTIATION: 0.6,
            DealStage.CONTRACT_SENT: 0.8,
            DealStage.CLOSED_WON: 1.0,
            DealStage.CLOSED_LOST: 0.0
        }
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sales_deals SET 
                stage = ?, 
                probability = ?, 
                last_activity = ?,
                notes = notes || ?
            WHERE deal_id = ?
        ''', (
            new_stage.value,
            stage_probabilities[new_stage],
            datetime.now().isoformat(),
            f" {notes}",
            deal_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_sales_pipeline(self) -> List[Dict]:
        """Get current sales pipeline"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sd.*, l.company_name, l.contact_name, sp.monthly_price
            FROM sales_deals sd
            JOIN leads l ON sd.lead_id = l.id
            LEFT JOIN sales_proposals sp ON sd.proposal_id = sp.proposal_id
            WHERE sd.stage NOT IN ('closed_won', 'closed_lost')
            ORDER BY sd.probability DESC, sd.value DESC
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        pipeline = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return pipeline
    
    def get_sales_metrics(self) -> Dict[str, any]:
        """Get sales performance metrics"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Total pipeline value
        cursor.execute('''
            SELECT SUM(value * probability) as weighted_pipeline
            FROM sales_deals 
            WHERE stage NOT IN ('closed_won', 'closed_lost')
        ''')
        weighted_pipeline = cursor.fetchone()[0] or 0
        
        # Closed won deals
        cursor.execute('''
            SELECT COUNT(*) as won_count, SUM(value) as won_value
            FROM sales_deals 
            WHERE stage = 'closed_won'
        ''')
        won_stats = cursor.fetchone()
        
        # Conversion rates by stage
        cursor.execute('''
            SELECT stage, COUNT(*) as count
            FROM sales_deals
            GROUP BY stage
        ''')
        stage_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'weighted_pipeline': weighted_pipeline,
            'won_deals': won_stats[0] or 0,
            'won_value': won_stats[1] or 0,
            'stage_distribution': stage_stats
        }
    
    def generate_sales_report(self) -> str:
        """Generate sales performance report"""
        metrics = self.get_sales_metrics()
        pipeline = self.get_sales_pipeline()
        
        report = f"""
SALES PERFORMANCE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PIPELINE OVERVIEW:
- Weighted Pipeline Value: ${metrics['weighted_pipeline']:,.2f}
- Active Deals: {len(pipeline)}
- Closed Won Deals: {metrics['won_deals']}
- Total Won Value: ${metrics['won_value']:,.2f}

STAGE DISTRIBUTION:
"""
        
        for stage, count in metrics['stage_distribution'].items():
            report += f"- {stage.replace('_', ' ').title()}: {count} deals\n"
        
        report += "\nTOP OPPORTUNITIES:\n"
        for deal in pipeline[:5]:
            report += f"- {deal['company_name']}: ${deal['value']:,} ({deal['probability']:.0%} probability)\n"
        
        return report


def main():
    """Main function to demonstrate the sales automation agent"""
    agent = SalesAutomationAgent()
    
    # Get qualified leads
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT l.id FROM leads l
        JOIN lead_qualifications lq ON l.id = lq.lead_id
        WHERE lq.status = 'qualified'
        LIMIT 2
    ''')
    
    lead_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not lead_ids:
        print("No qualified leads found.")
        return
    
    # Create proposals
    for lead_id in lead_ids:
        print(f"Creating proposal for lead {lead_id}...")
        proposal = agent.create_proposal(lead_id)
        
        if proposal:
            print(f"- Proposal ID: {proposal.proposal_id}")
            print(f"- Package: {proposal.package.value}")
            print(f"- Monthly Price: ${proposal.monthly_price:,}")
            print(f"- Setup Fee: ${proposal.setup_fee:,}")
            print(f"- Discount: {proposal.discount_percentage:.1%}")
            
            # Create deal
            deal = agent.create_deal(lead_id, proposal.proposal_id)
            print(f"- Deal ID: {deal.deal_id}")
            print(f"- Deal Value: ${deal.value:,}")
            print()
    
    # Show pipeline
    pipeline = agent.get_sales_pipeline()
    print(f"Current pipeline: {len(pipeline)} active deals")
    
    # Generate report
    report = agent.generate_sales_report()
    print(report)


if __name__ == "__main__":
    main()

