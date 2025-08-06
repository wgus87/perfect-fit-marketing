"""
Lead Scoring Agent - Advanced lead scoring and prioritization system
This agent uses machine learning and rule-based scoring to prioritize leads
"""

import sqlite3
import json
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math


@dataclass
class ScoringCriteria:
    """Configuration for lead scoring criteria"""
    company_size_weight: float = 0.25
    industry_relevance_weight: float = 0.20
    digital_maturity_weight: float = 0.20
    contact_quality_weight: float = 0.15
    growth_indicators_weight: float = 0.10
    pain_points_weight: float = 0.10
    
    # Company size scoring ranges
    ideal_employee_range: Tuple[int, int] = (10, 500)
    min_employee_threshold: int = 5
    
    # Industry scoring
    high_value_industries: List[str] = None
    medium_value_industries: List[str] = None
    
    # Digital maturity thresholds
    high_maturity_threshold: float = 0.7
    medium_maturity_threshold: float = 0.4
    
    def __post_init__(self):
        if self.high_value_industries is None:
            self.high_value_industries = [
                'technology', 'software', 'saas', 'e-commerce', 'finance',
                'healthcare', 'professional_services', 'consulting'
            ]
        if self.medium_value_industries is None:
            self.medium_value_industries = [
                'retail', 'manufacturing', 'education', 'real_estate',
                'hospitality', 'automotive', 'media'
            ]


