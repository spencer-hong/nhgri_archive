import os
import zlib
from stat import S_IREAD, S_IWRITE, S_IEXEC
from shutil import copy, rmtree
from pathlib import Path
import hashlib
import traceback
import celery
from celery.app.registry import TaskRegistry
import uuid
import time
import json
from urllib import request, parse

def check_status(list_of_ids):
	for task_id in list_of_ids:
		status = 'PENDING'
		while status != 'SUCCESS':
			time.sleep(1)
			url = f"http://flask:5000/api/status/{task_id}"
			res = request.urlopen(url)
			# res.add_header("Content-Type", "application/json")
			status = json.loads(res.read())['task_status']
	
	return True


class TiramisuException(Exception):
	message: str

	def __init__(self, message: str):
		self.message = message
		super().__init__(message)

	def __str__(self):
		return f"{self.message}"



def crc32(data):
	data = bytes(data, 'UTF-8')

	return hex(zlib.crc32(data) & 0xffffffff)  # crc32 returns a signed value, &-ing it will match py3k


def generate_id(path, data = None):

	if data is None:
		with open(path, "rb") as f:
			hexs = crc32(str(f.read()))
	else:
		hexs = crc32(str(data))

	return  hexs + "+++" + crc32(path.as_posix())



def tiramisu_update(context, container, data = None):


	try:
		# parent should always be a full path with new name

		if data is None:
			node_id = generate_id(Path(container.parent))
		else:
			node_id = generate_id(Path(container.parent), data)

		if container.extension is None:
			pass
		else:

			(context.config.root / ".tiramisu"/ '___tiramisu_versions' / node_id).mkdir()
		
		# child should always be the new folder with nodeID in tiramisu_versions
		container.child = context.config.root / ".tiramisu"/ '___tiramisu_versions' / node_id
		# container.child = (context.config.root / '__tiramisu_versions' / node_id / (node_id + f'.{container.extension}'))

		return container
	except:
		raise TiramisuException(traceback.format_exc())

def copy_files(source_path, to_path):
	copy(source_path, to_path)


def write_gitignore(path):
	copy_files(os.path.dirname(os.path.abspath(__file__)) + '/_gitignore_template', Path(path) / '.gitignore')

# removing a non-empty folder

def remove_folder(path):
	rmtree(path)


def lock_files_read_only(filepath):

	# Replace the first parameter with your file name
	os.chmod(filepath, S_IREAD)


def unlock_files_read_only(filepath):
	os.chmod(filepath, S_IREAD | S_IWRITE | S_IEXEC)
