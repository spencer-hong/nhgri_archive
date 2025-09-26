from celery import signature, shared_task, states
from celery.result import allow_join_result

from pathlib import Path
from tiramisu.utils import tiramisu_update, TiramisuException, check_status
from tiramisu.internal import group_elements
import importlib
import sys
import time 
sys.path.append('')
import traceback


import subprocess


## split PDF, find scanned/electronic PDFs, convert PDFS to images (all), do selective OCR
## convert doc to docx, convert docx to PDFs, convert PDFS to images (must find just the PDFs coming from word files), do tika on docx
def page_type(page):

	import fitz
	page_area = abs(page.rect) # Total page area
	img_area = 0.0
	for block in page.get_text("RAWDICT")["blocks"]:
		if block["type"] == 1: # Type=1 are images
			bbox=block["bbox"]
			img_area += (bbox[2]-bbox[0])*(bbox[3]-bbox[1]) # width*height
	img_perc = img_area / page_area

	text_area = 0.0
	for b in page.get_text_blocks():
		r = fitz.Rect(b[:4])  # Rectangle where block text appears
		text_area = text_area + abs(r)
	text_perc = text_area / page_area

	if text_perc < 0.01: #No text = Scanned
		page_type = "Scanned"
	elif img_perc > .8:  #Has text but very large images = Searchable
		page_type = "Searchable text" 
	else:
		page_type = "Digitally created"
	return page_type

@shared_task(name = "pdf_to_image_supervisor_digest")
def pdf_to_image_supervisor():
	query = """
	MATCH (n:File) - [:SPLIT_INTO] -> (m: File)
	WHERE m.fileExtension = "pdf"
	WITH collect(distinct m) as nodes
	UNWIND nodes as node
	return node.nodeID as nodeID, node.tiramisuPath as path, node.page as page
	"""

	from neo4j_tasks.main import app as neo4j_worker


	ret = (neo4j_worker.tasks["query_neo4j"].s(query) | ( pdf_to_image_chunk.s())).apply_async()

	while not ret.ready():
		time.sleep(1)
	with allow_join_result():
		return ret.get(disable_sync_subtasks = True)

@shared_task(name = "pdf_to_image_chunk_digest")
def pdf_to_image_chunk(queryrows):
	if len(queryrows) == 0:
		return 
	ret = pdf_to_image.chunks(zip(queryrows),  1).apply_async(queue = "digest_worker")

	while not ret.ready():
		time.sleep(1)
	with allow_join_result():
		return ret.get(disable_sync_subtasks = True)

@shared_task(name = "pdf_to_image_digest")
def pdf_to_image(queryrows):

	import fitz
	from neo4j_tasks.main import app as neo4j_worker

	actions_module = importlib.import_module('tiramisu.worker') 
	workspace = actions_module.workspace

	try:
		filename = queryrows['path']
		with workspace.createContext() as context:
			if not Path(filename).is_file():
				print(f"{filename} was not a file.")
			else:
				with context.one_to_one(filename) as p:
					mat = fitz.Matrix(300 / 72, 300 / 72) #300 DPI
					doc = fitz.open(p.parent)
					page = doc.load_page(0)  # number of page
					pix = page.get_pixmap(matrix = mat)

					p = tiramisu_update(context, p, data = pix)
					nodeID = p.child.name
					p.child = (Path(p.child) / f"{Path(p.parent).stem}.png")


					page = queryrows['page']

					pix.save(p.child)
					ret = neo4j_worker.tasks['add_node_neo4j'].s(nodeID = str(nodeID), label = "File", parentID = queryrows['nodeID'], relationship =  'CONVERT_TO', attributes = {"name":Path(filename).stem + ".png", "tiramisuPath": (p.child).as_posix(), "fileExtension":'png',  'page': str(page)}).apply_async()

					while not ret.ready():
						time.sleep(1)
		with allow_join_result():
			return ret.get(disable_sync_subtasks = True)

	except Exception as ex:
		# raise Ignore()
		pdf_to_image.update_state(
		state=states.FAILURE,
		meta={
			'exc_type': type(ex).__name__,
			'exc_message': traceback.format_exc().split('\n')
		})
		# raise ex
		return traceback.format_exc()

