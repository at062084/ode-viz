import os
from celery.schedules import crontab

# Superset specific config
ROW_LIMIT = 5000

# Flask App Builder configuration
# Your App secret key will be used for securely signing the session cookie
# and encrypting sensitive information on the database
# Make sure you are changing this key for production
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'changeme-secretkey-for-production')

# The SQLAlchemy connection string to your database backend
# This connection defines the path to the database that stores your
# superset metadata (slices, connections, tables, dashboards, ...)
SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(
    os.environ.get('DATABASE_USER', 'superset'),
    os.environ.get('DATABASE_PASSWORD', 'superset'),
    os.environ.get('DATABASE_HOST', 'postgres'),
    os.environ.get('DATABASE_PORT', '5432'),
    os.environ.get('DATABASE_DB', 'superset')
)

# Redis configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

# Cache configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_HOST': REDIS_HOST,
    'CACHE_REDIS_PORT': REDIS_PORT,
    'CACHE_REDIS_DB': 1,
}

DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_data_',
    'CACHE_REDIS_HOST': REDIS_HOST,
    'CACHE_REDIS_PORT': REDIS_PORT,
    'CACHE_REDIS_DB': 2,
}

# Celery configuration
class CeleryConfig:
    broker_url = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
    imports = ('superset.sql_lab', 'superset.tasks')
    result_backend = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        'sql_lab.get_sql_results': {
            'rate_limit': '100/s',
        },
    }
    beat_schedule = {
        'reports.scheduler': {
            'task': 'reports.scheduler',
            'schedule': crontab(minute=0, hour=0),
        },
        'reports.prune_log': {
            'task': 'reports.prune_log',
            'schedule': crontab(minute=0, hour=0),
        },
    }

CELERY_CONFIG = CeleryConfig

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True
# Add endpoints that need to be exempt from CSRF protection
WTF_CSRF_EXEMPT_LIST = []
# A CSRF token that expires in 1 year
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365

# Set this API key to enable Mapbox visualizations
MAPBOX_API_KEY = os.environ.get('MAPBOX_API_KEY', '')

# Feature flags
FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING': True,
    'DASHBOARD_NATIVE_FILTERS': True,
    'DASHBOARD_CROSS_FILTERS': True,
    'DASHBOARD_RBAC': True,
    'EMBEDDED_SUPERSET': True,
    'ALERT_REPORTS': True,
}

# Additional configuration
ENABLE_PROXY_FIX = True
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'resources': ['*'],
    'origins': ['*']
}

# Async query configuration
GLOBAL_ASYNC_QUERIES_REDIS_CONFIG = {
    'port': REDIS_PORT,
    'host': REDIS_HOST,
    'db': 3,
}

# SQL Lab configuration
SUPERSET_WEBSERVER_TIMEOUT = 300
SQLLAB_ASYNC_TIME_LIMIT_SEC = 300
SQLLAB_TIMEOUT = 300
