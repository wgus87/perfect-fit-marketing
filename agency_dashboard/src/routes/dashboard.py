"""
Dashboard API routes for the AI Agency management system
"""

from flask import Blueprint, jsonify, request
import sqlite3
import json
from datetime import datetime, timedelta
import os

dashboard_bp = Blueprint('dashboard', __name__)

# Database path - using the main agency database
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'leads.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@dashboard_bp.route('/overview', methods=['GET'])
def get_overview():
    """Get agency overview metrics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Lead metrics
        cursor.execute('SELECT COUNT(*) as total_leads FROM leads')
        total_leads = cursor.fetchone()['total_leads']
        
        cursor.execute('SELECT COUNT(*) as qualified_leads FROM lead_qualifications WHERE status IN ("qualified", "highly_qualified")')
        qualified_leads = cursor.fetchone()['qualified_leads']
        
        # Sales metrics
        cursor.execute('SELECT COUNT(*) as active_deals, SUM(value) as pipeline_value FROM sales_deals WHERE stage NOT IN ("closed_won", "closed_lost")')
        sales_data = cursor.fetchone()
        active_deals = sales_data['active_deals'] or 0
        pipeline_value = sales_data['pipeline_value'] or 0
        
        cursor.execute('SELECT COUNT(*) as won_deals, SUM(value) as won_value FROM sales_deals WHERE stage = "closed_won"')
        won_data = cursor.fetchone()
        won_deals = won_data['won_deals'] or 0
        won_value = won_data['won_value'] or 0
        
        # Client metrics
        cursor.execute('SELECT COUNT(*) as active_clients, SUM(monthly_value) as monthly_revenue FROM clients WHERE status IN ("onboarding", "active")')
        client_data = cursor.fetchone()
        active_clients = client_data['active_clients'] or 0
        monthly_revenue = client_data['monthly_revenue'] or 0
        
        # Outreach metrics
        cursor.execute('SELECT COUNT(*) as total_sent FROM outreach_messages WHERE status = "sent"')
        total_outreach = cursor.fetchone()['total_sent'] or 0
        
        cursor.execute('SELECT COUNT(*) as total_replied FROM outreach_messages WHERE status = "replied"')
        total_replies = cursor.fetchone()['total_replied'] or 0
        
        conn.close()
        
        # Calculate conversion rates
        lead_conversion_rate = (qualified_leads / total_leads * 100) if total_leads > 0 else 0
        deal_conversion_rate = (won_deals / (won_deals + active_deals) * 100) if (won_deals + active_deals) > 0 else 0
        outreach_response_rate = (total_replies / total_outreach * 100) if total_outreach > 0 else 0
        
        return jsonify({
            'leads': {
                'total': total_leads,
                'qualified': qualified_leads,
                'conversion_rate': round(lead_conversion_rate, 1)
            },
            'sales': {
                'active_deals': active_deals,
                'pipeline_value': pipeline_value,
                'won_deals': won_deals,
                'won_value': won_value,
                'conversion_rate': round(deal_conversion_rate, 1)
            },
            'clients': {
                'active': active_clients,
                'monthly_revenue': monthly_revenue,
                'annual_revenue': monthly_revenue * 12
            },
            'outreach': {
                'total_sent': total_outreach,
                'total_replies': total_replies,
                'response_rate': round(outreach_response_rate, 1)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/leads', methods=['GET'])
def get_leads():
    """Get leads data with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with filters
        query = '''
            SELECT l.*, ls.total_score, lq.status as qualification_status, lq.budget_range
            FROM leads l
            LEFT JOIN lead_scores ls ON l.id = ls.lead_id
            LEFT JOIN lead_qualifications lq ON l.id = lq.lead_id
        '''
        
        params = []
        if status:
            query += ' WHERE lq.status = ?'
            params.append(status)
        
        query += ' ORDER BY ls.total_score DESC, l.id DESC'
        query += f' LIMIT {per_page} OFFSET {(page - 1) * per_page}'
        
        cursor.execute(query, params)
        leads = [dict(row) for row in cursor.fetchall()]
        
        # Get total count
        count_query = 'SELECT COUNT(*) as total FROM leads l LEFT JOIN lead_qualifications lq ON l.id = lq.lead_id'
        if status:
            count_query += ' WHERE lq.status = ?'
            cursor.execute(count_query, params)
        else:
            cursor.execute(count_query)
        
        total = cursor.fetchone()['total']
        
        conn.close()
        
        return jsonify({
            'leads': leads,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/pipeline', methods=['GET'])
def get_pipeline():
    """Get sales pipeline data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sd.*, l.company_name, l.contact_name, sp.monthly_price
            FROM sales_deals sd
            JOIN leads l ON sd.lead_id = l.id
            LEFT JOIN sales_proposals sp ON sd.proposal_id = sp.proposal_id
            WHERE sd.stage NOT IN ('closed_won', 'closed_lost')
            ORDER BY sd.probability DESC, sd.value DESC
        ''')
        
        pipeline = [dict(row) for row in cursor.fetchall()]
        
        # Get stage distribution
        cursor.execute('''
            SELECT stage, COUNT(*) as count, SUM(value) as total_value
            FROM sales_deals
            WHERE stage NOT IN ('closed_won', 'closed_lost')
            GROUP BY stage
        ''')
        
        stage_distribution = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'pipeline': pipeline,
            'stage_distribution': stage_distribution
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/clients', methods=['GET'])
def get_clients():
    """Get clients data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM clients
            WHERE status IN ('onboarding', 'active')
            ORDER BY start_date DESC
        ''')
        
        clients = [dict(row) for row in cursor.fetchall()]
        
        # Get package distribution
        cursor.execute('''
            SELECT package, COUNT(*) as count, SUM(monthly_value) as revenue
            FROM clients
            WHERE status IN ('onboarding', 'active')
            GROUP BY package
        ''')
        
        package_distribution = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'clients': clients,
            'package_distribution': package_distribution
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data for charts"""
    try:
        period = request.args.get('period', '30d')  # 7d, 30d, 90d
        
        # Calculate date range
        if period == '7d':
            days = 7
        elif period == '90d':
            days = 90
        else:
            days = 30
        
        start_date = datetime.now() - timedelta(days=days)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Lead generation over time (simulated data for demo)
        lead_data = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            # Simulate lead generation data
            leads_count = max(0, int(5 + (i % 7) * 2 + (i % 3)))
            lead_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'leads': leads_count,
                'qualified': max(0, leads_count - 2)
            })
        
        # Revenue over time (simulated)
        revenue_data = []
        cumulative_revenue = 0
        for i in range(days):
            date = start_date + timedelta(days=i)
            daily_revenue = max(0, int(1000 + (i % 10) * 500))
            cumulative_revenue += daily_revenue
            revenue_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'daily_revenue': daily_revenue,
                'cumulative_revenue': cumulative_revenue
            })
        
        # Outreach performance
        cursor.execute('''
            SELECT channel, status, COUNT(*) as count
            FROM outreach_messages
            GROUP BY channel, status
        ''')
        
        outreach_data = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'lead_generation': lead_data,
            'revenue': revenue_data,
            'outreach_performance': outreach_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/agent-performance', methods=['GET'])
def get_agent_performance():
    """Get AI agent performance metrics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Lead generation agent performance
        cursor.execute('SELECT COUNT(*) as total_leads FROM leads WHERE source = "business_directory"')
        lead_gen_performance = cursor.fetchone()['total_leads'] or 0
        
        # Qualification agent performance
        cursor.execute('SELECT COUNT(*) as qualified FROM lead_qualifications WHERE status IN ("qualified", "highly_qualified")')
        qualification_performance = cursor.fetchone()['qualified'] or 0
        
        # Outreach agent performance
        cursor.execute('SELECT COUNT(*) as sent FROM outreach_messages WHERE status = "sent"')
        outreach_performance = cursor.fetchone()['sent'] or 0
        
        # Sales agent performance
        cursor.execute('SELECT COUNT(*) as proposals FROM sales_proposals')
        sales_performance = cursor.fetchone()['proposals'] or 0
        
        # Client management performance
        cursor.execute('SELECT COUNT(*) as active_clients FROM clients WHERE status = "active"')
        client_performance = cursor.fetchone()['active_clients'] or 0
        
        conn.close()
        
        agent_metrics = [
            {
                'name': 'Lead Generation Agent',
                'metric': 'Leads Generated',
                'value': lead_gen_performance,
                'status': 'active',
                'efficiency': 85
            },
            {
                'name': 'Qualification Agent',
                'metric': 'Leads Qualified',
                'value': qualification_performance,
                'status': 'active',
                'efficiency': 78
            },
            {
                'name': 'Outreach Agent',
                'metric': 'Messages Sent',
                'value': outreach_performance,
                'status': 'active',
                'efficiency': 92
            },
            {
                'name': 'Sales Agent',
                'metric': 'Proposals Created',
                'value': sales_performance,
                'status': 'active',
                'efficiency': 88
            },
            {
                'name': 'Client Management Agent',
                'metric': 'Active Clients',
                'value': client_performance,
                'status': 'active',
                'efficiency': 95
            }
        ]
        
        return jsonify({'agents': agent_metrics})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """Get current tasks and activities"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get service tasks
        cursor.execute('''
            SELECT st.*, c.company_name
            FROM service_tasks st
            JOIN clients c ON st.client_id = c.client_id
            WHERE st.status IN ('pending', 'in_progress')
            ORDER BY st.due_date ASC
            LIMIT 20
        ''')
        
        tasks = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({'tasks': tasks})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

