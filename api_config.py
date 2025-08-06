"""
API Configuration Management System
Manages API keys, rate limits, and fallback mechanisms for the AI Marketing Agency
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import sqlite3


@dataclass
class APIConfig:
    """Configuration for a single API"""
    name: str
    api_key: str
    base_url: str
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int = 1000
    free_tier_limit: int = 100
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority


@dataclass
class APIUsage:
    """Track API usage statistics"""
    api_name: str
    requests_today: int = 0
    requests_this_minute: int = 0
    last_request_time: Optional[datetime] = None
    total_requests: int = 0
    errors_today: int = 0
    last_error_time: Optional[datetime] = None


class APIManager:
    """
    Manages multiple APIs with rate limiting, fallback, and usage tracking
    """
    
    def __init__(self, config_file: str = "api_config.json", database_path: str = "leads.db"):
        self.config_file = config_file
        self.database_path = database_path
        self.apis: Dict[str, APIConfig] = {}
        self.usage: Dict[str, APIUsage] = {}
        self.logger = logging.getLogger(__name__)
        
        self.setup_database()
        self.load_configuration()
    
    def setup_database(self):
        """Setup API usage tracking tables"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_name TEXT NOT NULL,
                date TEXT NOT NULL,
                requests_count INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                response_time_avg REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(api_name, date)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_requests_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_name TEXT NOT NULL,
                endpoint TEXT,
                status_code INTEGER,
                response_time REAL,
                error_message TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_configuration(self):
        """Load API configurations from file or create default"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                for api_name, config in config_data.items():
                    self.apis[api_name] = APIConfig(**config)
                    self.usage[api_name] = APIUsage(api_name=api_name)
            else:
                self.create_default_configuration()
                
        except Exception as e:
            self.logger.error(f"Error loading API configuration: {str(e)}")
            self.create_default_configuration()
    
    def create_default_configuration(self):
        """Create default API configuration with free tier APIs"""
        default_apis = {
            "abstract_email_validation": APIConfig(
                name="abstract_email_validation",
                api_key=os.getenv("ABSTRACT_EMAIL_API_KEY", ""),
                base_url="https://emailvalidation.abstractapi.com/v1/",
                rate_limit_per_minute=60,
                rate_limit_per_day=100,  # Free tier limit
                free_tier_limit=100,
                enabled=True,
                priority=1
            ),
            "abstract_company_enrichment": APIConfig(
                name="abstract_company_enrichment",
                api_key=os.getenv("ABSTRACT_COMPANY_API_KEY", ""),
                base_url="https://companyenrichment.abstractapi.com/v1/",
                rate_limit_per_minute=60,
                rate_limit_per_day=100,  # Free tier limit
                free_tier_limit=100,
                enabled=True,
                priority=1
            ),
            "apideck_lead": APIConfig(
                name="apideck_lead",
                api_key=os.getenv("APIDECK_API_KEY", ""),
                base_url="https://unify.apideck.com/crm/",
                rate_limit_per_minute=60,
                rate_limit_per_day=2500,  # Free tier limit
                free_tier_limit=2500,
                enabled=True,
                priority=1
            ),
            "apideck_crm": APIConfig(
                name="apideck_crm",
                api_key=os.getenv("APIDECK_CRM_API_KEY", ""),
                base_url="https://unify.apideck.com/crm/",
                rate_limit_per_minute=60,
                rate_limit_per_day=2500,  # Free tier limit
                free_tier_limit=2500,
                enabled=True,
                priority=2
            )
        }
        
        for api_name, config in default_apis.items():
            self.apis[api_name] = config
            self.usage[api_name] = APIUsage(api_name=api_name)
        
        self.save_configuration()
    
    def save_configuration(self):
        """Save current API configuration to file"""
        try:
            config_data = {}
            for api_name, config in self.apis.items():
                config_data[api_name] = asdict(config)
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving API configuration: {str(e)}")
    
    def get_available_api(self, api_type: str) -> Optional[APIConfig]:
        """
        Get the best available API for a specific type based on priority and usage limits
        """
        # Filter APIs by type (based on name pattern)
        type_apis = []
        for api_name, config in self.apis.items():
            if api_type.lower() in api_name.lower() and config.enabled:
                type_apis.append(config)
        
        if not type_apis:
            return None
        
        # Sort by priority (lower number = higher priority)
        type_apis.sort(key=lambda x: x.priority)
        
        # Check each API for availability
        for api_config in type_apis:
            if self.can_make_request(api_config.name):
                return api_config
        
        return None
    
    def can_make_request(self, api_name: str) -> bool:
        """Check if we can make a request to the specified API"""
        if api_name not in self.apis or not self.apis[api_name].enabled:
            return False
        
        config = self.apis[api_name]
        usage = self.usage[api_name]
        
        # Check daily limit
        if usage.requests_today >= config.rate_limit_per_day:
            return False
        
        # Check minute limit
        now = datetime.now()
        if usage.last_request_time:
            time_diff = now - usage.last_request_time
            if time_diff < timedelta(minutes=1) and usage.requests_this_minute >= config.rate_limit_per_minute:
                return False
        
        return True
    
    def record_request(self, api_name: str, endpoint: str = "", status_code: int = 200, 
                      response_time: float = 0.0, error_message: str = ""):
        """Record an API request for usage tracking"""
        if api_name not in self.usage:
            self.usage[api_name] = APIUsage(api_name=api_name)
        
        usage = self.usage[api_name]
        now = datetime.now()
        
        # Update usage counters
        usage.total_requests += 1
        usage.requests_today += 1
        
        # Reset minute counter if needed
        if usage.last_request_time and (now - usage.last_request_time) >= timedelta(minutes=1):
            usage.requests_this_minute = 0
        
        usage.requests_this_minute += 1
        usage.last_request_time = now
        
        # Track errors
        if status_code >= 400:
            usage.errors_today += 1
            usage.last_error_time = now
        
        # Log to database
        self.log_request_to_database(api_name, endpoint, status_code, response_time, error_message)
        
        # Update daily usage in database
        self.update_daily_usage(api_name)
    
    def log_request_to_database(self, api_name: str, endpoint: str, status_code: int, 
                               response_time: float, error_message: str):
        """Log individual request to database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO api_requests_log (
                    api_name, endpoint, status_code, response_time, error_message
                ) VALUES (?, ?, ?, ?, ?)
            ''', (api_name, endpoint, status_code, response_time, error_message))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error logging API request: {str(e)}")
    
    def update_daily_usage(self, api_name: str):
        """Update daily usage statistics in database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            today = datetime.now().date().isoformat()
            usage = self.usage[api_name]
            
            cursor.execute('''
                INSERT OR REPLACE INTO api_usage (
                    api_name, date, requests_count, errors_count
                ) VALUES (?, ?, ?, ?)
            ''', (api_name, today, usage.requests_today, usage.errors_today))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating daily usage: {str(e)}")
    
    def reset_daily_counters(self):
        """Reset daily usage counters (should be called daily)"""
        for usage in self.usage.values():
            usage.requests_today = 0
            usage.errors_today = 0
    
    def get_usage_stats(self, api_name: str = None) -> Dict[str, Any]:
        """Get usage statistics for specific API or all APIs"""
        if api_name:
            if api_name in self.usage:
                return asdict(self.usage[api_name])
            return {}
        
        return {name: asdict(usage) for name, usage in self.usage.items()}
    
    def get_api_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all APIs"""
        health_status = {}
        
        for api_name, config in self.apis.items():
            usage = self.usage[api_name]
            
            # Calculate health metrics
            error_rate = 0.0
            if usage.total_requests > 0:
                error_rate = (usage.errors_today / usage.total_requests) * 100
            
            usage_percentage = (usage.requests_today / config.rate_limit_per_day) * 100
            
            health_status[api_name] = {
                "enabled": config.enabled,
                "can_make_request": self.can_make_request(api_name),
                "usage_percentage": usage_percentage,
                "error_rate": error_rate,
                "requests_today": usage.requests_today,
                "daily_limit": config.rate_limit_per_day,
                "last_request": usage.last_request_time.isoformat() if usage.last_request_time else None,
                "last_error": usage.last_error_time.isoformat() if usage.last_error_time else None
            }
        
        return health_status
    
    def add_api(self, config: APIConfig):
        """Add a new API configuration"""
        self.apis[config.name] = config
        self.usage[config.name] = APIUsage(api_name=config.name)
        self.save_configuration()
    
    def update_api(self, api_name: str, **kwargs):
        """Update an existing API configuration"""
        if api_name in self.apis:
            config = self.apis[api_name]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            self.save_configuration()
    
    def disable_api(self, api_name: str):
        """Disable an API"""
        if api_name in self.apis:
            self.apis[api_name].enabled = False
            self.save_configuration()
    
    def enable_api(self, api_name: str):
        """Enable an API"""
        if api_name in self.apis:
            self.apis[api_name].enabled = True
            self.save_configuration()


# Global API manager instance
api_manager = APIManager()


def get_api_manager() -> APIManager:
    """Get the global API manager instance"""
    return api_manager


if __name__ == "__main__":
    # Test the API manager
    manager = APIManager()
    
    print("API Health Status:")
    health = manager.get_api_health()
    for api_name, status in health.items():
        print(f"  {api_name}: {status}")
    
    print("\nUsage Statistics:")
    stats = manager.get_usage_stats()
    for api_name, usage in stats.items():
        print(f"  {api_name}: {usage}")

