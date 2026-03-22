#!/usr/bin/env python3
import requests
import json

# Test demo status
response = requests.get('http://localhost:8000/api/demo/status')
print('Status Code:', response.status_code)
print('Response:')
print(json.dumps(response.json(), indent=2))