from celery import Celery
from conf import celery_config

app = Celery()
app.config_from_object(celery_config)

if __name__ == '__main__':
    app.start()
