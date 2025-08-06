"""
Lead Qualification Agent - Automated lead qualification and assessment
This agent evaluates leads through automated questionnaires and interactions
"""

import sqlite3
import json
import openai
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import re


class QualificationStatus(Enum):
    """Lead qualification status"""
    UNQUALIFIED = "unqualified"
    QUALIFIED = "qualified"
    HIGHLY_QUALIFIED = "highly_qualified"
    DISQUALIFIED = "disqualified"
    PENDING = "pending"


@dataclass
class QualificationCriteria:
    """Criteria for lead qualification"""
    min_budget: int = 1000  # Minimum monthly budget
    max_budget: int = 50000  # Maximum monthly budget for initial targeting
    target_company_sizes: List[str] = None
    target_industries: List[str] = None
    decision_maker_titles: List[str] = None
    timeline_requirements: List[str] = None
    
    def __post_init__(self):
        if self.target_company_sizes is None:
            self.target_company_sizes = ["small", "medium", "large"]
        if self.target_industries is None:
            self.target_industries = [
                "technology", "e-commerce", "professional_services", 
                "healthcare", "finance", "manufacturing"
            ]
        if self.decision_maker_titles is None:
            self.decision_maker_titles = [
                "ceo", "founder", "owner", "president", "director", 
                "manager", "head", "vp", "chief"
            ]
        if self.timeline_requirements is None:
            self.timeline_requirements = ["immediate", "1-3 months", "3-6 months"]


@dataclass
class QualificationResult:
    """Result of lead qualification process"""
    lead_id: int
    status: QualificationStatus
    score: float
    budget_range: str = ""
    timeline: str = ""
    pain_points: List[str] = None
    decision_maker_info: Dict = None
    qualification_notes: str = ""
    qualification_date: datetime = None
    
    def __post_init__(self):
        if self.pain_points is None:
            self.pain_points = []
        if self.decision_maker_info is None:
            self.decision_maker_info = {}
        if self.qualification_date is None:
            self.qualification_date = datetime.now()


