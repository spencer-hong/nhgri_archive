import multiprocessing as mp
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple, Set, Union, Sequence, Type
import tiramisu.utils as utils
import celery

class TiramisuContainer:

	def __init__(self, parent, extension = None):
		self.child = None
		self.parent = parent
		self.extension = extension


def group_elements(lst, chunk_size):
	from itertools import islice
	lst = iter(lst)
	return iter(lambda: tuple(islice(lst, chunk_size)), ())

# object containing all tasks of a worker
class ClassHolder():
	name: str
	tasks: List[celery.Task]

	def __init__(self, name, tasks):

		self.name = name
		self.tasks = tasks
		self.keys = [i.name for i in tasks]

@dataclass
class TaskExecutor:

	def cancel_task(self, task_id: str) -> None:
		return None

	def task_status(self, task_id: str) -> Tuple[Any, Any]:
		return ("", "")

	def active_task_list(self) -> List[Any]:
		return []

@dataclass
class Config:
	root: Path

	def __init__(self, root: str):

		self.root = Path(root)


class Context:
	config: Config
	task_executor: Any

	def __init__(self, config: Config, task_executor):
		self.config = config
		self.task_executor = task_executor

	@contextmanager
	def one_to_many(self, file):
		# create an actual folder that is the child of the provided parent
		try:
			current_file = Path(file)
			container = TiramisuContainer(parent=current_file, extension = current_file.suffix )
			yield container
		except FileNotFoundError:
			yield None
		finally:
			pass

	@contextmanager
	def one_to_one(self, file):
		try:
			current_file = Path(file)
			
			container = TiramisuContainer(parent=current_file, extension=current_file.suffix)
			yield container
		except FileNotFoundError:
			yield None
		finally:
			pass


class Workspace:
	config: Config
	task_executor: Any

	def __init__(self, root: str):
		self.config = Config(root)
		self.task_executor = TaskExecutor()

	@contextmanager
	def createContext(self):
		context = Context(self.config, self.task_executor)
		try:
			yield context
		except Exception as ex:
			print(ex)
