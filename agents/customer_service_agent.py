"""
Customer Service Agent - Automated client communication and support management
Handles user-friendly contact methods and client gratitude messages
"""

import sqlite3
import logging
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import sys

# Add parent directory to path to import API modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class ContactRequest:
    """Represents a customer contact request"""
    id: Optional[int] = None
    client_id: Optional[int] = None
    contact_method: str = ""  # email, chat, phone, form
    subject: str = ""
    message: str = ""
    priority: str = "medium"  # low, medium, high, urgent
    status: str = "open"  # open, in_progress, resolved, closed
    assigned_to: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    client_email: str = ""
    client_name: str = ""


@dataclass
class GratitudeMessage:
    """Represents a gratitude message to be sent"""
    id: Optional[int] = None
    client_id: int = 0
    message_type: str = ""  # welcome, milestone, completion, referral, holiday
    trigger_event: str = ""
    message_content: str = ""
    delivery_method: str = "email"  # email, dashboard, sms
    scheduled_date: Optional[datetime] = None
    sent_date: Optional[datetime] = None
    status: str = "pending"  # pending, sent, failed
    personalization_data: str = "{}"


@dataclass
class ClientCommunication:
    """Tracks all communication with a client"""
    id: Optional[int] = None
    client_id: int = 0
    communication_type: str = ""  # inbound, outbound, automated
    method: str = ""  # email, chat, phone, dashboard
    subject: str = ""
    content: str = ""
    timestamp: Optional[datetime] = None
    agent_id: Optional[str] = None
    response_time_minutes: Optional[int] = None


