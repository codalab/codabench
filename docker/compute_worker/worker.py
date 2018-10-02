from billiard.exceptions import SoftTimeLimitExceeded
from celery import Celery, task


app = Celery('worker')
app.config_from_object('celeryconfig')



@task(name="compute_worker_run")
def run_wrapper(run_arguments):
    try:
        run(run_arguments)
    except SoftTimeLimitExceeded:
        print("soft-a time-a limit-a exceeded-a")
        pass
        # _send_update(task_id, {'status': 'failed'}, task_args['secret'])


def run(run_arguments):
    print("We hit this!")
    print(run_arguments)
    pass

