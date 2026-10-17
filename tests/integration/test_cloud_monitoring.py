"""Local tests; no cloud credentials or external requests."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.configure_cloud_monitoring import Monitoring, contains, main, policies, uptime


class MonitoringTests(unittest.TestCase):
    def test_dry_run_never_authenticates(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(sys, 'argv', ['monitor', '--email', 'operator@example.com', '--output', folder]), patch('scripts.configure_cloud_monitoring.Monitoring') as api, contextlib.redirect_stdout(io.StringIO()):
                main()
            api.assert_not_called()
            plan = json.loads((Path(folder) / 'plan.json').read_text())
            self.assertEqual(len(plan['uptimeChecks']), 2)
            self.assertEqual(len(plan['alertPolicies']), 5)
            self.assertFalse((Path(folder) / 'created.json').exists())

    def test_alerts_target_actual_demo_and_cleanup(self):
        rules = policies('channels/1', {'API': 'check-1', 'frontend': 'check-2'})
        self.assertTrue(all(p['notificationChannels'] == ['channels/1'] for p in rules))
        self.assertIn('service_name="triageai-demo"', rules[2]['conditions'][0]['conditionThreshold']['filter'])
        self.assertEqual(rules[2]['conditions'][0]['conditionThreshold']['thresholdValue'], 4)
        self.assertIn('jsonPayload.failed_workspaces>0', rules[3]['conditions'][0]['conditionMatchedLog']['filter'])
        self.assertEqual(rules[4]['conditions'][0]['conditionAbsent']['duration'], '10800s')
        check = uptime('health', 'example.com', '/health')
        self.assertTrue(check['httpCheck']['validateSsl'])
        self.assertEqual(check['period'], '900s')

    def test_reuses_match_on_later_page(self):
        api = object.__new__(Monitoring)
        desired = {'displayName': 'existing', 'enabled': True}
        with patch.object(api, 'request', side_effect=[{'nextPageToken': 'next'}, {'alertPolicies': [dict(desired, name='policies/1')]}]) as request, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(api.ensure('alertPolicies', 'alertPolicies', desired)['name'], 'policies/1')
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args.args, ('GET', 'alertPolicies?pageToken=next'))

    def test_drift_and_duplicate_refuse_mutation(self):
        api = object.__new__(Monitoring)
        for rows in [[{'displayName': 'existing', 'enabled': False}], [{'displayName': 'existing'}]*2]:
            with patch.object(api, 'request', return_value={'alertPolicies': rows}) as request:
                with self.assertRaises(RuntimeError):
                    api.ensure('alertPolicies', 'alertPolicies', {'displayName': 'existing', 'enabled': True})
                self.assertEqual(request.call_count, 1)

    def test_creates_only_when_missing(self):
        api = object.__new__(Monitoring)
        desired = {'displayName': 'new'}
        with patch.object(api, 'request', side_effect=[{}, {'name': 'policies/2'}]) as request, contextlib.redirect_stdout(io.StringIO()):
            api.ensure('alertPolicies', 'alertPolicies', desired)
        self.assertEqual(request.call_args.args, ('POST', 'alertPolicies', desired))
        self.assertTrue(contains({'name': 'extra', 'values': [1]}, {'values': [1]}))
        self.assertFalse(contains({'values': [1, 2]}, {'values': [1]}))
        self.assertTrue(contains({}, {'groupByFields': []}))


if __name__ == '__main__':
    unittest.main()
