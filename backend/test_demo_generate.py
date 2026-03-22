#!/usr/bin/env python3
import requests
import json

try:
    response = requests.post('http://localhost:8000/api/demo/generate')
    print('Demo Generate Response:')
    print(json.dumps(response.json(), indent=2))
    print(f'Status Code: {response.status_code}')
except Exception as e:
    print(f'Error: {e}')