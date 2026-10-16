"""Prepare or execute a private staging release. No resource bootstrap or public IAM grants."""
import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

REQUIRED = {'project', 'region', 'service', 'artifact_repository', 'runtime_account', 'migration_account',
            'cleanup_account', 'smoke_account', 'cloud_sql_instance', 'frontend_origin', 'report_bucket',
            'runtime_database_secret', 'migration_database_secret', 'cleanup_database_secret', 'rate_limit_secret'}


def validate(config, image):
    if set(config) != REQUIRED or any(not isinstance(v, str) for v in config.values()):
        raise ValueError('Configuration must contain exactly the documented string fields')
    if any('REPLACE' in v for v in config.values()):
        raise ValueError('Replace example configuration values before use')
    for key in ('project', 'region', 'service', 'artifact_repository', 'report_bucket'):
        if not re.fullmatch(r'[a-z][a-z0-9-]{2,50}', config[key]):
            raise ValueError(f'Invalid {key}')
    if not config['service'].endswith('-staging'):
        raise ValueError('This release tool is restricted to staging service names')
    for key in ('runtime_account', 'migration_account', 'cleanup_account', 'smoke_account'):
        if not re.fullmatch(r'[a-z][a-z0-9-]+@' + re.escape(config['project']) + r'\.iam\.gserviceaccount\.com', config[key]):
            raise ValueError(f'Invalid {key}')
    if len({config[k] for k in ('runtime_account', 'migration_account', 'cleanup_account')}) != 3:
        raise ValueError('Runtime, migration and cleanup identities must differ')
    for key in ('runtime_database_secret', 'migration_database_secret', 'cleanup_database_secret', 'rate_limit_secret'):
        if not re.fullmatch(r'[A-Za-z0-9_-]+:[1-9][0-9]*', config[key]):
            raise ValueError(f'{key} must pin a numeric Secret Manager version')
    if len({config[k] for k in ('runtime_database_secret', 'migration_database_secret', 'cleanup_database_secret')}) != 3:
        raise ValueError('Database secret references must be separate')
    origin = urlparse(config['frontend_origin'])
    if origin.scheme != 'https' or not origin.hostname or origin.username or origin.password or origin.path not in ('', '/') or origin.query or origin.fragment or origin.hostname in {'localhost', '127.0.0.1'}:
        raise ValueError('Frontend origin must be an explicit HTTPS origin')
    instance = config['cloud_sql_instance']
    if instance and not re.fullmatch(re.escape(config['project'] + ':' + config['region'] + ':') + r'[a-z][a-z0-9-]+', instance):
        raise ValueError('Cloud SQL instance must match project and region, or be empty for external PostgreSQL')
    prefix = f"{config['region']}-docker.pkg.dev/{config['project']}/{config['artifact_repository']}/backend@sha256:"
    if not image.startswith(prefix) or not re.fullmatch(r'[a-f0-9]{64}', image[len(prefix):]):
        raise ValueError('Image must be an immutable backend digest in the configured Artifact Registry')