class CustomerServiceAgent:
    """
    AI-powered customer service agent that manages client communications,
    handles support requests, and sends automated gratitude messages
    """
    
    def __init__(self, database_path: str = "leads.db", log_directory: str = "logs"):
        self.database_path = database_path
        self.log_directory = log_directory
        self.logger = logging.getLogger(__name__)
        
        # Service configuration
        self.config = {
            'response_time_targets': {
                'urgent': 15,      # minutes
                'high': 60,        # minutes
                'medium': 240,     # minutes (4 hours)
                'low': 1440        # minutes (24 hours)
            },
            'business_hours': {
                'start': 9,        # 9 AM
                'end': 17,         # 5 PM
                'timezone': 'UTC'
            },
            'auto_response_enabled': True,
            'gratitude_message_enabled': True,
            'escalation_threshold_hours': 24
        }
        
        # Message templates
        self.message_templates = self.load_message_templates()
        
        self.setup_logging()
        self.setup_database()
    
    def setup_logging(self):
        """Setup logging for the customer service agent"""
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)
        
        log_file = os.path.join(self.log_directory, "customer_service.log")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def setup_database(self):
        """Setup database tables for customer service operations"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Contact requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                contact_method TEXT NOT NULL,
                subject TEXT,
                message TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'open',
                assigned_to TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT,
                client_email TEXT,
                client_name TEXT,
                FOREIGN KEY (client_id) REFERENCES leads (id)
            )
        ''')
        
        # Gratitude messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gratitude_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                message_type TEXT NOT NULL,
                trigger_event TEXT,
                message_content TEXT,
                delivery_method TEXT DEFAULT 'email',
                scheduled_date TEXT,
                sent_date TEXT,
                status TEXT DEFAULT 'pending',
                personalization_data TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES leads (id)
            )
        ''')
        
        # Client communications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_communications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                communication_type TEXT NOT NULL,
                contact_method TEXT NOT NULL,
                subject TEXT,
                content TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                agent_id TEXT,
                response_time_minutes INTEGER,
                FOREIGN KEY (client_id) REFERENCES leads (id)
            )
        ''')
        
        # Customer service metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_service_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_date TEXT NOT NULL,
                total_requests INTEGER DEFAULT 0,
                resolved_requests INTEGER DEFAULT 0,
                avg_response_time_minutes REAL DEFAULT 0,
                satisfaction_score REAL DEFAULT 0,
                gratitude_messages_sent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_message_templates(self) -> Dict[str, Dict[str, str]]:
        """Load message templates for automated responses and gratitude messages"""
        return {
            'auto_responses': {
                'acknowledgment': """
                Dear {client_name},
                
                Thank you for contacting us. We have received your message regarding "{subject}" and will respond within {response_time}.
                
                Your request has been assigned reference number: {request_id}
                
                If this is an urgent matter, please call our support line or mark your request as urgent.
                
                Best regards,
                AI Marketing Agency Support Team
                """,
                'resolution': """
                Dear {client_name},
                
                We're pleased to inform you that your support request #{request_id} regarding "{subject}" has been resolved.
                
                Resolution Summary:
                {resolution_summary}
                
                If you have any questions or need further assistance, please don't hesitate to contact us.
                
                Thank you for choosing AI Marketing Agency.
                
                Best regards,
                Support Team
                """
            },
            'gratitude_messages': {
                'welcome': """
                Dear {client_name},
                
                Welcome to AI Marketing Agency! We're thrilled to have you as our newest client.
                
                We want to express our sincere gratitude for choosing us to help grow your business. Your trust in our services means everything to us, and we're committed to delivering exceptional results for {company_name}.
                
                Over the next few days, our AI agents will begin working on your campaigns, and you'll start seeing the power of automated marketing in action. You can track all progress through your dedicated dashboard.
                
                If you have any questions or need assistance, our customer service team is here to help. We're excited about this partnership and look forward to celebrating your success!
                
                Warm regards,
                The AI Marketing Agency Team
                """,
                'milestone': """
                Dear {client_name},
                
                Congratulations! Today marks {milestone_description} with AI Marketing Agency, and we wanted to take a moment to celebrate this achievement with you.
                
                During our partnership, we've accomplished:
                {achievements_summary}
                
                Your success is our success, and we're grateful for the opportunity to be part of your growth journey. Thank you for your continued trust in our services.
                
                Here's to many more milestones ahead!
                
                With appreciation,
                The AI Marketing Agency Team
                """,
                'completion': """
                Dear {client_name},
                
                We're excited to share that your {campaign_type} campaign has been successfully completed!
                
                Campaign Results:
                {results_summary}
                
                Thank you for your collaboration throughout this campaign. Your input and feedback were invaluable in achieving these outstanding results.
                
                We're already looking forward to our next project together. If you'd like to discuss expanding your marketing efforts or have any questions about these results, please don't hesitate to reach out.
                
                Gratefully yours,
                The AI Marketing Agency Team
                """,
                'referral': """
                Dear {client_name},
                
                Thank you so much for referring {referred_client} to AI Marketing Agency! Your recommendation means the world to us.
                
                There's no greater compliment than a client who trusts us enough to recommend our services to their network. Your referral is a testament to the partnership we've built together.
                
                As a token of our appreciation, we've applied a {referral_bonus} credit to your account, which will be reflected in your next invoice.
                
                Thank you again for being such a valued client and advocate for our services.
                
                With heartfelt gratitude,
                The AI Marketing Agency Team
                """,
                'holiday': """
                Dear {client_name},
                
                As we celebrate {holiday_name}, we wanted to take a moment to express our gratitude for your partnership with AI Marketing Agency.
                
                This year has been filled with achievements, growth, and success stories - and you've been an integral part of that journey. Thank you for trusting us with your marketing needs and for being such a wonderful client to work with.
                
                We wish you and your team at {company_name} a {holiday_wish}. May the coming year bring continued prosperity and success to your business.
                
                With warm wishes and appreciation,
                The AI Marketing Agency Team
                """
            }
        }
    
    def create_contact_request(self, contact_data: Dict[str, Any]) -> int:
        """Create a new contact request from client communication"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            # Determine priority based on keywords and urgency indicators
            priority = self._determine_priority(contact_data.get('message', ''), contact_data.get('subject', ''))
            
            cursor.execute('''
                INSERT INTO contact_requests (
                    client_id, contact_method, subject, message, priority,
                    client_email, client_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                contact_data.get('client_id'),
                contact_data.get('contact_method', 'email'),
                contact_data.get('subject', ''),
                contact_data.get('message', ''),
                priority,
                contact_data.get('client_email', ''),
                contact_data.get('client_name', '')
            ))
            
            request_id = cursor.lastrowid
            
            # Log the communication
            self._log_communication(
                client_id=contact_data.get('client_id'),
                communication_type='inbound',
                method=contact_data.get('contact_method', 'email'),
                subject=contact_data.get('subject', ''),
                content=contact_data.get('message', '')
            )
            
            # Send auto-acknowledgment if enabled
            if self.config['auto_response_enabled']:
                self._send_acknowledgment(request_id, contact_data)
            
            conn.commit()
            self.logger.info(f"Created contact request {request_id} with priority {priority}")
            
            return request_id
            
        except Exception as e:
            self.logger.error(f"Error creating contact request: {str(e)}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    def _determine_priority(self, message: str, subject: str) -> str:
        """Determine priority level based on message content"""
        urgent_keywords = ['urgent', 'emergency', 'critical', 'asap', 'immediately', 'broken', 'down', 'not working']
        high_keywords = ['important', 'priority', 'soon', 'issue', 'problem', 'error', 'bug']
        
        text = (message + ' ' + subject).lower()
        
        if any(keyword in text for keyword in urgent_keywords):
            return 'urgent'
        elif any(keyword in text for keyword in high_keywords):
            return 'high'
        else:
            return 'medium'
    
    def _send_acknowledgment(self, request_id: int, contact_data: Dict[str, Any]):
        """Send automated acknowledgment message"""
        try:
            priority = self._get_request_priority(request_id)
            response_time = self._get_response_time_estimate(priority)
            
            template = self.message_templates['auto_responses']['acknowledgment']
            message = template.format(
                client_name=contact_data.get('client_name', 'Valued Client'),
                subject=contact_data.get('subject', 'your inquiry'),
                response_time=response_time,
                request_id=request_id
            )
            
            # In a real implementation, this would send an actual email
            self.logger.info(f"Acknowledgment sent for request {request_id}")
            
            # Log the outbound communication
            self._log_communication(
                client_id=contact_data.get('client_id'),
                communication_type='outbound',
                method='email',
                subject=f"Re: {contact_data.get('subject', 'Your inquiry')} - Request #{request_id}",
                content=message,
                agent_id='auto_response_system'
            )
            
        except Exception as e:
            self.logger.error(f"Error sending acknowledgment for request {request_id}: {str(e)}")
    
    def _get_request_priority(self, request_id: int) -> str:
        """Get priority level for a request"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT priority FROM contact_requests WHERE id = ?', (request_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 'medium'
    
    def _get_response_time_estimate(self, priority: str) -> str:
        """Get response time estimate based on priority"""
        target_minutes = self.config['response_time_targets'].get(priority, 240)
        
        if target_minutes < 60:
            return f"{target_minutes} minutes"
        elif target_minutes < 1440:
            hours = target_minutes // 60
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            days = target_minutes // 1440
            return f"{days} business day{'s' if days > 1 else ''}"
    
    def process_contact_requests(self) -> Dict[str, Any]:
        """Process pending contact requests and manage responses"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        results = {
            'processed_requests': 0,
            'escalated_requests': 0,
            'auto_resolved_requests': 0
        }
        
        try:
            # Get open requests that need attention
            cursor.execute('''
                SELECT id, client_id, contact_method, subject, message, priority, 
                       created_at, client_email, client_name
                FROM contact_requests 
                WHERE status = 'open'
                ORDER BY 
                    CASE priority 
                        WHEN 'urgent' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 3 
                        ELSE 4 
                    END,
                    created_at ASC
            ''')
            
            requests = cursor.fetchall()
            
            for request in requests:
                request_id, client_id, method, subject, message, priority, created_at, email, name = request
                
                # Check if request needs escalation
                created_time = datetime.fromisoformat(created_at)
                hours_old = (datetime.now() - created_time).total_seconds() / 3600
                
                if hours_old > self.config['escalation_threshold_hours']:
                    self._escalate_request(request_id)
                    results['escalated_requests'] += 1
                else:
                    # Try to auto-resolve common requests
                    if self._attempt_auto_resolution(request_id, subject, message):
                        results['auto_resolved_requests'] += 1
                    else:
                        # Mark as in progress for human/advanced AI handling
                        self._update_request_status(request_id, 'in_progress')
                
                results['processed_requests'] += 1
            
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error processing contact requests: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
        
        return results
    
    def _attempt_auto_resolution(self, request_id: int, subject: str, message: str) -> bool:
        """Attempt to automatically resolve common requests"""
        # Simple keyword-based auto-resolution for common queries
        auto_resolvable_keywords = {
            'password': 'Password reset instructions have been sent to your email.',
            'login': 'Please check your login credentials and try again. If issues persist, contact support.',
            'dashboard': 'Dashboard access issues are typically resolved by clearing your browser cache.',
            'report': 'Your latest reports are available in the Reports section of your dashboard.',
            'billing': 'Billing inquiries have been forwarded to our accounts team for review.'
        }
        
        text = (subject + ' ' + message).lower()
        
        for keyword, resolution in auto_resolvable_keywords.items():
            if keyword in text:
                self._resolve_request(request_id, resolution, 'auto_resolution_system')
                return True
        
        return False
    
    def _escalate_request(self, request_id: int):
        """Escalate a request that has been open too long"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE contact_requests 
            SET status = 'escalated', updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (request_id,))
        
        conn.commit()
        conn.close()
        
        self.logger.warning(f"Request {request_id} escalated due to timeout")
    
    def _update_request_status(self, request_id: int, status: str):
        """Update the status of a contact request"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE contact_requests 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (status, request_id))
        
        conn.commit()
        conn.close()
    
    def _resolve_request(self, request_id: int, resolution: str, agent_id: str):
        """Mark a request as resolved and send resolution message"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            # Update request status
            cursor.execute('''
                UPDATE contact_requests 
                SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP, 
                    updated_at = CURRENT_TIMESTAMP, assigned_to = ?
                WHERE id = ?
            ''', (agent_id, request_id))
            
            # Get request details for resolution message
            cursor.execute('''
                SELECT client_id, subject, client_email, client_name 
                FROM contact_requests WHERE id = ?
            ''', (request_id,))
            
            request_data = cursor.fetchone()
            if request_data:
                client_id, subject, email, name = request_data
                
                # Send resolution message
                template = self.message_templates['auto_responses']['resolution']
                message = template.format(
                    client_name=name or 'Valued Client',
                    request_id=request_id,
                    subject=subject or 'your inquiry',
                    resolution_summary=resolution
                )
                
                # Log the resolution communication
                self._log_communication(
                    client_id=client_id,
                    communication_type='outbound',
                    method='email',
                    subject=f"Resolved: {subject} - Request #{request_id}",
                    content=message,
                    agent_id=agent_id
                )
            
            conn.commit()
            self.logger.info(f"Request {request_id} resolved by {agent_id}")
            
        except Exception as e:
            self.logger.error(f"Error resolving request {request_id}: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    
    def schedule_gratitude_message(self, client_id: int, message_type: str, 
                                 trigger_event: str, personalization_data: Dict[str, Any] = None) -> int:
        """Schedule a gratitude message for a client"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            # Get client information
            cursor.execute('SELECT company_name, contact_name FROM leads WHERE id = ?', (client_id,))
            client_data = cursor.fetchone()
            
            if not client_data:
                self.logger.error(f"Client {client_id} not found")
                return -1
            
            company_name, contact_name = client_data
            
            # Prepare personalization data
            if personalization_data is None:
                personalization_data = {}
            
            personalization_data.update({
                'client_name': contact_name or 'Valued Client',
                'company_name': company_name or 'Your Company'
            })
            
            # Generate message content
            message_content = self._generate_gratitude_message(message_type, personalization_data)
            
            # Schedule the message (immediate for now, could be delayed)
            scheduled_date = datetime.now()
            
            cursor.execute('''
                INSERT INTO gratitude_messages (
                    client_id, message_type, trigger_event, message_content,
                    scheduled_date, personalization_data
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                client_id, message_type, trigger_event, message_content,
                scheduled_date.isoformat(), json.dumps(personalization_data)
            ))
            
            message_id = cursor.lastrowid
            conn.commit()
            
            self.logger.info(f"Scheduled {message_type} gratitude message {message_id} for client {client_id}")
            return message_id
            
        except Exception as e:
            self.logger.error(f"Error scheduling gratitude message: {str(e)}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    def _generate_gratitude_message(self, message_type: str, personalization_data: Dict[str, Any]) -> str:
        """Generate personalized gratitude message content"""
        template = self.message_templates['gratitude_messages'].get(message_type, '')
        
        if not template:
            self.logger.error(f"No template found for message type: {message_type}")
            return f"Thank you for being a valued client, {personalization_data.get('client_name', 'Valued Client')}!"
        
        try:
            return template.format(**personalization_data)
        except KeyError as e:
            self.logger.error(f"Missing personalization data for template: {str(e)}")
            # Return template with minimal personalization
            return template.format(
                client_name=personalization_data.get('client_name', 'Valued Client'),
                company_name=personalization_data.get('company_name', 'Your Company'),
                **{k: f"[{k}]" for k in personalization_data.keys()}
            )
    
    def process_gratitude_messages(self) -> Dict[str, Any]:
        """Process and send pending gratitude messages"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        results = {
            'messages_sent': 0,
            'messages_failed': 0,
            'messages_processed': 0
        }
        
        try:
            # Get pending messages that are due
            cursor.execute('''
                SELECT id, client_id, message_type, message_content, delivery_method
                FROM gratitude_messages 
                WHERE status = 'pending' 
                AND scheduled_date <= CURRENT_TIMESTAMP
                ORDER BY scheduled_date ASC
            ''')
            
            messages = cursor.fetchall()
            
            for message in messages:
                message_id, client_id, msg_type, content, delivery_method = message
                
                try:
                    # Send the message (in real implementation, this would use actual email/SMS services)
                    success = self._send_gratitude_message(client_id, content, delivery_method)
                    
                    if success:
                        # Update message status
                        cursor.execute('''
                            UPDATE gratitude_messages 
                            SET status = 'sent', sent_date = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        ''', (message_id,))
                        
                        # Log the communication
                        self._log_communication(
                            client_id=client_id,
                            communication_type='outbound',
                            method=delivery_method,
                            subject=f"Thank you - {msg_type.title()} Message",
                            content=content,
                            agent_id='gratitude_system'
                        )
                        
                        results['messages_sent'] += 1
                        self.logger.info(f"Sent {msg_type} gratitude message {message_id} to client {client_id}")
                    else:
                        # Mark as failed
                        cursor.execute('''
                            UPDATE gratitude_messages 
                            SET status = 'failed' 
                            WHERE id = ?
                        ''', (message_id,))
                        
                        results['messages_failed'] += 1
                        self.logger.error(f"Failed to send gratitude message {message_id}")
                
                except Exception as e:
                    self.logger.error(f"Error processing gratitude message {message_id}: {str(e)}")
                    results['messages_failed'] += 1
                
                results['messages_processed'] += 1
            
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error processing gratitude messages: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
        
        return results
    
    def _send_gratitude_message(self, client_id: int, content: str, delivery_method: str) -> bool:
        """Send gratitude message via specified delivery method"""
        try:
            # In a real implementation, this would integrate with email services, SMS, etc.
            # For now, we'll simulate successful delivery
            
            if delivery_method == 'email':
                # Simulate email sending
                self.logger.info(f"Simulated email gratitude message sent to client {client_id}")
                return True
            elif delivery_method == 'dashboard':
                # Simulate dashboard notification
                self.logger.info(f"Simulated dashboard gratitude message sent to client {client_id}")
                return True
            elif delivery_method == 'sms':
                # Simulate SMS sending
                self.logger.info(f"Simulated SMS gratitude message sent to client {client_id}")
                return True
            else:
                self.logger.error(f"Unknown delivery method: {delivery_method}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending gratitude message: {str(e)}")
            return False
    
    def _log_communication(self, client_id: int, communication_type: str, method: str, 
                          subject: str, content: str, agent_id: str = None, 
                          response_time_minutes: int = None):
        """Log communication in the database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO client_communications (
                    client_id, communication_type, contact_method, subject, content,
                    agent_id, response_time_minutes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_id, communication_type, method, subject, content,
                agent_id, response_time_minutes
            ))
            
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error logging communication: {str(e)}")
        finally:
            conn.close()
    
    def generate_service_metrics(self) -> Dict[str, Any]:
        """Generate customer service performance metrics"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        metrics = {}
        
        try:
            # Get today's date
            today = datetime.now().date().isoformat()
            
            # Total requests today
            cursor.execute('''
                SELECT COUNT(*) FROM contact_requests 
                WHERE DATE(created_at) = ?
            ''', (today,))
            metrics['total_requests_today'] = cursor.fetchone()[0]
            
            # Resolved requests today
            cursor.execute('''
                SELECT COUNT(*) FROM contact_requests 
                WHERE DATE(resolved_at) = ? AND status = 'resolved'
            ''', (today,))
            metrics['resolved_requests_today'] = cursor.fetchone()[0]
            
            # Average response time (in minutes)
            cursor.execute('''
                SELECT AVG(response_time_minutes) 
                FROM client_communications 
                WHERE DATE(timestamp) = ? AND response_time_minutes IS NOT NULL
            ''', (today,))
            result = cursor.fetchone()[0]
            metrics['avg_response_time_minutes'] = round(result, 2) if result else 0
            
            # Gratitude messages sent today
            cursor.execute('''
                SELECT COUNT(*) FROM gratitude_messages 
                WHERE DATE(sent_date) = ? AND status = 'sent'
            ''', (today,))
            metrics['gratitude_messages_sent_today'] = cursor.fetchone()[0]
            
            # Open requests by priority
            cursor.execute('''
                SELECT priority, COUNT(*) 
                FROM contact_requests 
                WHERE status IN ('open', 'in_progress')
                GROUP BY priority
            ''')
            
            priority_counts = dict(cursor.fetchall())
            metrics['open_requests_by_priority'] = priority_counts
            
            # Calculate satisfaction score (placeholder - would be based on client feedback)
            metrics['satisfaction_score'] = 4.2  # Out of 5
            
            # Store metrics in database
            cursor.execute('''
                INSERT OR REPLACE INTO customer_service_metrics (
                    metric_date, total_requests, resolved_requests, 
                    avg_response_time_minutes, satisfaction_score, gratitude_messages_sent
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                today, metrics['total_requests_today'], metrics['resolved_requests_today'],
                metrics['avg_response_time_minutes'], metrics['satisfaction_score'],
                metrics['gratitude_messages_sent_today']
            ))
            
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error generating service metrics: {str(e)}")
        finally:
            conn.close()
        
        return metrics
    
    def run_customer_service_cycle(self) -> Dict[str, Any]:
        """Run a complete customer service processing cycle"""
        self.logger.info("Starting customer service cycle...")
        
        cycle_results = {
            'start_time': datetime.now().isoformat(),
            'contact_requests_processed': {},
            'gratitude_messages_processed': {},
            'service_metrics': {},
            'status': 'completed'
        }
        
        try:
            # Process contact requests
            cycle_results['contact_requests_processed'] = self.process_contact_requests()
            
            # Process gratitude messages
            cycle_results['gratitude_messages_processed'] = self.process_gratitude_messages()
            
            # Generate service metrics
            cycle_results['service_metrics'] = self.generate_service_metrics()
            
            cycle_results['end_time'] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Error during customer service cycle: {str(e)}")
            cycle_results['status'] = 'failed'
            cycle_results['error'] = str(e)
        
        self.logger.info("Customer service cycle completed")
        return cycle_results


if __name__ == "__main__":
    # Test the customer service agent
    agent = CustomerServiceAgent()
    
    print("Running customer service agent test...")
    
    # Test creating a contact request
    contact_data = {
        'client_id': 1,
        'contact_method': 'email',
        'subject': 'Dashboard Access Issue',
        'message': 'I am having trouble accessing my dashboard. Can you help?',
        'client_email': 'test@example.com',
        'client_name': 'Test Client'
    }
    
    request_id = agent.create_contact_request(contact_data)
    print(f"Created contact request: {request_id}")
    
    # Test scheduling a gratitude message
    message_id = agent.schedule_gratitude_message(
        client_id=1,
        message_type='welcome',
        trigger_event='client_onboarding',
        personalization_data={'company_name': 'Test Company'}
    )
    print(f"Scheduled gratitude message: {message_id}")
    
    # Run a complete service cycle
    results = agent.run_customer_service_cycle()
    print(f"Service cycle status: {results['status']}")
    print(f"Requests processed: {results['contact_requests_processed']['processed_requests']}")
    print(f"Messages sent: {results['gratitude_messages_processed']['messages_sent']}")
    
    print("Customer service agent test completed.")

