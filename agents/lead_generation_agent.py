"""
Lead Generation Agent - Automated prospect discovery and data collection
This agent continuously searches for potential clients across multiple channels
"""

import requests
import json
import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3
import os
import sys
from urllib.parse import urljoin, urlparse
import re

# Add parent directory to path to import API modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_integrations import APIIntegrationService


@dataclass
class Lead:
    """Data structure for storing lead information"""
    company_name: str
    website: str
    industry: str
    employee_count: Optional[int] = None
    revenue_estimate: Optional[str] = None
    location: str = ""
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    contact_title: Optional[str] = None
    phone: Optional[str] = None
    social_media: Dict[str, str] = None
    lead_score: float = 0.0
    source: str = ""
    discovered_date: datetime = None
    last_updated: datetime = None
    notes: str = ""
    
    def __post_init__(self):
        if self.social_media is None:
            self.social_media = {}
        if self.discovered_date is None:
            self.discovered_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()


class LeadGenerationAgent:
    """
    AI-powered lead generation agent that automatically discovers and qualifies prospects
    """
    
    def __init__(self, database_path: str = "leads.db"):
        self.database_path = database_path
        self.setup_database()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Initialize API integration service
        self.api_service = APIIntegrationService()
        
        # Lead scoring weights
        self.scoring_weights = {
            'website_quality': 0.2,
            'social_presence': 0.15,
            'company_size': 0.25,
            'industry_relevance': 0.2,
            'contact_availability': 0.2
        }
        
        # Target industries for digital marketing services
        self.target_industries = [
            'technology', 'software', 'saas', 'e-commerce', 'retail',
            'healthcare', 'finance', 'real estate', 'professional services',
            'manufacturing', 'consulting', 'education', 'hospitality'
        ]
    
    def setup_database(self):
        """Initialize SQLite database for storing leads"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                website TEXT,
                industry TEXT,
                employee_count INTEGER,
                revenue_estimate TEXT,
                location TEXT,
                contact_email TEXT,
                contact_name TEXT,
                contact_title TEXT,
                phone TEXT,
                social_media TEXT,
                lead_score REAL,
                source TEXT,
                discovered_date TEXT,
                last_updated TEXT,
                notes TEXT,
                status TEXT DEFAULT 'new'
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_lead_score ON leads(lead_score DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_company_name ON leads(company_name)
        ''')
        
        conn.commit()
        conn.close()
    
    def save_lead(self, lead: Lead) -> int:
        """Save lead to database and return the lead ID"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Check if lead already exists
        cursor.execute(
            "SELECT id FROM leads WHERE company_name = ? AND website = ?",
            (lead.company_name, lead.website)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing lead
            cursor.execute('''
                UPDATE leads SET
                    industry = ?, employee_count = ?, revenue_estimate = ?,
                    location = ?, contact_email = ?, contact_name = ?,
                    contact_title = ?, phone = ?, social_media = ?,
                    lead_score = ?, source = ?, last_updated = ?, notes = ?
                WHERE id = ?
            ''', (
                lead.industry, lead.employee_count, lead.revenue_estimate,
                lead.location, lead.contact_email, lead.contact_name,
                lead.contact_title, lead.phone, json.dumps(lead.social_media),
                lead.lead_score, lead.source, lead.last_updated.isoformat(),
                lead.notes, existing[0]
            ))
            lead_id = existing[0]
        else:
            # Insert new lead
            cursor.execute('''
                INSERT INTO leads (
                    company_name, website, industry, employee_count,
                    revenue_estimate, location, contact_email, contact_name,
                    contact_title, phone, social_media, lead_score, source,
                    discovered_date, last_updated, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lead.company_name, lead.website, lead.industry,
                lead.employee_count, lead.revenue_estimate, lead.location,
                lead.contact_email, lead.contact_name, lead.contact_title,
                lead.phone, json.dumps(lead.social_media), lead.lead_score,
                lead.source, lead.discovered_date.isoformat(),
                lead.last_updated.isoformat(), lead.notes
            ))
            lead_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return lead_id
    
    def get_leads(self, limit: int = 100, min_score: float = 0.0) -> List[Dict]:
        """Retrieve leads from database with optional filtering"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM leads 
            WHERE lead_score >= ? 
            ORDER BY lead_score DESC 
            LIMIT ?
        ''', (min_score, limit))
        
        columns = [description[0] for description in cursor.description]
        leads = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return leads
    
    def discover_leads_from_directories(self, directories: List[str]) -> List[Lead]:
        """
        Discover leads from business directories and databases
        This is a simplified version - in production, you'd integrate with APIs
        """
        discovered_leads = []
        
        # Simulated directory data - replace with actual API integrations
        sample_companies = [
            {
                'name': 'TechStart Solutions',
                'website': 'https://techstartsolutions.com',
                'industry': 'technology',
                'employees': 25,
                'location': 'San Francisco, CA'
            },
            {
                'name': 'GreenLeaf Consulting',
                'website': 'https://greenleafconsulting.com',
                'industry': 'consulting',
                'employees': 15,
                'location': 'Austin, TX'
            },
            {
                'name': 'Digital Commerce Pro',
                'website': 'https://digitalcommercepro.com',
                'industry': 'e-commerce',
                'employees': 50,
                'location': 'New York, NY'
            }
        ]
        
        for company_data in sample_companies:
            lead = Lead(
                company_name=company_data['name'],
                website=company_data['website'],
                industry=company_data['industry'],
                employee_count=company_data['employees'],
                location=company_data['location'],
                source='business_directory'
            )
            
            # Enrich lead data
            enriched_lead = self.enrich_lead_data(lead)
            discovered_leads.append(enriched_lead)
        
        return discovered_leads
    
    def enrich_lead_data(self, lead: Lead) -> Lead:
        """Enrich lead data with additional information from various sources"""
        
        # Analyze website for additional insights
        if lead.website:
            website_data = self.analyze_website(lead.website)
            if website_data:
                lead.notes += f"Website analysis: {website_data.get('description', '')} "
                
                # Extract contact information if available
                if 'contact_email' in website_data and not lead.contact_email:
                    lead.contact_email = website_data['contact_email']
                
                if 'phone' in website_data and not lead.phone:
                    lead.phone = website_data['phone']
        
        # Calculate lead score
        lead.lead_score = self.calculate_lead_score(lead)
        
        return lead
    
    def analyze_website(self, url: str) -> Optional[Dict]:
        """Analyze website to extract relevant information"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text.lower()
                
                # Extract basic information
                website_data = {
                    'has_contact_page': 'contact' in content or 'about' in content,
                    'has_blog': 'blog' in content or 'news' in content,
                    'has_social_media': any(platform in content for platform in 
                                          ['facebook', 'twitter', 'linkedin', 'instagram']),
                    'technology_indicators': []
                }
                
                # Look for technology indicators
                tech_keywords = ['wordpress', 'shopify', 'react', 'angular', 'vue', 'magento']
                for keyword in tech_keywords:
                    if keyword in content:
                        website_data['technology_indicators'].append(keyword)
                
                # Extract email addresses
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, content)
                if emails:
                    website_data['contact_email'] = emails[0]
                
                # Extract phone numbers
                phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
                phones = re.findall(phone_pattern, content)
                if phones:
                    website_data['phone'] = phones[0]
                
                return website_data
                
        except Exception as e:
            print(f"Error analyzing website {url}: {str(e)}")
            return None
    
    def calculate_lead_score(self, lead: Lead) -> float:
        """Calculate lead score based on various factors"""
        score = 0.0
        
        # Website quality score
        if lead.website:
            score += self.scoring_weights['website_quality'] * 0.8
        
        # Social media presence
        if lead.social_media and len(lead.social_media) > 0:
            score += self.scoring_weights['social_presence'] * min(len(lead.social_media) / 3, 1.0)
        
        # Company size score
        if lead.employee_count:
            if 10 <= lead.employee_count <= 500:  # Sweet spot for digital marketing services
                score += self.scoring_weights['company_size'] * 1.0
            elif lead.employee_count < 10:
                score += self.scoring_weights['company_size'] * 0.6
            else:
                score += self.scoring_weights['company_size'] * 0.4
        
        # Industry relevance
        if lead.industry and lead.industry.lower() in self.target_industries:
            score += self.scoring_weights['industry_relevance'] * 1.0
        
        # Contact availability
        contact_score = 0.0
        if lead.contact_email:
            contact_score += 0.5
        if lead.contact_name:
            contact_score += 0.3
        if lead.phone:
            contact_score += 0.2
        score += self.scoring_weights['contact_availability'] * contact_score
        
        return min(score, 1.0)  # Cap at 1.0
    
    def run_discovery_cycle(self) -> Dict[str, int]:
        """Run a complete lead discovery cycle"""
        print("Starting lead discovery cycle...")
        
        # Discover leads from various sources
        directories = ['yellowpages', 'yelp', 'google_business']
        new_leads = self.discover_leads_from_directories(directories)
        
        # Save leads to database
        saved_count = 0
        for lead in new_leads:
            lead_id = self.save_lead(lead)
            if lead_id:
                saved_count += 1
                print(f"Saved lead: {lead.company_name} (Score: {lead.lead_score:.2f})")
        
        # Get statistics
        high_quality_leads = len([l for l in new_leads if l.lead_score >= 0.7])
        medium_quality_leads = len([l for l in new_leads if 0.4 <= l.lead_score < 0.7])
        
        return {
            'total_discovered': len(new_leads),
            'total_saved': saved_count,
            'high_quality': high_quality_leads,
            'medium_quality': medium_quality_leads
        }
    
    def get_top_leads(self, limit: int = 20) -> List[Dict]:
        """Get top-scoring leads for outreach"""
        return self.get_leads(limit=limit, min_score=0.5)
    
    def update_lead_status(self, lead_id: int, status: str, notes: str = ""):
        """Update lead status and notes"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE leads SET 
                status = ?, 
                notes = notes || ?, 
                last_updated = ?
            WHERE id = ?
        ''', (status, f" {notes}", datetime.now().isoformat(), lead_id))
        
        conn.commit()
        conn.close()


def main():
    """Main function to demonstrate the lead generation agent"""
    agent = LeadGenerationAgent()
    
    # Run discovery cycle
    results = agent.run_discovery_cycle()
    print(f"\nDiscovery Results:")
    print(f"Total discovered: {results['total_discovered']}")
    print(f"Total saved: {results['total_saved']}")
    print(f"High quality leads: {results['high_quality']}")
    print(f"Medium quality leads: {results['medium_quality']}")
    
    # Get top leads
    top_leads = agent.get_top_leads(10)
    print(f"\nTop {len(top_leads)} leads:")
    for lead in top_leads:
        print(f"- {lead['company_name']} ({lead['industry']}) - Score: {lead['lead_score']:.2f}")


if __name__ == "__main__":
    main()

