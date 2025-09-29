import requests

# Get all available tools
response = requests.get('http://127.0.0.1:8001/tools')
tools = response.json()

print(f"Total tools available: {len(tools)}")
print("\nAvailable tools:")
for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")

# Test system server connection
print("\n" + "="*50)
print("Testing system server connection...")

# Try to create a quest
quest_response = requests.post('http://127.0.0.1:8001/run-tool', 
    json={'tool': 'system.create_quest', 
          'args': {'title': 'Test Quest', 'description': 'Testing system server', 'category': 'general'}})

print(f"Quest creation result: {quest_response.json()}")

# Test brain service
print("\n" + "="*50)
print("Testing brain service...")

brain_response = requests.post('http://127.0.0.1:8088/chat', 
    json={'input': 'Hello Jarvis, remember my goal is to buy a BMW 335i'})

print(f"Brain response: {brain_response.json()}")