def prepare(config, image, output):
    validate(config, image)
    output.mkdir(parents=True, exist_ok=True)
    env = {'APP_ENV': 'staging', 'DEBUG': 'false', 'AUTO_CREATE_TABLES': 'false',
           'CORS_ALLOWED_ORIGINS': json.dumps([config['frontend_origin'].rstrip('/')]),
           'REPORT_STORAGE_BACKEND': 'gcs', 'REPORT_GCS_BUCKET': config['report_bucket'],
           'DATABASE_POOL_SIZE': '3', 'DATABASE_MAX_OVERFLOW': '0', 'SESSION_TTL_MINUTES': '60',
           'PUBLIC_DEMO_ENABLED': 'true'}
    env_file = output / 'environment.yaml'
    # JSON is a YAML subset accepted by gcloud; no secret values are written here.
    env_file.write_text(json.dumps(env, indent=2) + '\n')
    common = ['--project', config['project'], '--region', config['region'], '--quiet']
    connection = ['--set-cloudsql-instances', config['cloud_sql_instance']] if config['cloud_sql_instance'] else []
    def job(name, identity, database, args):
        return ['gcloud', 'run', 'jobs', 'deploy', config['service'] + '-' + name, *common,
                '--image', image, '--service-account', config[identity], '--env-vars-file', str(env_file),
                '--set-secrets', f"DATABASE_URL={config[database]},RATE_LIMIT_SECRET={config['rate_limit_secret']}",
                *connection, '--command', 'python', '--args=' + ','.join(args), '--tasks', '1', '--parallelism', '1',
                '--max-retries', '0', '--task-timeout', '600s', '--cpu', '1', '--memory', '1Gi']
    migrate = job('migrate', 'migration_account', 'migration_database_secret', ['-m', 'alembic', 'upgrade', 'head'])
    cleanup = job('cleanup', 'cleanup_account', 'cleanup_database_secret', ['scripts/cleanup_demo_data.py'])
    service = ['gcloud', 'run', 'deploy', config['service'], *common, '--image', image,
               '--service-account', config['runtime_account'], '--env-vars-file', str(env_file),
               '--set-secrets', f"DATABASE_URL={config['runtime_database_secret']},RATE_LIMIT_SECRET={config['rate_limit_secret']}",
               *connection, '--port', '8001', '--execution-environment', 'gen2', '--cpu', '1', '--memory', '1Gi',
               '--concurrency', '8', '--min-instances', '0', '--max-instances', '2', '--timeout', '60s',
               '--no-allow-unauthenticated', '--tag', 'candidate',
               '--startup-probe', 'httpGet.path=/ready,httpGet.port=8001,periodSeconds=10,failureThreshold=24,timeoutSeconds=5']
    commands = {'migrate_deploy': migrate,
                'migrate_execute': ['gcloud', 'run', 'jobs', 'execute', config['service'] + '-migrate', *common, '--wait'],
                'cleanup_deploy_dry_run': cleanup, 'service_deploy': service}
    (output / 'plan.json').write_text(json.dumps(commands, indent=2) + '\n')
    return commands


def run(command):
    return subprocess.run(command, check=True, text=True, capture_output=True).stdout


def release(config, commands, image, output):
    common = ['--project', config['project'], '--region', config['region'], '--quiet']
    # Existing service only: first deployment and IAM bootstrap are separate reviewed operations.
    before = json.loads(run(['gcloud', 'run', 'services', 'describe', config['service'], *common, '--format=json']))
    if before.get('metadata', {}).get('annotations', {}).get('run.googleapis.com/invoker-iam-disabled') == 'true':
        raise ValueError('Staging invoker IAM checks must be enabled')
    policy = json.loads(run(['gcloud', 'run', 'services', 'get-iam-policy', config['service'], *common, '--format=json']))
    if any(member in {'allUsers', 'allAuthenticatedUsers'} for binding in policy.get('bindings', []) for member in binding.get('members', [])):
        raise ValueError('Staging must remain IAM-private before this release')
    traffic = [t for t in before['status'].get('traffic', []) if t.get('percent', 0)]
    if len(traffic) != 1 or traffic[0]['percent'] != 100 or not traffic[0].get('revisionName'):
        raise ValueError('Expected one known revision receiving 100% traffic; inspect existing rollout')
    previous = traffic[0]['revisionName']
    (output / 'release.json').write_text(json.dumps({'previous_revision': previous, 'image': image}, indent=2))
    for key in ('migrate_deploy', 'migrate_execute', 'cleanup_deploy_dry_run'):
        run(commands[key])
    # Existing private IAM is verified above and retained; CI does not need setIamPolicy.
    deploy = [arg for arg in commands['service_deploy'] if arg != '--no-allow-unauthenticated']
    run([*deploy, '--no-traffic'])
    after = json.loads(run(['gcloud', 'run', 'services', 'describe', config['service'], *common, '--format=json']))
    candidate = next(t for t in after['status']['traffic'] if t.get('tag') == 'candidate')
    (output / 'release.json').write_text(json.dumps({'previous_revision': previous,
        'candidate_revision': candidate['revisionName'], 'image': image, 'smoke_passed': False}, indent=2))
    run(['python', 'scripts/cloud_smoke.py', '--url', candidate['url'], '--audience', after['status']['url'],
         '--identity-service-account', config['smoke_account']])
    # Private staging only. Public release is outside this workflow.
    run(['gcloud', 'run', 'services', 'update-traffic', config['service'], *common,
         '--to-revisions', candidate['revisionName'] + '=100'])
    (output / 'release.json').write_text(json.dumps({'previous_revision': previous,
        'candidate_revision': candidate['revisionName'], 'image': image, 'smoke_passed': True}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    commands = prepare(config, args.image, args.output)
    if args.apply:
        release(config, commands, args.image, args.output)
    print(json.dumps({'dry_run': not args.apply, 'plan': str(args.output / 'plan.json')}))


if __name__ == '__main__':
    main()
