import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_workflow():
    print("--- 1. Testing Health Check ---")
    res = requests.get(f"{BASE_URL}/")
    print(res.json())
    print("\n--- 2. Requesting Plan (Architect + MCP) ---")
    
    prompt = "Create a workflow that reads a new Gmail email and sends a Slack message."
    
    res = requests.post(f"{BASE_URL}/plan", json={"prompt": prompt})
    
    if res.status_code != 200:
        print(f"Error: {res.text}")
        return
        
    data = res.json()
    print("Plan Response:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    thread_id = data.get("thread_id")
    if not thread_id:
        print("No thread ID returned!")
        return
        
    print("\n--- 3. Confirming Plan (Coder + MCP) ---")
    # Simulate user reading the plan and confirming
    time.sleep(1)
    
    res = requests.post(f"{BASE_URL}/confirm", json={"thread_id": thread_id})
    if res.status_code != 200:
        print(f"Error: {res.text}")
        return
        
    print("Final n8n JSON:")
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_workflow()
