import httpx
import json

client = httpx.Client(base_url='http://localhost:8000')
r = client.post('/api/v1/evidence/EVD-20261022175022-8504-d28b7edf/analyze', json={})
print('Status:', r.status_code)
data = r.json()
print('Analysis ID:', data.get('analysis_id'))
print('Execution Status:', data.get('execution_status'))
print('Summary:', json.dumps(data.get('summary'), indent=2))
findings = data.get('findings', [])
print(f'Total findings: {len(findings)}')
for i, f in enumerate(findings):
    cat = f['category']
    prio = f['priority']
    st = f['start_time']
    et = f['end_time']
    val = f['measured_value']
    print(f'Finding {i+1}: [{cat.upper()}] ({prio}) {st}s -> {et}s | Value: {val}')
    print(f'  Explanation: {f["explanation"]}')
