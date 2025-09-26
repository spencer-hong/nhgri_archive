from flask import Flask, request
from celery.result import AsyncResult

import importlib
import os

# defined in docker-compose.yaml
task_executor_module = importlib.import_module(os.environ.get("TIRAMISU_TASK_EXECUTOR"))
task_executor = task_executor_module.task_executor

# workspace is defined 
actions_module = importlib.import_module('tiramisu.worker')  
workspace = actions_module.workspace 
workspace.task_executor = task_executor

app = Flask(__name__)

# submit tasks to this endpoint
@app.route("/api/action/concurrent", methods=["POST"])
def action_run_post_con():
    action_list = request.json["action_list"]
    print(action_list)
    task_id = task_executor.concurrent(action_list)
    return {"task_id": task_id}

# submit list of tasks to be run in a chain
@app.route("/api/action/chain", methods=["POST"])
def action_run_post_chain():
    action_list = request.json["action_list"]
    task_id = task_executor.chain(action_list)
    return {"task_id": task_id}

# submit requests to view status to this endpoint
# this is not recommended, please use localhost:8000/flower for status
@app.route("/api/status/<task_id>", methods=["GET"])
def status(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }

    return result

# returns the active task list
# should use localhost:8000/flower for active task list
@app.route("/api/task/list", methods=["GET"])
def task_list():
    return {
        "status": "succeeded",
        "active": task_executor.active_task_list()
    }

if __name__ == '__main__':
    app.run("0.0.0.0", 5000)
