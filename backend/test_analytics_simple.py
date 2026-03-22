"""
Simple test for clinical analytics endpoints without database dependency
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints_basic():
    """Test that endpoints respond (even if with empty data)"""
    print("Testing Clinical Analytics Endpoints (Basic)...")
    
    endpoints = [
        "/api/clinical/daily-metrics/test_patient",
        "/api/clinical/weekly-report/test_patient", 
        "/api/clinical/episode-frequency/test_patient",
        "/api/clinical/resistance-index/test_patient"
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint}...")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Success - Response has {len(data)} keys")
                results.append(True)
            elif response.status_code == 500:
                error_detail = response.json().get("detail", "Unknown error")
                print(f"❌ Server Error: {error_detail}")
                results.append(False)
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")
            results.append(False)
    
    return results

def test_root_endpoint():
    """Test the root endpoint"""
    print("Testing Root Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Root endpoint working: {data}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Root endpoint error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Clinical Analytics API Endpoints (Simple)...")
    
    try:
        # Test root endpoint first
        if not test_root_endpoint():
            print("❌ Server basic functionality failed.")
            exit(1)
        
        # Test analytics endpoints
        results = test_endpoints_basic()
        
        success_count = sum(results)
        total_count = len(results)
        
        print(f"\n📊 Results: {success_count}/{total_count} endpoints working")
        
        if success_count == total_count:
            print("✅ All clinical analytics endpoints are responding!")
        elif success_count > 0:
            print("⚠️ Some endpoints working, some have issues (likely database connectivity)")
        else:
            print("❌ All endpoints failed")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()