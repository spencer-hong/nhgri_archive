from tiramisu.internal import ClassHolder

import celery


from digest.tasks.initial import digest
from digest.tasks.convert import pdf_to_image_supervisor, doc_to_pdf_supervisor, docx_to_pdf_supervisor, split_pdfs_supervisor

# create celery app
app = celery.Celery()

app.conf.task_routes = {
    '*_ml': {'queue': 'ml_worker'},
    '*_neo4j': {'queue': 'neo4j_worker'},
    '*_digest': {'queue': 'digest_worker'},
    '*_labelstudio': {'queue': 'labelstudio_worker'}
} # update worker queue


if __name__ == '__main__':
    app.worker_main()