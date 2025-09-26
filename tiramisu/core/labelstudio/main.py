from tiramisu.internal import ClassHolder
import celery
from celery.app.registry import TaskRegistry

from labelstudio.tasks.utils import show_me_in_labelstudio



app = celery.Celery()

app.conf.task_routes = {
    '*_ml': {'queue': 'ml_worker'},
    '*_neo4j': {'queue': 'neo4j_worker'},
    '*_digest': {'queue': 'digest_worker'},
    '*_labelstudio': {'queue': 'labelstudio_worker'}
} # update worker queue


# start worker
if __name__ == '__main__':
    app.worker_main()
