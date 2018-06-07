BROKER_URL = 'amqp://devops:devops@10.10.50.30/publish'
CELERY_RESULT_BACKEND = 'rpc://'
CELERY_RESULT_PERSISTENT = True
CELERY_TASK_SERIALIZER = 'msgpack'
CELERY_RESULT_SERIALIZER = 'json'
CELERYD_TASK_SOFT_TIME_LIMIT = 300
CELERY_TASK_RESULT_EXPIRES = 60 * 60 * 24 * 7
CELERY_ACCEPT_CONTENT = ['json', 'msgpack']
CELERYD_MAX_TASKS_PER_CHILD = 200
CELERYD_CONCURRENCY = 20
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_INCLUDE = ['tasks.cmdb_agent', 'tasks.nginx', 'tasks.dubbo', 'tasks.zabbix_agent',
                  'tasks.get_package', 'tasks.rollback', 'tasks.deploy', 'tasks.service', 'tasks.send_shell',
                  'tasks.callback', 'tasks.log_task', 'tasks.publish_plan']
