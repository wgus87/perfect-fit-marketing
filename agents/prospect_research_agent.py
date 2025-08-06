"""
Prospect Research Agent - Deep research and data enrichment for leads
This agent performs comprehensive research on prospects to gather intelligence
"""

import requests
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3
import re
from urllib.parse import urljoin, urlparse
import os


@dataclass
class CompanyIntelligence:
    """Data structure for storing company intelligence"""
    company_name: str
    website: str
    industry: str
    description: str = ""
    founded_year: Optional[int] = None
    headquarters: str = ""
    employee_count: Optional[int] = None
    revenue_range: str = ""
    funding_info: Dict = None
    key_personnel: List[Dict] = None
    competitors: List[str] = None
    technologies_used: List[str] = None
    social_media_presence: Dict[str, str] = None
    recent_news: List[Dict] = None
    pain_points: List[str] = None
    growth_indicators: List[str] = None
    digital_maturity_score: float = 0.0
    research_date: datetime = None
    
    def __post_init__(self):
        if self.funding_info is None:
            self.funding_info = {}
        if self.key_personnel is None:
            self.key_personnel = []
        if self.competitors is None:
            self.competitors = []
        if self.technologies_used is None:
            self.technologies_used = []
        if self.social_media_presence is None:
            self.social_media_presence = {}
        if self.recent_news is None:
            self.recent_news = []
        if self.pain_points is None:
            self.pain_points = []
        if self.growth_indicators is None:
            self.growth_indicators = []
        if self.research_date is None:
            self.research_date = datetime.now()


