"""Check an IAM-private Cloud Run candidate using synthetic data; never print tokens."""
import argparse
import json
import subprocess
from urllib.request import Request, urlopen


def smoke(url, audience, identity_service_account):
    identity = subprocess.run(['gcloud', 'auth', 'print-identity-token', '--audiences', audience,
                               '--impersonate-service-account', identity_service_account],
                              check=True, capture_output=True, text=True).stdout.strip()
    sessions = []
    def request(path, body=None, token=None):
        headers = {'X-Serverless-Authorization': 'Bearer ' + identity}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        if body is not None:
            headers['Content-Type'] = 'application/json'
        req = Request(url.rstrip('/') + path, headers=headers,
                      data=json.dumps(body).encode() if body is not None else None)
        with urlopen(req, timeout=60) as response:
            data = response.read(3 * 1024 * 1024)
            return json.loads(data) if 'application/json' in response.headers.get('Content-Type', '') else data
    health = request('/health')
    ready = request('/ready')
    if health.get('status') != 'ok' or ready.get('status') != 'ready' or not ready.get('schema_current') or not ready.get('model_loaded') or ready.get('is_placeholder') is not False:
        raise RuntimeError('Candidate health/database/schema/model check failed')
    try:
        for _ in range(2):
            sessions.append(request('/api/v1/auth/demo', {})['access_token'])
        result = request('/predict', {'patient_age': 35, 'chief_complaint': 'Synthetic deployment check: minor ankle pain',
                                     'heart_rate': 75, 'oxygen_saturation': 99}, sessions[0])
        if result.get('is_placeholder') is not False:
            raise RuntimeError('Candidate inference is not using the real model')
        aid = result['assessment_id']
        if request('/assessments', token=sessions[1]):
            raise RuntimeError('Workspace isolation check failed')
        generated = request('/reports/generate', {'assessment_id': aid}, sessions[0])
        pdf = request('/reports/' + generated['report_id'] + '/download', token=sessions[0])
        if not isinstance(pdf, bytes) or not pdf.startswith(b'%PDF'):
            raise RuntimeError('Candidate private PDF check failed')
    finally:
        for token in sessions:
            request('/api/v1/auth/logout', {}, token)
    print('Candidate health, readiness, inference, workspace isolation and private PDF checks passed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--audience', required=True)
    parser.add_argument('--identity-service-account', required=True)
    args = parser.parse_args()
    smoke(args.url, args.audience, args.identity_service_account)
