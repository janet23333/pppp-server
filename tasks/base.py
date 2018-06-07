import celery


class CallbackTask(celery.Task):
    def on_success(self, retval, task_id, args, kwargs):
        print(
            'call back on  success and taskid is {} ,retval is{} ,args is{}.kwargs id {}'.format(task_id, retval, args,
                                                                                                 kwargs))

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print('{0!r} failed: {1!r}'.format(task_id, exc))
