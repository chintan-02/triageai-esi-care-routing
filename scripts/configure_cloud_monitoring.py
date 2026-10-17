"""Plan or create demo monitoring. Dry-run by default; never prints access tokens."""
import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def uptime(name, host, path):
    return {
        'displayName': name,
        'monitoredResource': {'type': 'uptime_url', 'labels': {
            'project_id': 'triageai-chintan-2026', 'host': host}},
        'httpCheck': {'path': path, 'port': 443, 'useSsl': True,
                      'validateSsl': True, 'requestMethod': 'GET',
                      'acceptedResponseStatusCodes': [{'statusValue': 200}]},
        'period': '900s', 'timeout': '30s', 'checkerType': 'STATIC_IP_CHECKERS',
    }


def policies(channel, checks):
    result = []
    def add(name, condition, guidance, log=False):
        strategy = {'autoClose': '86400s'}
        if log:
            strategy['notificationRateLimit'] = {'period': '3600s'}
        result.append({'displayName': name, 'enabled': True, 'combiner': 'OR',
                       'notificationChannels': [channel], 'alertStrategy': strategy,
                       'documentation': {'mimeType': 'text/markdown', 'content': guidance},
                       'conditions': [dict(displayName=name, **condition)]})

    for label, identifier in checks.items():
        add('TriageAI demo ' + label + ' unavailable', {'conditionThreshold': {
            'filter': 'metric.type="monitoring.googleapis.com/uptime_check/check_passed" '
                      'AND resource.type="uptime_url" AND metric.labels.check_id="' + identifier + '"',
            'comparison': 'COMPARISON_GT', 'thresholdValue': 1, 'duration': '300s',
            'aggregations': [{'alignmentPeriod': '1200s', 'perSeriesAligner': 'ALIGN_NEXT_OLDER',
                              'crossSeriesReducer': 'REDUCE_COUNT_FALSE', 'groupByFields': []}],
            'trigger': {'count': 1}}},
            'At least two checker locations report failure. Check Netlify deploys or Cloud Run '
            'revision/startup logs. API /health does not test database readiness. '
            'Run /ready and the synthetic smoke test separately. See docs/deployment/live-demo-runbook.md.')

    add('TriageAI demo API 5xx burst', {'conditionThreshold': {
        'filter': 'metric.type="run.googleapis.com/request_count" AND resource.type="cloud_run_revision" '
                  'AND resource.labels.service_name="triageai-demo" '
                  'AND resource.labels.location="northamerica-northeast1" '
                  'AND metric.labels.response_code_class="5xx"',
        'comparison': 'COMPARISON_GT', 'thresholdValue': 4, 'duration': '0s',
        'aggregations': [{'alignmentPeriod': '300s', 'perSeriesAligner': 'ALIGN_SUM',
                          'crossSeriesReducer': 'REDUCE_SUM', 'groupByFields': []}],
        'trigger': {'count': 1}}},
        'Five or more container 5xx responses in five minutes. Inspect request/error logs, '
        'database connections and memory. Do not log tokens or patient text. '
        'This metric excludes requests rejected before reaching a container.')

    add('TriageAI demo cleanup failure', {'conditionMatchedLog': {
        'filter': 'resource.type="cloud_run_job" '
                  'AND resource.labels.job_name="triageai-staging-cleanup" '
                  'AND (severity>=ERROR OR jsonPayload.failed_workspaces>0 '
                  'OR protoPayload.status.code>0)'}},
        'Inspect the exact cleanup execution and its structured summary. Check DB permissions, '
        'GCS object-delete access and secret versions. Retry after resolving the cause; '
        'do not manually delete database metadata before report objects.', log=True)

    add('TriageAI demo cleanup heartbeat missing', {'conditionAbsent': {
        'filter': 'metric.type="run.googleapis.com/job/completed_execution_count" '
                  'AND resource.type="cloud_run_job" '
                  'AND resource.labels.job_name="triageai-staging-cleanup" '
                  'AND resource.labels.location="northamerica-northeast1"',
        'duration': '10800s', 'aggregations': [
            {'alignmentPeriod': '300s', 'perSeriesAligner': 'ALIGN_SUM',
             'crossSeriesReducer': 'REDUCE_SUM', 'groupByFields': []}],
        'trigger': {'count': 1}}},
        'No cleanup completion metric for three hours. Inspect Scheduler state, OAuth identity, '
        'job Invoker IAM and running executions. Failure alerts separately cover failed runs. '
        'An absence alert needs an established time series and does not reliably detect deleted resources.')
    return result