@shared_task(name ="split_pdfs_supervisor_digest")
def split_pdfs_supervisor():

	query = """
MATCH (n:Folder) - [:CONTAINS] -> (m:File)  
	WHERE m.fileExtension = "pdf" 
	return m.nodeID as nodeID, m.tiramisuPath as path
	UNION 
	match (c:Folder) - [:CONTAINS] -> (d:File) - [:CONVERT_TO] -> (e:File)  
	where e.fileExtension = "pdf"  
	return e.nodeID as nodeID, e.tiramisuPath as path  
	"""

	from neo4j_tasks.main import app as neo4j_worker

	ret = (neo4j_worker.tasks['query_neo4j'].s(query) | ( split_pdfs_chunk.s())).apply_async()

	while not ret.ready():
		time.sleep(1)
	

	with allow_join_result():
		return ret.get(disable_sync_subtasks = True)


@shared_task(name = 'split_pdfs_chunk_digest')
def split_pdfs_chunk(queryrows):

	if len(queryrows) == 0:
		return 
	ret = split_pdfs.chunks(zip(queryrows), 1).apply_async(queue = 'digest_worker')

	while not ret.ready():
		time.sleep(1)

	with allow_join_result():
		return ret.get(disable_sync_subtasks = True)
	
@shared_task(name = "split_pdfs_digest")
def split_pdfs(queryrows):

	from pypdf import PdfReader, PdfWriter
	from neo4j_tasks.main import app as neo4j_worker
	import io
	actions_module = importlib.import_module('tiramisu.worker') 
	workspace = actions_module.workspace

	try:
		filename = queryrows['path']

		with workspace.createContext() as context:
			if not Path(filename).is_file():
				print(f"{filename} was not a file.")
			else:
				with context.one_to_many(filename) as p:

					inputpdf = PdfReader(open(p.parent, "rb"), strict = False)

					for i in range(len(inputpdf.pages)):
						output = PdfWriter()
						output.add_page(inputpdf.pages[i])
						response_bytes_stream = io.BytesIO()
						output.write(response_bytes_stream)

						p = tiramisu_update(context, p, data = response_bytes_stream.getvalue() )

						new_pdf_path = (Path(p.child) / f"{Path(p.parent).stem}_page_{i}.pdf").as_posix()
						with open(new_pdf_path, "wb") as outputStream:
							output.write(outputStream)

						ret1 = neo4j_worker.tasks['add_node_neo4j'].s(nodeID = str(Path(p.child).name), label = "File", parentID = queryrows['nodeID'], relationship =  'SPLIT_INTO', attributes = {"name":Path(filename).stem + f"_page_{i}.pdf" , "tiramisuPath": new_pdf_path,  "fileExtension":'pdf',  'page': i}).apply_async()

						while not ret1.ready():
							time.sleep(1)

				with allow_join_result():
					_ = ret1.get(disable_sync_subtasks = True)
				return new_pdf_path
	

	except Exception as ex:
		split_pdfs.update_state(
		state=states.FAILURE,
		meta={
			'exc_type': type(ex).__name__,
			'exc_message': traceback.format_exc().split('\n')
		})
		# raise ex
		return traceback.format_exc()



@shared_task(name ="find_pdf_type_digest" )
def find_pdf_type(queryrows):


	import numpy as np 
	import fitz
	from neo4j_tasks.main import app as neo4j_worker

	name = Path(queryrows['path']).stem


	file = fitz.open(queryrows['path'])

	page0 = file[0]
	type_page = page_type(page0)

	if type_page == 'Scanned':
		ret = signature(neo4j_worker.tasks['update_metadata_neo4j'], kwargs = {"nodeID": queryrows['nodeID'], "attributes": {"scanned": True}}).delay()

		while not ret.ready():
			time.sleep(1)

		with allow_join_result():
			return ret.get(disable_sync_subtasks = True)
	elif type_page == 'Searchable text':
		ret = signature(neo4j_worker.tasks['update_metadata_neo4j'], kwargs = {"nodeID": queryrows['nodeID'], "attributes": {"scanned": True}}).delay()

		while not ret.ready():
			time.sleep(1)

		with allow_join_result():
			return ret.get(disable_sync_subtasks = True)
	else:
		ret = signature(neo4j_worker.tasks['update_metadata_neo4j'], kwargs = {"nodeID": queryrows['nodeID'], "attributes": {"scanned": False}}).delay()

		while not ret.ready():
			time.sleep(1)

		with allow_join_result():
			return ret.get(disable_sync_subtasks = True)


