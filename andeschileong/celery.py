import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'andeschileong.settings')

app = Celery('andeschileong')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
