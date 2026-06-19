#!/usr/bin/env python
"""
Verification script to test that all hybrid tools are working correctly with PostgreSQL.
Run this AFTER the backend is started: python main.py
"""
import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_TOKEN = "test_admin_token"  # Change to your token if different

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name: str):
    print(f"\n{Colors.BLUE}> Testing {name}...{Colors.END}")

def print_success(msg: str):
    print(f"{Colors.GREEN}OK {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}FAIL {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.YELLOW}INFO {msg}{Colors.END}")

def test_health() -> bool:
    """Test health check endpoints."""
    print_test("Health Check")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        if resp.status_code == 200:
            data = resp.json()
            print_success(f"Liveness: {data['status']}")
            print_info(f"  Version: {data['version']}")
            print_info(f"  Uptime: {data['uptime_seconds']}s")
            return True
        else:
            print_error(f"Health check failed: {resp.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot reach backend: {e}")
        return False

def test_database_health() -> bool:
    """Test readiness check (includes database)."""
    print_test("Database Health")
    try:
        resp = requests.get(f"{BASE_URL}/health/ready")
        if resp.status_code == 200:
            data = resp.json()
            checks = data.get('checks', {})
            status = data.get('status')
            
            if checks.get('database') == 'ok':
                print_success(f"Database: {checks['database']}")
                print_success(f"Overall status: {status}")
                return True
            else:
                print_error(f"Database: {checks.get('database', 'unknown')}")
                return False
        else:
            print_error(f"Readiness check failed: {resp.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot reach readiness endpoint: {e}")
        return False

def test_knowledge_base() -> bool:
    """Test knowledge base CRUD operations."""
    print_test("Knowledge Base Tool")
    try:
        # List existing
        resp = requests.get(f"{BASE_URL}/knowledge")
        if resp.status_code == 200:
            entries = resp.json()
            print_success(f"Listed {len(entries)} knowledge entries")
        else:
            print_error(f"List failed: {resp.status_code}")
            return False
        
        # Create new
        new_entry = {
            "question_en": "What is test?",
            "answer_en": "This is a test answer.",
            "question_ml": "Test എന്നത് എന്ത്?",
            "answer_ml": "ഇത് ഒരു പരിക്ഷണ ഉത്തരം.",
            "category": "Testing"
        }
        resp = requests.post(
            f"{BASE_URL}/knowledge",
            json=new_entry,
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )
        if resp.status_code == 200:
            created = resp.json()
            entry_id = created.get('id')
            print_success(f"Created knowledge entry ID: {entry_id}")
            
            # Get the entry
            resp = requests.get(f"{BASE_URL}/knowledge/{entry_id}")
            if resp.status_code == 200:
                retrieved = resp.json()
                print_success(f"Retrieved entry: {retrieved['question_en']}")
                return True
            else:
                print_error(f"Retrieve failed: {resp.status_code}")
                return False
        else:
            print_error(f"Create failed: {resp.status_code}")
            print_info(f"Response: {resp.text[:200]}")
            return False
    except Exception as e:
        print_error(f"Knowledge base test failed: {e}")
        return False

def test_lead_capture() -> bool:
    """Test lead capture tool."""
    print_test("Lead Capture Tool")
    try:
        # Create lead
        new_lead = {
            "name": "Test Lead",
            "phone": "9876543210",
            "course": "MERN Stack",
            "consent_whatsapp": True,
            "language": "en",
            "source": "test"
        }
        resp = requests.post(f"{BASE_URL}/leads", json=new_lead)
        if resp.status_code == 200:
            created = resp.json()
            lead_id = created.get('id')
            print_success(f"Created lead ID: {lead_id}")
            print_info(f"  Name: {created['name']}")
            print_info(f"  Phone: {created['phone']}")
            
            # Get the lead
            resp = requests.get(f"{BASE_URL}/leads/{lead_id}")
            if resp.status_code == 200:
                retrieved = resp.json()
                print_success(f"Retrieved lead: {retrieved['name']}")
                return True
            else:
                print_error(f"Retrieve failed: {resp.status_code}")
                return False
        else:
            print_error(f"Create failed: {resp.status_code}")
            print_info(f"Response: {resp.text[:200]}")
            return False
    except Exception as e:
        print_error(f"Lead capture test failed: {e}")
        return False