def contains(actual, desired):
    if isinstance(desired, dict):
        return isinstance(actual, dict) and all(contains(actual.get(k, [] if v == [] else None), v) for k, v in desired.items())
    if isinstance(desired, list):
        return isinstance(actual, list) and len(actual) == len(desired) and all(contains(a, d) for a, d in zip(actual, desired))
    return actual == desired


class Monitoring:
    def __init__(self, project):
        self.project = project
        self.token = subprocess.run(['gcloud', 'auth', 'print-access-token'], check=True,
                                    capture_output=True, text=True).stdout.strip()

    def request(self, method, suffix, body=None):
        req = Request('https://monitoring.googleapis.com/v3/projects/' + self.project + '/' + suffix,
                      method=method, headers={'Authorization': 'Bearer ' + self.token,
                                              'Content-Type': 'application/json'},
                      data=json.dumps(body).encode() if body is not None else None)
        try:
            with urlopen(req, timeout=60) as response:
                return json.load(response)
        except HTTPError as exc:
            raise RuntimeError('Monitoring API HTTP ' + str(exc.code) + ': ' + exc.read().decode()) from None

    def ensure(self, collection, key, desired):
        items, page = [], None
        while True:
            suffix = collection + ('?' + urlencode({'pageToken': page}) if page else '')
            response = self.request('GET', suffix)
            items.extend(response.get(key, []))
            page = response.get('nextPageToken')
            if not page:
                break
        matches = [item for item in items if item.get('displayName') == desired['displayName']]
        if len(matches) > 1:
            raise RuntimeError('Duplicate display name: ' + desired['displayName'])
        if matches:
            if not contains(matches[0], desired):
                raise RuntimeError('Existing configuration differs; inspect before updating: ' + desired['displayName'])
            print('Verified existing:', desired['displayName'])
            return matches[0]
        created = self.request('POST', collection, desired)
        print('Created:', desired['displayName'])
        return created


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--email', required=True, help='Operator notification email; not a credential')
    parser.add_argument('--output', type=Path, default=Path('/tmp/triageai-monitoring-plan'))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', args.email):
        parser.error('Provide a valid notification email')
    project = 'triageai-chintan-2026'
    channel = {'type': 'email', 'displayName': 'TriageAI demo operator',
               'labels': {'email_address': args.email}, 'enabled': True}
    checks = {
        'API': uptime('TriageAI demo API health', 'triageai-demo-3mn3ubivua-nn.a.run.app', '/health'),
        'frontend': uptime('TriageAI demo frontend', 'triageai-chintan-staging.netlify.app', '/login'),
    }
    plan = {'notificationChannel': channel, 'uptimeChecks': checks,
            'alertPolicies': policies('CHANNEL_RESOURCE_NAME', {'API': 'API_CHECK_ID', 'frontend': 'FRONTEND_CHECK_ID'})}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    if not args.apply:
        print('Dry run; no cloud calls. Plan:', args.output / 'plan.json')
        return
    api = Monitoring(project)
    saved_channel = api.ensure('notificationChannels', 'notificationChannels', channel)
    identifiers = {label: api.ensure('uptimeCheckConfigs', 'uptimeCheckConfigs', check)['name'].rsplit('/', 1)[1]
                   for label, check in checks.items()}
    saved_policies = [api.ensure('alertPolicies', 'alertPolicies', policy)['name']
                      for policy in policies(saved_channel['name'], identifiers)]
    state = {'channel': saved_channel['name'], 'checks': identifiers, 'policies': saved_policies,
             'email_verification_status': saved_channel.get('verificationStatus', 'UNSPECIFIED')}
    (args.output / 'created.json').write_text(json.dumps(state, indent=2) + '\n')
    print('Monitoring resources configured. Validate notification delivery and checker results in Console.')


if __name__ == '__main__':
    main()
