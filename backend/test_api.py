"""
Simple script to test the API endpoints
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("Testing /api/v1/health...")
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


def test_analyze():
    """Test analyze endpoint"""
    print("Testing /api/v1/analyze...")
    
    # Create a dummy image file
    dummy_image = b"fake image content"
    
    # Prepare boxes data
    boxes = [
        {"x": 100, "y": 50, "width": 300, "height": 200, "label": "blueprints"},
        {"x": 450, "y": 50, "width": 200, "height": 150, "label": "resources"},
        {"x": 700, "y": 50, "width": 100, "height": 100, "label": "species"}
    ]
    
    files = {
        'image': ('test.png', dummy_image, 'image/png')
    }
    
    data = {
        'boxes': json.dumps(boxes),
        'session_id': 'test_session_123'
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/analyze", files=files, data=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Request ID: {result['request_id']}")
        print(f"Game State: {json.dumps(result['game_state'], indent=2, ensure_ascii=False)}")
        print(f"Recommendations ({len(result['recommendations'])}):")
        for rec in result['recommendations']:
            print(f"  {rec['rank']}. {rec['blueprint_name']} - Score: {rec['score']}")
    else:
        print(f"Error: {response.text}")
    print()


def test_history():
    """Test history endpoint"""
    print("Testing /api/v1/history...")
    response = requests.get(f"{BASE_URL}/api/v1/history?limit=5")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total records: {result['total']}")
        print(f"Records returned: {len(result['records'])}")
        for record in result['records']:
            print(f"  - {record['id']}: {record['game_state']['species']}")
    else:
        print(f"Error: {response.text}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("API Test Script")
    print("=" * 60)
    print()
    
    try:
        test_health()
        test_analyze()
        test_history()
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server.")
        print("Make sure the server is running: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"Error: {e}")