class ProspectResearchAgent:
    """
    AI-powered prospect research agent that gathers comprehensive intelligence
    """
    
    def __init__(self, database_path: str = "leads.db"):
        self.database_path = database_path
        self.setup_database()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Research sources and patterns
        self.social_platforms = {
            'linkedin': 'linkedin.com/company/',
            'twitter': 'twitter.com/',
            'facebook': 'facebook.com/',
            'instagram': 'instagram.com/'
        }
        
        # Technology indicators for digital maturity assessment
        self.tech_indicators = {
            'modern_cms': ['wordpress', 'drupal', 'shopify', 'squarespace'],
            'ecommerce': ['shopify', 'magento', 'woocommerce', 'bigcommerce'],
            'analytics': ['google analytics', 'adobe analytics', 'mixpanel'],
            'marketing_automation': ['hubspot', 'marketo', 'pardot', 'mailchimp'],
            'social_media_tools': ['hootsuite', 'buffer', 'sprout social'],
            'modern_frameworks': ['react', 'angular', 'vue', 'next.js']
        }
        
        # Pain point indicators
        self.pain_point_keywords = {
            'low_traffic': ['increase traffic', 'more visitors', 'website traffic'],
            'poor_conversion': ['conversion rate', 'lead generation', 'sales funnel'],
            'brand_awareness': ['brand recognition', 'market presence', 'visibility'],
            'competition': ['competitive advantage', 'market share', 'differentiation'],
            'digital_presence': ['online presence', 'digital marketing', 'social media']
        }
    
    def setup_database(self):
        """Initialize database tables for storing research data"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_intelligence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                website TEXT,
                industry TEXT,
                description TEXT,
                founded_year INTEGER,
                headquarters TEXT,
                employee_count INTEGER,
                revenue_range TEXT,
                funding_info TEXT,
                key_personnel TEXT,
                competitors TEXT,
                technologies_used TEXT,
                social_media_presence TEXT,
                recent_news TEXT,
                pain_points TEXT,
                growth_indicators TEXT,
                digital_maturity_score REAL,
                research_date TEXT,
                UNIQUE(company_name, website)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def research_company(self, company_name: str, website: str) -> CompanyIntelligence:
        """Conduct comprehensive research on a company"""
        print(f"Researching {company_name}...")
        
        intelligence = CompanyIntelligence(
            company_name=company_name,
            website=website,
            industry="",  # Will be determined during research
        )
        
        # Website analysis
        website_data = self.analyze_company_website(website)
        if website_data:
            intelligence.description = website_data.get('description', '')
            intelligence.technologies_used = website_data.get('technologies', [])
            intelligence.pain_points = website_data.get('pain_points', [])
        
        # Social media research
        intelligence.social_media_presence = self.find_social_media_profiles(company_name, website)
        
        # Technology stack analysis
        intelligence.digital_maturity_score = self.assess_digital_maturity(intelligence)
        
        # Growth indicators analysis
        intelligence.growth_indicators = self.identify_growth_indicators(intelligence)
        
        # Industry classification
        intelligence.industry = self.classify_industry(intelligence)
        
        return intelligence
    
    def analyze_company_website(self, website: str) -> Optional[Dict]:
        """Analyze company website for insights"""
        try:
            response = self.session.get(website, timeout=15)
            if response.status_code != 200:
                return None
            
            content = response.text.lower()
            
            analysis = {
                'description': '',
                'technologies': [],
                'pain_points': [],
                'contact_info': {},
                'pages': []
            }
            
            # Extract meta description
            meta_desc_pattern = r'<meta name="description" content="([^"]*)"'
            meta_match = re.search(meta_desc_pattern, content, re.IGNORECASE)
            if meta_match:
                analysis['description'] = meta_match.group(1)
            
            # Identify technologies
            for category, techs in self.tech_indicators.items():
                for tech in techs:
                    if tech in content:
                        analysis['technologies'].append(tech)
            
            # Identify pain points from content
            for pain_type, keywords in self.pain_point_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        analysis['pain_points'].append(pain_type)
            
            # Find key pages
            key_pages = ['about', 'services', 'products', 'contact', 'blog', 'news']
            for page in key_pages:
                if f'/{page}' in content or f'{page}.html' in content:
                    analysis['pages'].append(page)
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing website {website}: {str(e)}")
            return None
    
    def find_social_media_profiles(self, company_name: str, website: str) -> Dict[str, str]:
        """Find social media profiles for the company"""
        profiles = {}
        
        # Extract domain for social media search
        domain = urlparse(website).netloc.replace('www.', '')
        company_slug = company_name.lower().replace(' ', '').replace(',', '').replace('.', '')
        
        # Common social media profile patterns
        potential_profiles = {
            'linkedin': [
                f"linkedin.com/company/{company_slug}",
                f"linkedin.com/company/{company_name.lower().replace(' ', '-')}",
                f"linkedin.com/company/{domain.split('.')[0]}"
            ],
            'twitter': [
                f"twitter.com/{company_slug}",
                f"twitter.com/{domain.split('.')[0]}",
                f"twitter.com/{company_name.lower().replace(' ', '')}"
            ],
            'facebook': [
                f"facebook.com/{company_slug}",
                f"facebook.com/{domain.split('.')[0]}",
                f"facebook.com/{company_name.lower().replace(' ', '')}"
            ]
        }
        
        # Check if profiles exist (simplified - in production, use actual API calls)
        for platform, urls in potential_profiles.items():
            for url in urls:
                full_url = f"https://{url}"
                try:
                    response = self.session.head(full_url, timeout=5)
                    if response.status_code == 200:
                        profiles[platform] = full_url
                        break
                except:
                    continue
        
        return profiles
    
    def assess_digital_maturity(self, intelligence: CompanyIntelligence) -> float:
        """Assess company's digital maturity based on technology usage"""
        score = 0.0
        max_score = 1.0
        
        # Website technology score (0.3)
        tech_score = 0.0
        if intelligence.technologies_used:
            modern_tech_count = len([t for t in intelligence.technologies_used 
                                   if t in ['react', 'angular', 'vue', 'next.js', 'shopify']])
            tech_score = min(modern_tech_count / 3, 1.0) * 0.3
        
        # Social media presence score (0.2)
        social_score = 0.0
        if intelligence.social_media_presence:
            social_score = min(len(intelligence.social_media_presence) / 4, 1.0) * 0.2
        
        # Marketing tools score (0.3)
        marketing_score = 0.0
        marketing_tools = [t for t in intelligence.technologies_used 
                          if t in ['google analytics', 'hubspot', 'marketo', 'mailchimp']]
        if marketing_tools:
            marketing_score = min(len(marketing_tools) / 3, 1.0) * 0.3
        
        # E-commerce capability score (0.2)
        ecommerce_score = 0.0
        ecommerce_tools = [t for t in intelligence.technologies_used 
                          if t in ['shopify', 'magento', 'woocommerce', 'bigcommerce']]
        if ecommerce_tools:
            ecommerce_score = 0.2
        
        score = tech_score + social_score + marketing_score + ecommerce_score
        return min(score, max_score)
    
    def identify_growth_indicators(self, intelligence: CompanyIntelligence) -> List[str]:
        """Identify indicators of company growth"""
        indicators = []
        
        # Technology adoption indicates growth
        if intelligence.digital_maturity_score > 0.6:
            indicators.append("high_digital_maturity")
        
        # Social media presence indicates marketing investment
        if len(intelligence.social_media_presence) >= 3:
            indicators.append("strong_social_presence")
        
        # Modern website technologies indicate recent investment
        modern_techs = ['react', 'angular', 'vue', 'next.js', 'shopify']
        if any(tech in intelligence.technologies_used for tech in modern_techs):
            indicators.append("modern_technology_stack")
        
        # Marketing automation tools indicate scaling efforts
        marketing_tools = ['hubspot', 'marketo', 'pardot', 'mailchimp']
        if any(tool in intelligence.technologies_used for tool in marketing_tools):
            indicators.append("marketing_automation_adoption")
        
        return indicators
    
    def classify_industry(self, intelligence: CompanyIntelligence) -> str:
        """Classify company industry based on available data"""
        description = intelligence.description.lower()
        technologies = [t.lower() for t in intelligence.technologies_used]
        
        # E-commerce indicators
        if any(tech in technologies for tech in ['shopify', 'magento', 'woocommerce']):
            return 'e-commerce'
        
        # Technology company indicators
        tech_keywords = ['software', 'technology', 'app', 'platform', 'saas']
        if any(keyword in description for keyword in tech_keywords):
            return 'technology'
        
        # Professional services indicators
        service_keywords = ['consulting', 'services', 'agency', 'firm']
        if any(keyword in description for keyword in service_keywords):
            return 'professional_services'
        
        # Healthcare indicators
        health_keywords = ['health', 'medical', 'clinic', 'hospital']
        if any(keyword in description for keyword in health_keywords):
            return 'healthcare'
        
        # Default classification
        return 'general_business'
    
    def save_intelligence(self, intelligence: CompanyIntelligence) -> int:
        """Save company intelligence to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO company_intelligence (
                    company_name, website, industry, description, founded_year,
                    headquarters, employee_count, revenue_range, funding_info,
                    key_personnel, competitors, technologies_used,
                    social_media_presence, recent_news, pain_points,
                    growth_indicators, digital_maturity_score, research_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                intelligence.company_name, intelligence.website, intelligence.industry,
                intelligence.description, intelligence.founded_year, intelligence.headquarters,
                intelligence.employee_count, intelligence.revenue_range,
                json.dumps(intelligence.funding_info), json.dumps(intelligence.key_personnel),
                json.dumps(intelligence.competitors), json.dumps(intelligence.technologies_used),
                json.dumps(intelligence.social_media_presence), json.dumps(intelligence.recent_news),
                json.dumps(intelligence.pain_points), json.dumps(intelligence.growth_indicators),
                intelligence.digital_maturity_score, intelligence.research_date.isoformat()
            ))
            
            intelligence_id = cursor.lastrowid
            conn.commit()
            return intelligence_id
            
        except Exception as e:
            print(f"Error saving intelligence: {str(e)}")
            return 0
        finally:
            conn.close()
    
    def get_intelligence(self, company_name: str, website: str) -> Optional[CompanyIntelligence]:
        """Retrieve company intelligence from database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM company_intelligence 
            WHERE company_name = ? AND website = ?
        ''', (company_name, website))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Convert row to CompanyIntelligence object
            columns = [
                'id', 'company_name', 'website', 'industry', 'description',
                'founded_year', 'headquarters', 'employee_count', 'revenue_range',
                'funding_info', 'key_personnel', 'competitors', 'technologies_used',
                'social_media_presence', 'recent_news', 'pain_points',
                'growth_indicators', 'digital_maturity_score', 'research_date'
            ]
            
            data = dict(zip(columns, row))
            
            # Parse JSON fields
            json_fields = [
                'funding_info', 'key_personnel', 'competitors', 'technologies_used',
                'social_media_presence', 'recent_news', 'pain_points', 'growth_indicators'
            ]
            
            for field in json_fields:
                if data[field]:
                    data[field] = json.loads(data[field])
                else:
                    data[field] = [] if field != 'funding_info' else {}
            
            # Convert research_date
            if data['research_date']:
                data['research_date'] = datetime.fromisoformat(data['research_date'])
            
            # Remove id field and create CompanyIntelligence object
            del data['id']
            return CompanyIntelligence(**data)
        
        return None
    
    def research_leads_batch(self, leads: List[Dict]) -> List[CompanyIntelligence]:
        """Research multiple leads in batch"""
        intelligence_results = []
        
        for lead in leads:
            company_name = lead['company_name']
            website = lead['website']
            
            # Check if we already have intelligence for this company
            existing_intelligence = self.get_intelligence(company_name, website)
            
            if existing_intelligence:
                print(f"Using existing intelligence for {company_name}")
                intelligence_results.append(existing_intelligence)
            else:
                # Conduct new research
                intelligence = self.research_company(company_name, website)
                
                # Save to database
                intelligence_id = self.save_intelligence(intelligence)
                if intelligence_id:
                    print(f"Saved intelligence for {company_name} (ID: {intelligence_id})")
                
                intelligence_results.append(intelligence)
                
                # Rate limiting
                time.sleep(2)
        
        return intelligence_results
    
    def generate_prospect_summary(self, intelligence: CompanyIntelligence) -> str:
        """Generate a summary of prospect research for sales team"""
        summary = f"""
PROSPECT RESEARCH SUMMARY
Company: {intelligence.company_name}
Website: {intelligence.website}
Industry: {intelligence.industry}
Digital Maturity Score: {intelligence.digital_maturity_score:.2f}/1.0

DESCRIPTION:
{intelligence.description}

TECHNOLOGIES USED:
{', '.join(intelligence.technologies_used) if intelligence.technologies_used else 'None identified'}

SOCIAL MEDIA PRESENCE:
{', '.join(intelligence.social_media_presence.keys()) if intelligence.social_media_presence else 'Limited'}

IDENTIFIED PAIN POINTS:
{', '.join(intelligence.pain_points) if intelligence.pain_points else 'None identified'}

GROWTH INDICATORS:
{', '.join(intelligence.growth_indicators) if intelligence.growth_indicators else 'None identified'}

RESEARCH DATE: {intelligence.research_date.strftime('%Y-%m-%d')}
"""
        return summary


def main():
    """Main function to demonstrate the prospect research agent"""
    agent = ProspectResearchAgent()
    
    # Sample leads for research
    sample_leads = [
        {
            'company_name': 'TechStart Solutions',
            'website': 'https://techstartsolutions.com'
        },
        {
            'company_name': 'GreenLeaf Consulting',
            'website': 'https://greenleafconsulting.com'
        }
    ]
    
    # Research leads
    intelligence_results = agent.research_leads_batch(sample_leads)
    
    # Generate summaries
    for intelligence in intelligence_results:
        summary = agent.generate_prospect_summary(intelligence)
        print(summary)
        print("-" * 80)


if __name__ == "__main__":
    main()

