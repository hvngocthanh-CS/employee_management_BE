#!/usr/bin/env python3
"""
Test script for Employee Management API
=========================================
Simple test script to verify API endpoints are working
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"{method} {endpoint}: {response.status_code}")
        if response.status_code < 400:
            print("✅ Success")
        else:
            print("❌ Failed")
            print(f"Response: {response.text}")
        print("-" * 50)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to {endpoint}: {e}")
        print("-" * 50)

def main():
    print("🚀 Testing Employee Management API")
    print("=" * 50)
    
    # Test basic endpoints
    test_endpoint("/departments")
    test_endpoint("/positions") 
    test_endpoint("/employees")
    test_endpoint("/users")
    test_endpoint("/salaries")
    test_endpoint("/attendances")
    test_endpoint("/leaves")
    
    # Test creating a department
    test_endpoint("/departments", "POST", {"name": "IT Department"})
    
    # Test creating a position
    test_endpoint("/positions", "POST", {
        "title": "Software Developer",
        "code": "DEV001",
        "level": "senior",
        "description": "Senior Software Developer"
    })

if __name__ == "__main__":
    main()