class LeadScoringAgent:
    """
    Advanced lead scoring agent that evaluates and prioritizes prospects
    """
    
    def __init__(self, database_path: str = "leads.db", criteria: ScoringCriteria = None):
        self.database_path = database_path
        self.criteria = criteria or ScoringCriteria()
        self.setup_database()
        
        # Scoring history for machine learning improvements
        self.scoring_history = []
        
        # Pain point value mapping
        self.pain_point_values = {
            'low_traffic': 0.9,
            'poor_conversion': 0.95,
            'brand_awareness': 0.8,
            'competition': 0.85,
            'digital_presence': 0.9,
            'lead_generation': 0.95,
            'customer_retention': 0.8,
            'market_expansion': 0.85
        }
        
        # Growth indicator values
        self.growth_indicator_values = {
            'high_digital_maturity': 0.9,
            'strong_social_presence': 0.7,
            'modern_technology_stack': 0.8,
            'marketing_automation_adoption': 0.85,
            'recent_funding': 0.95,
            'expanding_team': 0.8,
            'new_product_launch': 0.9
        }
    
    def setup_database(self):
        """Initialize database tables for scoring data"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lead_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                company_name TEXT,
                total_score REAL,
                company_size_score REAL,
                industry_score REAL,
                digital_maturity_score REAL,
                contact_quality_score REAL,
                growth_indicators_score REAL,
                pain_points_score REAL,
                scoring_date TEXT,
                scoring_version TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scoring_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                predicted_score REAL,
                actual_outcome TEXT,
                feedback_date TEXT,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def score_company_size(self, employee_count: Optional[int]) -> float:
        """Score based on company size"""
        if not employee_count:
            return 0.3  # Unknown size gets medium-low score
        
        min_range, max_range = self.criteria.ideal_employee_range
        
        if employee_count < self.criteria.min_employee_threshold:
            return 0.2  # Too small
        elif min_range <= employee_count <= max_range:
            return 1.0  # Ideal size
        elif employee_count < min_range:
            # Scale from min_threshold to min_range
            ratio = (employee_count - self.criteria.min_employee_threshold) / (min_range - self.criteria.min_employee_threshold)
            return 0.2 + (0.8 * ratio)
        else:
            # Larger companies get decreasing scores
            excess = employee_count - max_range
            decay_factor = math.exp(-excess / 1000)  # Exponential decay
            return 0.6 * decay_factor
    
    def score_industry_relevance(self, industry: str) -> float:
        """Score based on industry relevance"""
        if not industry:
            return 0.5  # Unknown industry gets medium score
        
        industry_lower = industry.lower()
        
        if industry_lower in self.criteria.high_value_industries:
            return 1.0
        elif industry_lower in self.criteria.medium_value_industries:
            return 0.7
        else:
            return 0.4  # Low-value industry
    
    def score_digital_maturity(self, maturity_score: float) -> float:
        """Score based on digital maturity"""
        if maturity_score >= self.criteria.high_maturity_threshold:
            return 1.0
        elif maturity_score >= self.criteria.medium_maturity_threshold:
            return 0.7
        else:
            return 0.4
    
    def score_contact_quality(self, lead_data: Dict) -> float:
        """Score based on contact information quality"""
        score = 0.0
        
        # Email availability and quality
        if lead_data.get('contact_email'):
            email = lead_data['contact_email']
            if '@' in email and '.' in email:
                score += 0.4
                # Bonus for business email domains
                if not any(domain in email for domain in ['gmail.com', 'yahoo.com', 'hotmail.com']):
                    score += 0.1
        
        # Contact name availability
        if lead_data.get('contact_name'):
            score += 0.2
        
        # Contact title/role information
        if lead_data.get('contact_title'):
            title = lead_data['contact_title'].lower()
            # Higher score for decision-maker titles
            if any(keyword in title for keyword in ['ceo', 'founder', 'owner', 'president', 'director']):
                score += 0.3
            elif any(keyword in title for keyword in ['manager', 'head', 'lead']):
                score += 0.2
            else:
                score += 0.1
        
        # Phone number availability
        if lead_data.get('phone'):
            score += 0.1
        
        return min(score, 1.0)
    
    def score_growth_indicators(self, growth_indicators: List[str]) -> float:
        """Score based on growth indicators"""
        if not growth_indicators:
            return 0.0
        
        total_score = 0.0
        for indicator in growth_indicators:
            if indicator in self.growth_indicator_values:
                total_score += self.growth_indicator_values[indicator]
        
        # Normalize to 0-1 range (assuming max 3 strong indicators)
        return min(total_score / 3.0, 1.0)
    
    def score_pain_points(self, pain_points: List[str]) -> float:
        """Score based on identified pain points"""
        if not pain_points:
            return 0.0
        
        total_score = 0.0
        for pain_point in pain_points:
            if pain_point in self.pain_point_values:
                total_score += self.pain_point_values[pain_point]
        
        # Normalize to 0-1 range (assuming max 2 major pain points)
        return min(total_score / 2.0, 1.0)
    
    def calculate_composite_score(self, lead_data: Dict, intelligence_data: Dict = None) -> Dict[str, float]:
        """Calculate comprehensive lead score"""
        scores = {}
        
        # Company size score
        scores['company_size'] = self.score_company_size(lead_data.get('employee_count'))
        
        # Industry relevance score
        scores['industry'] = self.score_industry_relevance(lead_data.get('industry'))
        
        # Digital maturity score
        if intelligence_data:
            scores['digital_maturity'] = self.score_digital_maturity(
                intelligence_data.get('digital_maturity_score', 0.0)
            )
            
            # Growth indicators score
            scores['growth_indicators'] = self.score_growth_indicators(
                intelligence_data.get('growth_indicators', [])
            )
            
            # Pain points score
            scores['pain_points'] = self.score_pain_points(
                intelligence_data.get('pain_points', [])
            )
        else:
            scores['digital_maturity'] = 0.5  # Default when no intelligence data
            scores['growth_indicators'] = 0.0
            scores['pain_points'] = 0.0
        
        # Contact quality score
        scores['contact_quality'] = self.score_contact_quality(lead_data)
        
        # Calculate weighted total score
        total_score = (
            scores['company_size'] * self.criteria.company_size_weight +
            scores['industry'] * self.criteria.industry_relevance_weight +
            scores['digital_maturity'] * self.criteria.digital_maturity_weight +
            scores['contact_quality'] * self.criteria.contact_quality_weight +
            scores['growth_indicators'] * self.criteria.growth_indicators_weight +
            scores['pain_points'] * self.criteria.pain_points_weight
        )
        
        scores['total'] = total_score
        return scores
    
    def score_lead(self, lead_id: int) -> Optional[Dict[str, float]]:
        """Score a single lead by ID"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Get lead data
        cursor.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
        lead_row = cursor.fetchone()
        
        if not lead_row:
            conn.close()
            return None
        
        # Convert to dict
        lead_columns = [desc[0] for desc in cursor.description]
        lead_data = dict(zip(lead_columns, lead_row))
        
        # Get intelligence data if available
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
            json_fields = ['growth_indicators', 'pain_points']
            for field in json_fields:
                if intelligence_data.get(field):
                    intelligence_data[field] = json.loads(intelligence_data[field])
        
        conn.close()
        
        # Calculate scores
        scores = self.calculate_composite_score(lead_data, intelligence_data)
        
        # Save scores to database
        self.save_lead_score(lead_id, lead_data['company_name'], scores)
        
        return scores
    
    def save_lead_score(self, lead_id: int, company_name: str, scores: Dict[str, float]):
        """Save lead scores to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO lead_scores (
                lead_id, company_name, total_score, company_size_score,
                industry_score, digital_maturity_score, contact_quality_score,
                growth_indicators_score, pain_points_score, scoring_date, scoring_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lead_id, company_name, scores['total'], scores['company_size'],
            scores['industry'], scores['digital_maturity'], scores['contact_quality'],
            scores['growth_indicators'], scores['pain_points'],
            datetime.now().isoformat(), "1.0"
        ))
        
        conn.commit()
        conn.close()
    
    def score_all_leads(self) -> List[Dict]:
        """Score all leads in the database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM leads')
        lead_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        scored_leads = []
        for lead_id in lead_ids:
            scores = self.score_lead(lead_id)
            if scores:
                scored_leads.append({
                    'lead_id': lead_id,
                    'scores': scores
                })
        
        return scored_leads
    
    def get_top_scored_leads(self, limit: int = 20, min_score: float = 0.6) -> List[Dict]:
        """Get top-scored leads for outreach"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT l.*, ls.total_score, ls.company_size_score, ls.industry_score,
                   ls.digital_maturity_score, ls.contact_quality_score,
                   ls.growth_indicators_score, ls.pain_points_score
            FROM leads l
            JOIN lead_scores ls ON l.id = ls.lead_id
            WHERE ls.total_score >= ?
            ORDER BY ls.total_score DESC
            LIMIT ?
        ''', (min_score, limit))
        
        columns = [desc[0] for desc in cursor.description]
        leads = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return leads
    
    def analyze_scoring_performance(self) -> Dict[str, float]:
        """Analyze scoring performance and accuracy"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Get scoring statistics
        cursor.execute('''
            SELECT 
                AVG(total_score) as avg_score,
                MIN(total_score) as min_score,
                MAX(total_score) as max_score,
                COUNT(*) as total_leads
            FROM lead_scores
        ''')
        
        stats = cursor.fetchone()
        
        # Get score distribution
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN total_score >= 0.8 THEN 1 ELSE 0 END) as high_score,
                SUM(CASE WHEN total_score >= 0.6 AND total_score < 0.8 THEN 1 ELSE 0 END) as medium_score,
                SUM(CASE WHEN total_score < 0.6 THEN 1 ELSE 0 END) as low_score
            FROM lead_scores
        ''')
        
        distribution = cursor.fetchone()
        conn.close()
        
        if stats[3] > 0:  # total_leads > 0
            return {
                'average_score': stats[0],
                'min_score': stats[1],
                'max_score': stats[2],
                'total_leads': stats[3],
                'high_score_percentage': (distribution[0] / stats[3]) * 100,
                'medium_score_percentage': (distribution[1] / stats[3]) * 100,
                'low_score_percentage': (distribution[2] / stats[3]) * 100
            }
        else:
            return {
                'average_score': 0,
                'min_score': 0,
                'max_score': 0,
                'total_leads': 0,
                'high_score_percentage': 0,
                'medium_score_percentage': 0,
                'low_score_percentage': 0
            }
    
    def record_outcome_feedback(self, lead_id: int, outcome: str, notes: str = ""):
        """Record actual outcome for machine learning improvement"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Get the predicted score
        cursor.execute('SELECT total_score FROM lead_scores WHERE lead_id = ?', (lead_id,))
        score_row = cursor.fetchone()
        predicted_score = score_row[0] if score_row else 0.0
        
        cursor.execute('''
            INSERT INTO scoring_feedback (
                lead_id, predicted_score, actual_outcome, feedback_date, notes
            ) VALUES (?, ?, ?, ?, ?)
        ''', (lead_id, predicted_score, outcome, datetime.now().isoformat(), notes))
        
        conn.commit()
        conn.close()
    
    def generate_scoring_report(self) -> str:
        """Generate a comprehensive scoring report"""
        performance = self.analyze_scoring_performance()
        
        report = f"""
LEAD SCORING PERFORMANCE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERALL STATISTICS:
- Total Leads Scored: {performance['total_leads']}
- Average Score: {performance['average_score']:.3f}
- Score Range: {performance['min_score']:.3f} - {performance['max_score']:.3f}

SCORE DISTRIBUTION:
- High Score (≥0.8): {performance['high_score_percentage']:.1f}%
- Medium Score (0.6-0.8): {performance['medium_score_percentage']:.1f}%
- Low Score (<0.6): {performance['low_score_percentage']:.1f}%

SCORING CRITERIA WEIGHTS:
- Company Size: {self.criteria.company_size_weight:.1%}
- Industry Relevance: {self.criteria.industry_relevance_weight:.1%}
- Digital Maturity: {self.criteria.digital_maturity_weight:.1%}
- Contact Quality: {self.criteria.contact_quality_weight:.1%}
- Growth Indicators: {self.criteria.growth_indicators_weight:.1%}
- Pain Points: {self.criteria.pain_points_weight:.1%}
"""
        return report


def main():
    """Main function to demonstrate the lead scoring agent"""
    agent = LeadScoringAgent()
    
    # Score all leads
    print("Scoring all leads...")
    scored_leads = agent.score_all_leads()
    print(f"Scored {len(scored_leads)} leads")
    
    # Get top leads
    top_leads = agent.get_top_scored_leads(10, 0.5)
    print(f"\nTop {len(top_leads)} leads:")
    for lead in top_leads:
        print(f"- {lead['company_name']}: {lead['total_score']:.3f}")
    
    # Generate report
    report = agent.generate_scoring_report()
    print(report)


if __name__ == "__main__":
    main()