@shared_task(name ="find_pdf_type_supervisor_digest")
def find_pdf_type_supervisor():

	query = """
	MATCH (n:File) - [:SPLIT_INTO] -> (m: File)
	WHERE m.fileExtension = "pdf"
	return m.nodeID as nodeID, m.tiramisuPath as path
	"""
	from neo4j_tasks.main import app as neo4j_worker

	ret = (neo4j_worker.tasks['query_neo4j'].s(query,) | (find_pdf_type_chunk.s())).apply_async()

	while not ret.ready():
		time.sleep(1)


	with allow_join_result():
		return ret.get(disable_sync_subtasks = True)

@shared_task(name="find_pdf_type_chunk_digest")
def find_pdf_type_chunk(queryrows):

	ret = find_pdf_type.chunks(zip(queryrows), 1).apply_async(queue = "digest_worker")

	while not ret.ready():
		time.sleep(1)

	with allow_join_result():
		return ret.get(disable_sync_subtasks = True)



@shared_task(name = "doc_to_pdf_supervisor_digest")
def doc_to_pdf_supervisor():
	query = """
	MATCH (n:Folder) - [:CONTAINS] -> (m: File)
	WHERE m.fileExtension = "doc"
	return m.nodeID as nodeID, m.tiramisuPath as path
	"""
	from neo4j_tasks.main import app as neo4j_worker

	ret = (neo4j_worker.tasks["query_neo4j"].s(query) | ( doc_to_pdf_chunk.s())).apply_async()

	while not ret.ready():
		time.sleep(1)

	with allow_join_result():
		return ret.get(disable_sync_subtasks = True)

