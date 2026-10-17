"""Release ordering tests use a fake gcloud runner, never cloud credentials."""
import json
import subprocess

import pytest

from scripts import cloud_run_release as release


@pytest.fixture
def config():
    return dict(project='triageai-test', region='northamerica-northeast1', service='triageai-staging',
                artifact_repository='triageai', runtime_account='runtime@triageai-test.iam.gserviceaccount.com',
                migration_account='migrate@triageai-test.iam.gserviceaccount.com',
                cleanup_account='cleanup@triageai-test.iam.gserviceaccount.com',
                smoke_account='smoke@triageai-test.iam.gserviceaccount.com',
                cloud_sql_instance='triageai-test:northamerica-northeast1:demo',
                frontend_origin='https://triageai-demo.netlify.app', report_bucket='triageai-reports',
                runtime_database_secret='runtime-db:1', migration_database_secret='migration-db:2',
                cleanup_database_secret='cleanup-db:3', rate_limit_secret='rate-key:4')


def image(config):
    return f"{config['region']}-docker.pkg.dev/{config['project']}/triageai/backend@sha256:" + 'a' * 64


def test_plan_is_secret_free_and_pins_same_image_for_all_workloads(config, tmp_path):
    plan = release.prepare(config, image(config), tmp_path)
    env = json.loads((tmp_path / 'environment.yaml').read_text())
    assert 'DATABASE_URL' not in env and 'RATE_LIMIT_SECRET' not in env
    assert env['APP_ENV'] == 'staging' and env['AUTO_CREATE_TABLES'] == 'false'
    assert json.loads(env['CORS_ALLOWED_ORIGINS']) == [config['frontend_origin']]
    for name in ('migrate_deploy', 'cleanup_deploy_dry_run', 'service_deploy'):
        command = plan[name]
        assert image(config) in command
        assert config['cloud_sql_instance'] in command
    assert '--apply' not in plan['cleanup_deploy_dry_run']
    assert '--wait' in plan['migrate_execute']
    assert '--no-allow-unauthenticated' in plan['service_deploy']


@pytest.mark.parametrize(('key', 'value'), [('service', 'triageai-production'), ('rate_limit_secret', 'key:latest'),
    ('frontend_origin', 'http://localhost:5173'), ('frontend_origin', 'https://example.com/path'),
    ('cloud_sql_instance', 'wrong-project:wrong-region:demo'), ('project', 'bad\nINJECT=1')])
def test_invalid_deployment_configuration_is_rejected(config, tmp_path, key, value):
    config[key] = value
    with pytest.raises(ValueError):
        release.prepare(config, image(config), tmp_path)
    assert not (tmp_path / 'plan.json').exists()


@pytest.mark.parametrize('failure', [None, 'migration', 'smoke', 'public'])
def test_release_order_and_failure_gates(config, tmp_path, monkeypatch, failure):
    commands = release.prepare(config, image(config), tmp_path)
    calls = []
    def fake(command):
        calls.append(command)
        if 'get-iam-policy' in command:
            return json.dumps({'bindings': [{'members': ['allUsers']}]} if failure == 'public' else {})
        if 'describe' in command:
            return json.dumps({'status': {'url': 'https://canonical.run.app', 'traffic': [
                {'revisionName': 'old', 'percent': 100},
                {'revisionName': 'new', 'tag': 'candidate', 'url': 'https://candidate.run.app'},
            ]}})
        if (failure == 'migration' and command == commands['migrate_execute']) or (failure == 'smoke' and 'scripts/cloud_smoke.py' in command):
            raise subprocess.CalledProcessError(1, command)
        return ''
    monkeypatch.setattr(release, 'run', fake)
    if failure:
        with pytest.raises((ValueError, subprocess.CalledProcessError)):
            release.release(config, commands, image(config), tmp_path)
        assert not any('update-traffic' in c for c in calls)
        if failure in {'migration', 'public'}:
            assert not any('candidate' in c for c in calls)
    else:
        release.release(config, commands, image(config), tmp_path)
        migration_index = calls.index(commands['migrate_execute'])
        deploy_index = next(i for i, c in enumerate(calls) if '--no-traffic' in c)
        smoke_index = next(i for i, c in enumerate(calls) if 'scripts/cloud_smoke.py' in c)
        promotion_index = next(i for i, c in enumerate(calls) if 'update-traffic' in c)
        assert migration_index < deploy_index < smoke_index < promotion_index
        assert json.loads((tmp_path / 'release.json').read_text())['previous_revision'] == 'old'


@pytest.mark.parametrize('bad_pdf', [False, True])
def test_smoke_uses_separate_iam_and_app_tokens_and_revokes_sessions(monkeypatch, capsys, bad_pdf):
    from scripts import cloud_smoke
    calls = []
    class Identity:
        stdout = 'secret-iam-token\n'
    monkeypatch.setattr(cloud_smoke.subprocess, 'run', lambda *a, **k: Identity())
    class Response:
        def __init__(self, data):
            self.data = data
            self.headers = {'Content-Type': 'application/pdf' if isinstance(data, bytes) else 'application/json'}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, size):
            return self.data if isinstance(self.data, bytes) else json.dumps(self.data).encode()
    def open_request(req, timeout):
        path = req.full_url.removeprefix('https://candidate.run.app')
        calls.append((path, dict(req.header_items())))
        assert req.get_header('X-serverless-authorization') == 'Bearer secret-iam-token'
        if path == '/health':
            return Response({'status': 'ok'})
        if path == '/ready':
            return Response(dict(status='ready', schema_current=True, model_loaded=True, is_placeholder=False))
        if path == '/api/v1/auth/demo':
            return Response({'access_token': 'secret-app-' + str(len(calls))})
        if path == '/predict':
            assert req.get_header('Authorization').startswith('Bearer secret-app-')
            return Response({'assessment_id': 'synthetic-assessment', 'is_placeholder': False})
        if path == '/assessments':
            return Response([])
        if path == '/reports/generate':
            return Response({'report_id': 'synthetic-report'})
        if path.endswith('/download'):
            return Response(b'not-a-pdf' if bad_pdf else b'%PDF-synthetic')
        if path == '/api/v1/auth/logout':
            response = Response(b'')
            response.headers = {'Content-Type': 'application/json'}
            return response
        raise AssertionError(path)
    monkeypatch.setattr(cloud_smoke, 'urlopen', open_request)
    if bad_pdf:
        with pytest.raises(RuntimeError, match='PDF'):
            cloud_smoke.smoke('https://candidate.run.app', 'https://canonical.run.app', 'smoke@example.com')
    else:
        cloud_smoke.smoke('https://candidate.run.app', 'https://canonical.run.app', 'smoke@example.com')
    assert sum(path.endswith('/logout') for path, _ in calls) == 2
    assert 'secret-' not in capsys.readouterr().out
