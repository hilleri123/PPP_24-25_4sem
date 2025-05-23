import redislite
from celery import Celery


rdb = redislite.Redis('/tmp/redis.db')

REDIS_SOCKET_PATH = 'redis+socket://%s' % (rdb.socket_file,)

app = Celery(
    'worker',
    broker=REDIS_SOCKET_PATH,
    backend=REDIS_SOCKET_PATH,
    include=["app.celery.tasks"],
)

app.autodiscover_tasks(["app.celery.tasks"])
