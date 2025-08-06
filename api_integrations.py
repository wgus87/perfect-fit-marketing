"""
API Integration Modules
Provides integration with various free/freemium APIs for the AI Marketing Agency
Uses Hunter.io and Clearbit free tiers for core functionality
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
from api_config import get_api_manager, APIConfig

# Free API keys for development/testing
HUNTER_API_KEY = "DEMO_API_KEY"  # Sign up at hunter.io/api
CLEARBIT_API_KEY = "sk_DEMO_KEY"  # Sign up at clearbit.com/docs


@dataclass
class EmailValidationResult:
    """Result from email validation API"""
    email: str
    is_valid: bool
    is_disposable: bool
    is_free_provider: bool
    is_role_email: bool
    quality_score: float
    suggestion: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class CompanyEnrichmentResult:
    """Result from company enrichment API"""
    domain: str
    company_name: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[List[str]] = None
    social_media: Optional[Dict[str, str]] = None
    error_message: Optional[str] = None


@dataclass
class LeadResult:
    """Result from lead generation API"""
    lead_id: str
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    error_message: Optional[str] = None


class EmailValidationAPI:
    """
    Email validation using Abstract API
    """
    
    def __init__(self):
        self.api_manager = get_api_manager()
        self.logger = logging.getLogger(__name__)
    
    def validate_email(self, email: str) -> EmailValidationResult:
        """
        Validate a single email address
        """
        api_config = self.api_manager.get_available_api("email")
        
        if not api_config:
            return EmailValidationResult(
                email=email,
                is_valid=False,
                is_disposable=False,
                is_free_provider=False,
                is_role_email=False,
                quality_score=0.0,
                error_message="No available email validation API"
            )
        
        start_time = time.time()
        
        try:
            url = f"{api_config.base_url}"
            params = {
                "api_key": api_config.api_key,
                "email": email
            }
            
            response = requests.get(url, params=params, timeout=10)
            response_time = time.time() - start_time
            
            # Record the request
            self.api_manager.record_request(
                api_config.name,
                "validate",
                response.status_code,
                response_time
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse Abstract API response
                return EmailValidationResult(
                    email=email,
                    is_valid=data.get("is_valid_format", {}).get("value", False) and 
                            data.get("is_mx_found", {}).get("value", False),
                    is_disposable=data.get("is_disposable_email", {}).get("value", False),
                    is_free_provider=data.get("is_free_email", {}).get("value", False),
                    is_role_email=data.get("is_role_email", {}).get("value", False),
                    quality_score=data.get("quality_score", 0.0),
                    suggestion=data.get("autocorrect", "")
                )
            
            else:
                error_msg = f"API request failed with status {response.status_code}"
                self.api_manager.record_request(
                    api_config.name,
                    "validate",
                    response.status_code,
                    response_time,
                    error_msg
                )
                
                return EmailValidationResult(
                    email=email,
                    is_valid=False,
                    is_disposable=False,
                    is_free_provider=False,
                    is_role_email=False,
                    quality_score=0.0,
                    error_message=error_msg
                )
        
        except Exception as e:
            error_msg = f"Email validation error: {str(e)}"
            self.logger.error(error_msg)
            
            self.api_manager.record_request(
                api_config.name,
                "validate",
                500,
                time.time() - start_time,
                error_msg
            )
            
            return EmailValidationResult(
                email=email,
                is_valid=False,
                is_disposable=False,
                is_free_provider=False,
                is_role_email=False,
                quality_score=0.0,
                error_message=error_msg
            )
    
    def validate_emails_batch(self, emails: List[str]) -> List[EmailValidationResult]:
        """
        Validate multiple email addresses
        """
        results = []
        
        for email in emails:
            # Check rate limits before each request
            if not self.api_manager.can_make_request("abstract_email_validation"):
                self.logger.warning("Rate limit reached for email validation API")
                break
            
            result = self.validate_email(email)
            results.append(result)
            
            # Small delay to respect rate limits
            time.sleep(0.1)
        
        return results


class CompanyEnrichmentAPI:
    """
    Company data enrichment using Abstract API
    """
    
    def __init__(self):
        self.api_manager = get_api_manager()
        self.logger = logging.getLogger(__name__)
    
    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        """
        Enrich company data by domain
        """
        api_config = self.api_manager.get_available_api("company")
        
        if not api_config:
            return CompanyEnrichmentResult(
                domain=domain,
                error_message="No available company enrichment API"
            )
        
        start_time = time.time()
        
        try:
            url = f"{api_config.base_url}"
            params = {
                "api_key": api_config.api_key,
                "domain": domain
            }
            
            response = requests.get(url, params=params, timeout=15)
            response_time = time.time() - start_time
            
            # Record the request
            self.api_manager.record_request(
                api_config.name,
                "enrich",
                response.status_code,
                response_time
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse Abstract API response
                return CompanyEnrichmentResult(
                    domain=domain,
                    company_name=data.get("name"),
                    industry=data.get("industry"),
                    employee_count=data.get("employees_count"),
                    annual_revenue=data.get("annual_revenue"),
                    location=data.get("country"),
                    description=data.get("description"),
                    technologies=data.get("technologies", []),
                    social_media={
                        "linkedin": data.get("linkedin_url"),
                        "twitter": data.get("twitter_url"),
                        "facebook": data.get("facebook_url")
                    }
                )
            
            else:
                error_msg = f"API request failed with status {response.status_code}"
                self.api_manager.record_request(
                    api_config.name,
                    "enrich",
                    response.status_code,
                    response_time,
                    error_msg
                )
                
                return CompanyEnrichmentResult(
                    domain=domain,
                    error_message=error_msg
                )
        
        except Exception as e:
            error_msg = f"Company enrichment error: {str(e)}"
            self.logger.error(error_msg)
            
            self.api_manager.record_request(
                api_config.name,
                "enrich",
                500,
                time.time() - start_time,
                error_msg
            )
            
            return CompanyEnrichmentResult(
                domain=domain,
                error_message=error_msg
            )
    
    def enrich_companies_batch(self, domains: List[str]) -> List[CompanyEnrichmentResult]:
        """
        Enrich multiple companies
        """
        results = []
        
        for domain in domains:
            # Check rate limits before each request
            if not self.api_manager.can_make_request("abstract_company_enrichment"):
                self.logger.warning("Rate limit reached for company enrichment API")
                break
            
            result = self.enrich_company(domain)
            results.append(result)
            
            # Small delay to respect rate limits
            time.sleep(0.2)
        
        return results


class LeadGenerationAPI:
    """
    Lead generation using Apideck Lead API
    """
    
    def __init__(self):
        self.api_manager = get_api_manager()
        self.logger = logging.getLogger(__name__)
    
    def get_leads(self, limit: int = 10, filters: Dict[str, Any] = None) -> List[LeadResult]:
        """
        Get leads from Apideck Lead API
        """
        api_config = self.api_manager.get_available_api("lead")
        
        if not api_config:
            self.logger.error("No available lead generation API")
            return []
        
        start_time = time.time()
        
        try:
            url = f"{api_config.base_url}leads"
            headers = {
                "Authorization": f"Bearer {api_config.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {"limit": limit}
            if filters:
                params.update(filters)
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response_time = time.time() - start_time
            
            # Record the request
            self.api_manager.record_request(
                api_config.name,
                "leads",
                response.status_code,
                response_time
            )
            
            if response.status_code == 200:
                data = response.json()
                leads = []
                
                for lead_data in data.get("data", []):
                    lead = LeadResult(
                        lead_id=lead_data.get("id", ""),
                        company_name=lead_data.get("company_name", ""),
                        contact_name=f"{lead_data.get('first_name', '')} {lead_data.get('last_name', '')}".strip(),
                        email=lead_data.get("emails", [{}])[0].get("email") if lead_data.get("emails") else None,
                        phone=lead_data.get("phone_numbers", [{}])[0].get("number") if lead_data.get("phone_numbers") else None,
                        title=lead_data.get("title"),
                        industry=lead_data.get("industry"),
                        location=lead_data.get("addresses", [{}])[0].get("city") if lead_data.get("addresses") else None
                    )
                    leads.append(lead)
                
                return leads
            
            else:
                error_msg = f"API request failed with status {response.status_code}"
                self.api_manager.record_request(
                    api_config.name,
                    "leads",
                    response.status_code,
                    response_time,
                    error_msg
                )
                
                self.logger.error(error_msg)
                return []
        
        except Exception as e:
            error_msg = f"Lead generation error: {str(e)}"
            self.logger.error(error_msg)
            
            self.api_manager.record_request(
                api_config.name,
                "leads",
                500,
                time.time() - start_time,
                error_msg
            )
            
            return []


class APIIntegrationService:
    """
    Main service class that coordinates all API integrations
    """
    
    def __init__(self):
        self.email_validator = EmailValidationAPI()
        self.company_enricher = CompanyEnrichmentAPI()
        self.lead_generator = LeadGenerationAPI()
        self.api_manager = get_api_manager()
        self.logger = logging.getLogger(__name__)
    
    def validate_lead_email(self, email: str) -> EmailValidationResult:
        """Validate a lead's email address"""
        return self.email_validator.validate_email(email)
    
    def enrich_lead_company(self, domain: str) -> CompanyEnrichmentResult:
        """Enrich a lead's company information"""
        return self.company_enricher.enrich_company(domain)
    
    def generate_new_leads(self, count: int = 10) -> List[LeadResult]:
        """Generate new leads"""
        return self.lead_generator.get_leads(limit=count)
    
    def process_lead_with_enrichment(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a lead with full enrichment (email validation + company data)
        """
        enriched_lead = lead_data.copy()
        
        # Validate email if present
        if lead_data.get("email"):
            email_result = self.validate_lead_email(lead_data["email"])
            enriched_lead["email_validation"] = {
                "is_valid": email_result.is_valid,
                "is_disposable": email_result.is_disposable,
                "is_free_provider": email_result.is_free_provider,
                "quality_score": email_result.quality_score,
                "suggestion": email_result.suggestion
            }
        
        # Enrich company data if domain is available
        domain = self.extract_domain_from_email(lead_data.get("email", ""))
        if domain:
            company_result = self.enrich_lead_company(domain)
            enriched_lead["company_enrichment"] = {
                "industry": company_result.industry,
                "employee_count": company_result.employee_count,
                "annual_revenue": company_result.annual_revenue,
                "location": company_result.location,
                "description": company_result.description,
                "technologies": company_result.technologies
            }
        
        return enriched_lead
    
    def extract_domain_from_email(self, email: str) -> Optional[str]:
        """Extract domain from email address"""
        if "@" in email:
            return email.split("@")[1].lower()
        return None
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get status of all API integrations"""
        return self.api_manager.get_api_health()
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage summary for all APIs"""
        return self.api_manager.get_usage_stats()


if __name__ == "__main__":
    # Test the API integrations
    service = APIIntegrationService()
    
    print("API Status:")
    status = service.get_api_status()
    for api_name, api_status in status.items():
        print(f"  {api_name}: {'✓' if api_status['can_make_request'] else '✗'} "
              f"({api_status['usage_percentage']:.1f}% used)")
    
    # Test email validation (if API key is available)
    test_email = "test@example.com"
    print(f"\nTesting email validation for: {test_email}")
    email_result = service.validate_lead_email(test_email)
    print(f"  Valid: {email_result.is_valid}")
    print(f"  Quality Score: {email_result.quality_score}")
    
    # Test company enrichment (if API key is available)
    test_domain = "example.com"
    print(f"\nTesting company enrichment for: {test_domain}")
    company_result = service.enrich_lead_company(test_domain)
    print(f"  Company: {company_result.company_name}")
    print(f"  Industry: {company_result.industry}")
    
    print(f"\nUsage Summary:")
    usage = service.get_usage_summary()
    for api_name, api_usage in usage.items():
        print(f"  {api_name}: {api_usage['requests_today']} requests today")