@shared_task(name = "doc_to_pdf_chunk_digest")
def doc_to_pdf_chunk(queryrows):
	from neo4j_tasks.main import app as neo4j_worker

	actions_module = importlib.import_module('tiramisu.worker') 
	workspace = actions_module.workspace

	if len(queryrows) == 0:
		return 
	for row in queryrows:

		try:
			filename = row['path']
			with workspace.createContext() as context:
				if not Path(filename).is_file():
					print(f"{filename} was not a file.")
				else:
					with context.one_to_one(filename) as p:

						p.child =  p.parent.stem + '.doc'

						p = tiramisu_update(context, p)

						subprocess.call(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', str(p.child), filename ])

						ret1 = neo4j_worker.tasks['add_node_neo4j'].s(nodeID = str(p.child.name), label = "File", parentID = row['nodeID'], relationship =  'CONVERT_TO', attributes = {"name":Path(filename).stem + ".pdf", "tiramisuPath": (p.child / (Path(filename).stem + ".pdf" )).as_posix(), "fileExtension":'pdf'}).apply_async()


					while not ret1.ready():
						time.sleep(1)



		except Exception as ex:
			print(traceback.format_exc())
			# raise Ignore()
			doc_to_pdf.update_state(
			state=states.FAILURE,
			meta={
				'exc_type': type(ex).__name__,
				'exc_message': traceback.format_exc().split('\n')
			})
			# raise ex
			return traceback.format_exc()
	with allow_join_result():
		return ret1.get(disable_sync_subtasks = True)

@shared_task(name = "doc_to_pdf_digest")
def doc_to_pdf(queryrows):
	from neo4j_tasks.main import app as neo4j_worker

	actions_module = importlib.import_module('tiramisu.worker') 
	workspace = actions_module.workspace
	try:
		filename = queryrows['path']
		with workspace.createContext() as context:
			if not Path(filename).is_file():
				print(f"{filename} was not a file.")
			else:
				with context.one_to_one(filename) as p:

					p.child =  p.parent.stem + '.doc'

					p = tiramisu_update(context, p)

					subprocess.call(['libreoffice', '--headless',  '--convert-to', 'pdf', '--outdir', str(p.child), filename ])

					while not p.child.exists():
						time.sleep(1)
					ret1 = neo4j_worker.tasks['add_node_neo4j'].s(nodeID = str(p.child.name), label = "File", parentID = queryrows['nodeID'], relationship =  'CONVERT_TO', attributes = {"name":Path(filename).stem + ".pdf", "tiramisuPath": (p.child / (Path(filename).stem + ".pdf" )).as_posix(), "fileExtension":'pdf'}).apply_async()
					

				while not ret1.ready():
					time.sleep(1)

		with allow_join_result():
			return ret1.get(disable_sync_subtasks = True)

	except Exception as ex:
		print(traceback.format_exc())
		# raise Ignore()
		doc_to_pdf.update_state(
		state=states.FAILURE,
		meta={
			'exc_type': type(ex).__name__,
			'exc_message': traceback.format_exc().split('\n')
		})
		# raise ex
		return traceback.format_exc()


@shared_task(name = "docx_to_pdf_supervisor_digest")
def docx_to_pdf_supervisor():
	query = """
	MATCH (n:Folder) - [:CONTAINS] -> (m: File)
	WHERE m.fileExtension = "docx"
	return m.nodeID as nodeID, m.tiramisuPath as path
	"""
	from neo4j_tasks.main import app as neo4j_worker

	ret = (neo4j_worker.tasks["query_neo4j"].s(query) | ( docx_to_pdf_chunk.s())).apply_async()

	while not ret.ready():
		time.sleep(1)


	with allow_join_result():
		return ret.get(disable_sync_subtasks = True)

@shared_task(name = "docx_to_pdf_chunk_digest")
def docx_to_pdf_chunk(queryrows):
	from neo4j_tasks.main import app as neo4j_worker
	actions_module = importlib.import_module('tiramisu.worker') 
	workspace = actions_module.workspace

	if len(queryrows) == 0:
		return 
	for row in queryrows:

		
		try:
			filename = row['path']
			with workspace.createContext() as context:
				if not Path(filename).is_file():
					print(f"{filename} was not a file.")
				else:
					with context.one_to_one(filename) as p:

						p.child =  p.parent.stem + '.docx'

						p = tiramisu_update(context, p)

						subprocess.call(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', str(p.child), filename ])

						ret1 = neo4j_worker.tasks['add_node_neo4j'].s(nodeID = str(p.child.name), label = "File", parentID = row['nodeID'], relationship =  'CONVERT_TO', attributes = {"name":Path(filename).stem + ".pdf", "tiramisuPath": (p.child / (Path(filename).stem + ".pdf" )).as_posix(), "fileExtension":'pdf'}).apply_async()


		except Exception as ex:
			print(traceback.format_exc())
			# raise Ignore()
			docx_to_pdf.update_state(
			state=states.FAILURE,
			meta={
				'exc_type': type(ex).__name__,
				'exc_message': traceback.format_exc().split('\n')
			})
			# raise ex
			return traceback.format_exc()
	with allow_join_result():
		return ret1.get(disable_sync_subtasks = True)


@shared_task(name = "docx_to_pdf_digest")
def docx_to_pdf(queryrows):
	from neo4j_tasks.main import app as neo4j_worker
	actions_module = importlib.import_module('tiramisu.worker') 
	workspace = actions_module.workspace
	try:
		filename = queryrows['path']
		with workspace.createContext() as context:
			if not Path(filename).is_file():
				print(f"{filename} was not a file.")
			else:
				with context.one_to_one(filename) as p:

					p.child =  p.parent.stem + '.docx'

					p = tiramisu_update(context, p)
					subprocess.call(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', str(p.child), filename ])

					ret1 = neo4j_worker.tasks['add_node_neo4j'].s(nodeID = str(p.child.name), label = "File", parentID = queryrows['nodeID'], relationship =  'CONVERT_TO', attributes = {"name":Path(filename).stem + ".pdf", "tiramisuPath": (p.child / (Path(filename).stem + ".pdf" )).as_posix(), "fileExtension":'pdf'}).apply_async()

					while not ret1.ready():
						time.sleep(1)

		with allow_join_result():
			return ret1.get(disable_sync_subtasks = True)

	except Exception as ex:
		print(traceback.format_exc())
		# raise Ignore()
		docx_to_pdf.update_state(
		state=states.FAILURE,
		meta={
			'exc_type': type(ex).__name__,
			'exc_message': traceback.format_exc().split('\n')
		})
		# raise ex
		return traceback.format_exc()

