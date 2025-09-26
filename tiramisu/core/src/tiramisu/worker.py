from celery import Celery, current_task, states, chain, signature
from celery.result import AsyncResult
from tiramisu.internal import Workspace, TaskExecutor
from typing import Any, List, Dict, Tuple
import os
from celery.result import allow_join_result
import json
import time 
import importlib


import sys 
sys.path.append('')




def find_worker_queue(task_name):

	if task_name.split("_")[-1]  == "ml":
		return "ml_worker"
	elif task_name.split("_")[-1] == "neo4j":
		return "neo4j_worker"
	elif task_name.split("_")[-1] == "labelstudio":
		return "labelstudio_worker"
	elif task_name.split("_")[-1] == "digest":
		return "digest_worker"
	else:
		return None


workspace = Workspace(os.environ.get("TIRAMISU_CONFIG_FILENAME"))


class CeleryTaskExecutor(TaskExecutor):
	def concurrent(self, action_list: List[Dict[str, Any]], opened_tasks = []):

		ids = []
		print(action_list)
		for task in action_list:
			print(task)
			action_kwargs = task.get("kwargs", {})
			
			action = task.get("action")

			# from digest.main import app as digest_worker
			# print(digest_worker.tasks)

			worker = find_worker_queue(action)
			

			if worker is None:
				return {"status": "failed", "error": f"{action} is not a registered task."}
			else:
				ids.append(signature(action, kwargs = action_kwargs, queue = worker).delay().id)
		
		return ids
		
	
	def cancel_task(self, task_id: str):
		celery.control.revoke(task_id, terminate=True)

	def task_status(self, task_id) -> Tuple[Any, Any, Any]:
		result = AsyncResult(task_id)

		return result

	def chain(self, chain):

		print("The following task chain is: \n")
		for i in chain:
			print(f"Task:{i}")
		task_ids = []
		for i in chain:
			print(f"Current task:{i}")

			action_kwargs = i.get("kwargs", {})
			action = i.get("action")

			worker = find_worker_queue(action)
			if worker is None:
				return {"status": "failed", "error": f"{action} is not a registered task."}
			else:
				res = signature(action, kwargs = action_kwargs, immutable = True, queue = worker).delay()
				task_ids.append(res.id)
				print(f"{action} is the task that is waiting at the moment")
				while not res.ready():
					time.sleep(1)
				with allow_join_result():
					_ = res.get(disable_sync_subtasks = True)
				print(f"{action} has now finished.")
			 # will block until finished

		return task_ids

	def active_task_list(self):
		mod = celery.control.inspect()
		return {'active': mod.active(), 'scheduled': mod.scheduled(), 'queued': mod.reserved()}


# Worker needs to set the TaskExecutor to its own Workspace
task_executor = CeleryTaskExecutor()
workspace.task_executor = task_executor
