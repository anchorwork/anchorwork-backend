import requests
import json

BASE_URL = "http://localhost:8000"

def print_result(route, resp):
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    print(f"\n[{route}] — {resp.status_code}\n", json.dumps(data, indent=2) if isinstance(data, dict) else data)

def main():
    print("Testing all major Anchorwork API endpoints...\n")
    
    # Crew endpoints
    crew_prompt = "I need a ritual for resetting my energy after a stressful week."
    resp = requests.post(f"{BASE_URL}/crew/brainstorm", json={"prompt": crew_prompt})
    print_result("/crew/brainstorm", resp)
    
    sample_crew_responses = {
        "First Matey": "Sing a shanty...",
        "Cartographer": "Draw a new map...",
        "Coder": "Automate check-ins."
    }
    resp = requests.post(f"{BASE_URL}/crew/ritual_synthesis", json={"prompt": "Renew my hope", "crew_responses": sample_crew_responses})
    print_result("/crew/ritual_synthesis", resp)
    
    resp = requests.get(f"{BASE_URL}/crew/history", params={"n": 3})
    print_result("/crew/history", resp)
    
    resp = requests.get(f"{BASE_URL}/crew/history/search", params={"keyword": "burnout"})
    print_result("/crew/history/search", resp)

    # Coder agent
    resp = requests.post(f"{BASE_URL}/coder", json={"prompt": "Run static analysis"})
    print_result("/coder", resp)

    # Semantic Search
    resp = requests.post(f"{BASE_URL}/semantic_search", json={"query": "anchorwork ritual"})
    print_result("/semantic_search", resp)

    # Web Search
    resp = requests.post(f"{BASE_URL}/web-search", json={"query": "AI ritual design"})
    print_result("/web-search", resp)

    # Save Log
    resp = requests.post(f"{BASE_URL}/save_log", json={"prompt": "test", "response": "testing"})
    print_result("/save_log", resp)

    # Status
    resp = requests.get(f"{BASE_URL}/status/")
    print_result("/status", resp)

    # Briefing
    resp = requests.post(f"{BASE_URL}/briefing", json={"topic": "Resilience", "body": "Tips for resilience in stressful times."})
    print_result("/briefing", resp)

    print("\nAll tests complete.\n")

if __name__ == "__main__":
    main()