class LeadQualificationAgent:
    """
    AI-powered lead qualification agent that assesses prospect fit
    """
    
    def __init__(self, database_path: str = "leads.db", criteria: QualificationCriteria = None):
        self.database_path = database_path
        self.criteria = criteria or QualificationCriteria()
        self.setup_database()
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI()
        
        # Qualification questions templates
        self.qualification_questions = {
            "budget": [
                "What's your current monthly marketing budget?",
                "How much are you looking to invest in digital marketing monthly?",
                "What budget range are you considering for marketing services?"
            ],
            "timeline": [
                "When are you looking to start with new marketing services?",
                "What's your timeline for implementing marketing improvements?",
                "How urgent is your need for marketing support?"
            ],
            "pain_points": [
                "What are your biggest marketing challenges right now?",
                "What marketing goals are you struggling to achieve?",
                "What's not working with your current marketing efforts?"
            ],
            "decision_making": [
                "Who is involved in marketing decisions at your company?",
                "What's your decision-making process for marketing services?",
                "Are you the primary decision maker for marketing investments?"
            ],
            "current_situation": [
                "Tell me about your current marketing setup",
                "What marketing activities are you currently doing?",
                "How are you currently generating leads?"
            ]
        }
        
        # Response analysis patterns
        self.budget_patterns = {
            r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per month|monthly|/month|pm)': 'monthly',
            r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per year|yearly|annually|/year)': 'yearly',
            r'(\d+)k\s*(?:per month|monthly|/month|pm)': 'monthly_k',
            r'(\d+)k\s*(?:per year|yearly|annually|/year)': 'yearly_k'
        }
        
        self.timeline_patterns = {
            r'immediate|asap|right away|now': 'immediate',
            r'1-3 months|1 to 3 months|within 3 months': '1-3 months',
            r'3-6 months|3 to 6 months|within 6 months': '3-6 months',
            r'6+ months|6 or more months|next year': '6+ months'
        }
    
    def setup_database(self):
        """Initialize database tables for qualification data"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lead_qualifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                status TEXT,
                score REAL,
                budget_range TEXT,
                timeline TEXT,
                pain_points TEXT,
                decision_maker_info TEXT,
                qualification_notes TEXT,
                qualification_date TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qualification_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                question_type TEXT,
                question TEXT,
                response TEXT,
                interaction_date TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_qualification_questions(self, lead_data: Dict, intelligence_data: Dict = None) -> List[Dict]:
        """Generate personalized qualification questions for a lead"""
        questions = []
        
        # Analyze lead data to determine which questions to ask
        company_name = lead_data.get('company_name', '')
        industry = lead_data.get('industry', '')
        
        # Always ask about budget and timeline
        questions.extend([
            {
                'type': 'budget',
                'question': f"Hi {company_name}! I'd love to learn more about your marketing goals. What's your current monthly budget for digital marketing services?",
                'priority': 1
            },
            {
                'type': 'timeline',
                'question': "When are you looking to start with new marketing initiatives?",
                'priority': 1
            }
        ])
        
        # Ask about pain points based on industry
        if industry:
            industry_specific_question = self.get_industry_specific_question(industry)
            questions.append({
                'type': 'pain_points',
                'question': industry_specific_question,
                'priority': 2
            })
        else:
            questions.append({
                'type': 'pain_points',
                'question': "What are your biggest marketing challenges right now?",
                'priority': 2
            })
        
        # Ask about decision making
        questions.append({
            'type': 'decision_making',
            'question': "Are you the primary decision maker for marketing services, or are there others involved in the process?",
            'priority': 2
        })
        
        # Ask about current situation
        questions.append({
            'type': 'current_situation',
            'question': "Could you tell me about your current marketing setup and what's working or not working for you?",
            'priority': 3
        })
        
        return sorted(questions, key=lambda x: x['priority'])
    
    def get_industry_specific_question(self, industry: str) -> str:
        """Get industry-specific qualification questions"""
        industry_questions = {
            'technology': "What are your biggest challenges in reaching and converting technical decision-makers?",
            'e-commerce': "What's your biggest challenge with driving traffic and conversions to your online store?",
            'healthcare': "What marketing challenges do you face in the healthcare industry with compliance and patient acquisition?",
            'finance': "What are your main challenges with lead generation and trust-building in the financial sector?",
            'professional_services': "What's your biggest challenge in establishing thought leadership and generating qualified leads?",
            'manufacturing': "What challenges do you face in reaching B2B buyers and showcasing your capabilities online?"
        }
        
        return industry_questions.get(industry.lower(), 
            "What are your biggest marketing challenges in your industry?")
    
    def analyze_response(self, question_type: str, response: str) -> Dict:
        """Analyze qualification response using AI"""
        analysis_prompt = f"""
        Analyze this qualification response for a digital marketing prospect:
        
        Question Type: {question_type}
        Response: "{response}"
        
        Extract the following information:
        1. Key insights about their needs/situation
        2. Budget information (if mentioned)
        3. Timeline information (if mentioned)
        4. Pain points mentioned
        5. Decision-making authority indicators
        6. Qualification score (1-10, where 10 is highly qualified)
        
        Return your analysis in JSON format with keys: insights, budget, timeline, pain_points, decision_authority, score, notes
        """
        
        try:
            response_obj = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert sales qualification analyst. Analyze prospect responses and extract key qualification information."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3
            )
            
            analysis_text = response_obj.choices[0].message.content
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback analysis
                return self.fallback_response_analysis(question_type, response)
                
        except Exception as e:
            print(f"Error analyzing response with AI: {str(e)}")
            return self.fallback_response_analysis(question_type, response)
    
    def fallback_response_analysis(self, question_type: str, response: str) -> Dict:
        """Fallback response analysis using pattern matching"""
        analysis = {
            'insights': [],
            'budget': '',
            'timeline': '',
            'pain_points': [],
            'decision_authority': '',
            'score': 5,
            'notes': ''
        }
        
        response_lower = response.lower()
        
        # Budget analysis
        if question_type == 'budget':
            for pattern, period in self.budget_patterns.items():
                match = re.search(pattern, response_lower)
                if match:
                    amount = match.group(1)
                    if period == 'monthly':
                        analysis['budget'] = f"${amount}/month"
                    elif period == 'yearly':
                        analysis['budget'] = f"${amount}/year"
                    elif period == 'monthly_k':
                        analysis['budget'] = f"${int(amount)*1000}/month"
                    elif period == 'yearly_k':
                        analysis['budget'] = f"${int(amount)*1000}/year"
                    break
        
        # Timeline analysis
        if question_type == 'timeline':
            for pattern, timeline in self.timeline_patterns.items():
                if re.search(pattern, response_lower):
                    analysis['timeline'] = timeline
                    break
        
        # Pain points analysis
        if question_type == 'pain_points':
            pain_keywords = {
                'lead generation': ['leads', 'lead generation', 'prospects'],
                'traffic': ['traffic', 'visitors', 'website visits'],
                'conversions': ['conversions', 'sales', 'closing'],
                'brand awareness': ['brand', 'awareness', 'visibility'],
                'competition': ['competition', 'competitors', 'market share']
            }
            
            for pain_point, keywords in pain_keywords.items():
                if any(keyword in response_lower for keyword in keywords):
                    analysis['pain_points'].append(pain_point)
        
        # Decision authority analysis
        if question_type == 'decision_making':
            if any(phrase in response_lower for phrase in ['i am', 'i make', 'my decision']):
                analysis['decision_authority'] = 'primary'
            elif any(phrase in response_lower for phrase in ['team', 'committee', 'others']):
                analysis['decision_authority'] = 'committee'
            else:
                analysis['decision_authority'] = 'unknown'
        
        return analysis
    
    def qualify_lead(self, lead_id: int) -> QualificationResult:
        """Qualify a single lead through automated assessment"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Get lead data
        cursor.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
        lead_row = cursor.fetchone()
        
        if not lead_row:
            conn.close()
            return None
        
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
        
        conn.close()
        
        # Generate qualification questions
        questions = self.generate_qualification_questions(lead_data, intelligence_data)
        
        # Simulate responses for demonstration (in production, these would come from actual interactions)
        simulated_responses = self.simulate_qualification_responses(lead_data)
        
        # Analyze responses and calculate qualification score
        qualification_score = 0.0
        budget_range = ""
        timeline = ""
        pain_points = []
        decision_maker_info = {}
        notes = []
        
        for i, question in enumerate(questions):
            if i < len(simulated_responses):
                response = simulated_responses[i]
                analysis = self.analyze_response(question['type'], response)
                
                # Store interaction
                self.save_qualification_interaction(lead_id, question['type'], question['question'], response)
                
                # Update qualification data
                if analysis.get('budget'):
                    budget_range = analysis['budget']
                if analysis.get('timeline'):
                    timeline = analysis['timeline']
                if analysis.get('pain_points'):
                    pain_points.extend(analysis['pain_points'])
                if analysis.get('decision_authority'):
                    decision_maker_info['authority'] = analysis['decision_authority']
                
                # Add to qualification score
                qualification_score += analysis.get('score', 5) / 10.0
                notes.append(f"{question['type']}: {analysis.get('notes', 'No specific notes')}")
        
        # Normalize score
        qualification_score = qualification_score / len(questions) if questions else 0.0
        
        # Determine qualification status
        status = self.determine_qualification_status(qualification_score, budget_range, timeline)
        
        # Create qualification result
        result = QualificationResult(
            lead_id=lead_id,
            status=status,
            score=qualification_score,
            budget_range=budget_range,
            timeline=timeline,
            pain_points=pain_points,
            decision_maker_info=decision_maker_info,
            qualification_notes="; ".join(notes)
        )
        
        # Save qualification result
        self.save_qualification_result(result)
        
        return result
    
    def simulate_qualification_responses(self, lead_data: Dict) -> List[str]:
        """Simulate qualification responses for demonstration"""
        company_name = lead_data.get('company_name', 'Company')
        industry = lead_data.get('industry', 'business')
        
        # Generate realistic responses based on company data
        responses = [
            f"We're currently spending around $3,000 per month on various marketing activities, but we're looking to increase that to around $5,000-7,000 for the right services.",
            "We'd like to start within the next 2-3 months. We're planning our Q4 marketing push.",
            f"Our biggest challenge is generating qualified leads. We get website traffic but the conversion rate is low, and we're struggling to reach decision-makers in the {industry} space.",
            "I'm the marketing director and I make most of the marketing decisions, though I do need to get approval from the CEO for larger investments over $10k.",
            "Right now we're doing some social media posting, Google Ads, and email newsletters, but nothing is really integrated or optimized. We know we need a more strategic approach."
        ]
        
        return responses
    
    def determine_qualification_status(self, score: float, budget_range: str, timeline: str) -> QualificationStatus:
        """Determine qualification status based on score and criteria"""
        # Extract budget amount for comparison
        budget_amount = self.extract_budget_amount(budget_range)
        
        # Check disqualification criteria
        if budget_amount and budget_amount < self.criteria.min_budget:
            return QualificationStatus.DISQUALIFIED
        
        if timeline and timeline == '6+ months':
            return QualificationStatus.DISQUALIFIED
        
        # Determine qualification level
        if score >= 0.8 and budget_amount and budget_amount >= self.criteria.min_budget * 2:
            return QualificationStatus.HIGHLY_QUALIFIED
        elif score >= 0.6 and budget_amount and budget_amount >= self.criteria.min_budget:
            return QualificationStatus.QUALIFIED
        elif score >= 0.4:
            return QualificationStatus.PENDING
        else:
            return QualificationStatus.UNQUALIFIED
    
    def extract_budget_amount(self, budget_range: str) -> Optional[int]:
        """Extract numeric budget amount from budget range string"""
        if not budget_range:
            return None
        
        # Extract numbers from budget string
        numbers = re.findall(r'\d+(?:,\d{3})*', budget_range.replace('$', '').replace(',', ''))
        if numbers:
            amount = int(numbers[0])
            
            # Convert yearly to monthly if needed
            if '/year' in budget_range or 'yearly' in budget_range:
                amount = amount // 12
            
            return amount
        
        return None
    
    def save_qualification_interaction(self, lead_id: int, question_type: str, question: str, response: str):
        """Save qualification interaction to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO qualification_interactions (
                lead_id, question_type, question, response, interaction_date
            ) VALUES (?, ?, ?, ?, ?)
        ''', (lead_id, question_type, question, response, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def save_qualification_result(self, result: QualificationResult):
        """Save qualification result to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO lead_qualifications (
                lead_id, status, score, budget_range, timeline,
                pain_points, decision_maker_info, qualification_notes, qualification_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.lead_id, result.status.value, result.score, result.budget_range,
            result.timeline, json.dumps(result.pain_points),
            json.dumps(result.decision_maker_info), result.qualification_notes,
            result.qualification_date.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_qualified_leads(self, status: QualificationStatus = None, limit: int = 50) -> List[Dict]:
        """Get qualified leads from database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT l.*, lq.* FROM leads l
                JOIN lead_qualifications lq ON l.id = lq.lead_id
                WHERE lq.status = ?
                ORDER BY lq.score DESC
                LIMIT ?
            ''', (status.value, limit))
        else:
            cursor.execute('''
                SELECT l.*, lq.* FROM leads l
                JOIN lead_qualifications lq ON l.id = lq.lead_id
                WHERE lq.status IN ('qualified', 'highly_qualified')
                ORDER BY lq.score DESC
                LIMIT ?
            ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        leads = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return leads
    
    def generate_qualification_report(self) -> str:
        """Generate qualification performance report"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Get qualification statistics
        cursor.execute('''
            SELECT 
                status,
                COUNT(*) as count,
                AVG(score) as avg_score
            FROM lead_qualifications
            GROUP BY status
        ''')
        
        stats = cursor.fetchall()
        
        # Get total qualified leads
        cursor.execute('''
            SELECT COUNT(*) FROM lead_qualifications 
            WHERE status IN ('qualified', 'highly_qualified')
        ''')
        
        total_qualified = cursor.fetchone()[0]
        
        conn.close()
        
        report = f"""
LEAD QUALIFICATION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

QUALIFICATION STATISTICS:
"""
        
        for status, count, avg_score in stats:
            report += f"- {status.title()}: {count} leads (Avg Score: {avg_score:.2f})\n"
        
        report += f"\nTOTAL QUALIFIED LEADS: {total_qualified}\n"
        
        return report


def main():
    """Main function to demonstrate the lead qualification agent"""
    agent = LeadQualificationAgent()
    
    # Get leads to qualify
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM leads LIMIT 3')
    lead_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Qualify leads
    for lead_id in lead_ids:
        print(f"Qualifying lead {lead_id}...")
        result = agent.qualify_lead(lead_id)
        if result:
            print(f"- Status: {result.status.value}")
            print(f"- Score: {result.score:.2f}")
            print(f"- Budget: {result.budget_range}")
            print(f"- Timeline: {result.timeline}")
            print(f"- Pain Points: {', '.join(result.pain_points)}")
            print()
    
    # Get qualified leads
    qualified_leads = agent.get_qualified_leads()
    print(f"Found {len(qualified_leads)} qualified leads")
    
    # Generate report
    report = agent.generate_qualification_report()
    print(report)


if __name__ == "__main__":
    main()