def test_dashboard_stats() -> bool:
    """Test dashboard stats endpoint."""
    print_test("Dashboard Stats Tool")
    try:
        resp = requests.get(
            f"{BASE_URL}/dashboard/stats",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )
        if resp.status_code == 200:
            stats = resp.json()
            data = stats.get('stats', {})
            print_success("Retrieved dashboard stats")
            print_info(f"  Total calls (all-time): {data.get('total_calls_all_time', 0)}")
            print_info(f"  Leads captured: {data.get('leads_captured', 0)}")
            print_info(f"  Resolution rate: {data.get('resolution_rate', 0)}%")
            print_info(f"  Escalation rate: {data.get('escalation_rate', 0)}%")
            return True
        else:
            print_error(f"Stats failed: {resp.status_code}")
            return False
    except Exception as e:
        print_error(f"Dashboard stats test failed: {e}")
        return False

def test_analytics() -> bool:
    """Test analytics endpoint."""
    print_test("Analytics Tool")
    try:
        resp = requests.get(
            f"{BASE_URL}/dashboard/analytics",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )
        if resp.status_code == 200:
            analytics = resp.json()
            print_success("Retrieved analytics breakdown")
            
            outcomes = analytics.get('outcomes', [])
            if outcomes:
                print_info(f"  Outcomes tracked: {len(outcomes)}")
                for outcome in outcomes[:2]:
                    print_info(f"    - {outcome['label']}: {outcome['count']}")
            
            languages = analytics.get('languages', {})
            if languages:
                print_info(f"  Languages: EN={languages.get('en', {}).get('count', 0)}, ML={languages.get('ml', {}).get('count', 0)}")
            
            return True
        else:
            print_error(f"Analytics failed: {resp.status_code}")
            return False
    except Exception as e:
        print_error(f"Analytics test failed: {e}")
        return False

def test_audit_logs() -> bool:
    """Test audit logs endpoint."""
    print_test("Audit Logs Tool")
    try:
        resp = requests.get(
            f"{BASE_URL}/dashboard/audit-logs",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )
        if resp.status_code == 200:
            logs = resp.json()
            print_success(f"Retrieved {len(logs)} audit log entries")
            if logs:
                latest = logs[0] if isinstance(logs, list) else logs.get('logs', [{}])[0]
                print_info(f"  Latest action: {latest.get('action', 'unknown')[:50]}")
            return True
        else:
            print_error(f"Audit logs failed: {resp.status_code}")
            return False
    except Exception as e:
        print_error(f"Audit logs test failed: {e}")
        return False

def test_settings() -> bool:
    """Test settings persistence."""
    print_test("Settings Persistence Tool")
    try:
        resp = requests.get(
            f"{BASE_URL}/dashboard/settings",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )
        if resp.status_code == 200:
            settings = resp.json()
            print_success(f"Retrieved {len(settings)} setting entries")
            print_info(f"  Engine mode: {settings.get('engine_mode', 'unknown')}")
            print_info(f"  Office hours enabled: {settings.get('office_hours_enabled', False)}")
            print_info(f"  Escalation enabled: {settings.get('escalation_enabled', False)}")
            return True
        else:
            print_error(f"Settings failed: {resp.status_code}")
            return False
    except Exception as e:
        print_error(f"Settings test failed: {e}")
        return False

def main():
    """Run all tests."""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("PostgreSQL + Hybrid Tools Verification")
    print(f"{'='*60}{Colors.END}")
    
    print(f"\nBackend URL: {BASE_URL}")
    print(f"Admin token: {ADMIN_TOKEN}")
    
    # Give backend a moment to respond
    print("\nWaiting for backend...")
    time.sleep(1)
    
    results = []
    
    # Run all tests
    results.append(("Health Check", test_health()))
    results.append(("Database Health", test_database_health()))
    results.append(("Knowledge Base Tool", test_knowledge_base()))
    results.append(("Lead Capture Tool", test_lead_capture()))
    results.append(("Dashboard Stats Tool", test_dashboard_stats()))
    results.append(("Analytics Tool", test_analytics()))
    results.append(("Audit Logs Tool", test_audit_logs()))
    results.append(("Settings Persistence Tool", test_settings()))
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}")
    print("Test Summary")
    print(f"{'='*60}{Colors.END}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{status} {name}")
    
    print(f"\nResults: {Colors.GREEN}{passed}/{total}{Colors.END} tests passed")
    
    if passed == total:
        print(f"\n{Colors.GREEN}OK All hybrid tools are working correctly with PostgreSQL!{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}FAIL Some tests failed. Check the errors above.{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
