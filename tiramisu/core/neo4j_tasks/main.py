from tiramisu.internal import ClassHolder
import celery

from neo4j_tasks.tasks.update import add_node_neo4j, write_neo4j, update_metadata_neo4j, query_neo4j, load_csv_neo4j

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
