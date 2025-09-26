from celery import signature, shared_task

from urllib import request, parse
import json 
from neo4j_tasks.tasks.graphApp import graphApp
import os 
import ast 


URL = "bolt://neo4j:7687"
# password can be changed in docker (see core/docker-compose.yaml line 20)
# for debugging purposes; for production, save password in a secure file and remove references in code
pw = os.environ['NEO4J_PASSWORD']

LABEL_STUDIO_URL = 'http://labelstudio:8085'

class ConfigurationNotFoundError(Exception):
    pass

# delete all projects in LabelStudio
@shared_task(name = "delete_all_labelstudio")
def delete_all_labelstudio(api):
	from label_studio_sdk import Client
	
	ls = Client(url=LABEL_STUDIO_URL, api_key=api)
	ls.check_connection()
	
	ls.delete_all_projects()
	
	return  {
		"status": "completed"
	}

# Upload PDF/images to LabelStudio to view
# Can change interface here using LabelStudio labeling config
# jsonl is a list of dictionaries containing necessary fields (pdf, image, image1, etc)
@shared_task(name="upload_to_labelstudio")
def upload_to_labelstudio(jsonl, title, api, configuration):
	from label_studio_sdk import Client 

	jsonl = ast.literal_eval(jsonl)

	if configuration == 'pdf':
			config = """
			<View>
			<Header value="PDF"/>
			<Rating name="rating" toName="pdf" maxRating="10" icon="star" size="medium" />
			<Choices name="choices" choice="single-radio" toName="pdf" showInline="true">
			<Choice value="Choice A"/>
			<Choice value="Choice B"/>
			</Choices>
			<HyperText name="pdf" value="$pdf" inline="true"/>
		</View>
			"""
	elif configuration == 'two_image':
		config = """
			<View style="display: flex;">
	    <View style="width: 49%; margin-right: 1.99%">
	      <Image name="img-left" value="$image1"/>
	      <Choices name="class-left" toName="img-left" choice="multiple">
	        <Choice value="People" />
	      </Choices>
	    </View>

	    <View style="width: 49%;">
	      <Image name="img-right" value="$image2"/>
	      <Choices name="class-right" toName="img-right" choice="multiple">
	        <Choice value="Food" />
	      </Choices>
	    </View>
	  </View>
		"""
	elif configuration == 'image':
		config = """
			<View>
			<Image name="image" value="$image"/>
			<Image name="image2" value"$image2"/>
			<Choices name="choice" toName="image">
				<Choice value="Choice A"/>
			</Choices>
			</View>
		"""
	elif configuration == 'image+text':
		config = """
		<View style="display: flex;">
		<View style="width: 150px; padding-left: 2em; margin-right: 2em; background: #f1f1f1; border-radius: 3px">
			<Labels name="ner" toName="text">
			<Label value="Date" />
			</Labels>
		</View>

		<View>
		<View>
		<Header value="Multi-modal Page Annotation" />
		<Style> .document-border { border: 4px dotted blue;}</Style>
		<Style> .page-border { border: 4px dotted gray; }</Style>
		

		<View style="display: flex;">
			<View style="width: 100%;">
			<View className="document-border">
			<Image name="img-left" value="$image1"/>
			</View>
			</View>

			<View style="width: 100%;">
			<View className="page-border">
			<Text name="text" value="$text1"/>
				</View>
			</View>
		</View>
		
		<View>
			<Header value="What is the class of this document?" />
			<Choices name="comparison" toName="img-left" showInline="true">
			<Choice value="Email"/>
			<Choice value="Letter"/>
			<Choice value="Report"/>
			<Choice value="Else"/>
			</Choices>
		</View>
		</View>
		</View>

		</View>
		"""

	elif configuration == 'page_segmentation':
		config = """
			<View>
			<Header value="Page stream segmentation task" />
			<Style> .document-border { border: 4px dotted blue;}</Style>
			<Style> .page-border { border: 4px dotted gray; }</Style>
			

			<View style="display: flex;">
				<View style="width: 100%;">
				<View className="document-border">
				<Image name="img-left" value="$image1"/>
				</View>
				</View>

				<View style="width: 100%;">
				<View className="page-border">
				<Image name="img-right" value="$image2"/>
					</View>
				</View>
			</View>
			
			<View>
				<Header value="Does the document end here?" />
				<Choices name="comparison" toName="img-left" showInline="true">
				<Choice value="Yes" />
				<Choice value="No" />
				</Choices>
			</View>
			</View>
		"""
	elif configuration == 'custom':
		config = configuration
	else:
		raise ConfigurationNotFoundError

	if configuration == 'pdf':
		for row in jsonl:
			pdf_name = parse.quote(row['pdf'])
			server_name = "http://localhost:8080/file/" + pdf_name[len("/tiramisu/.tiramisu/___tiramisu_versions/"):]
			row['pdf'] = f"<embed src='{server_name}' width='100%' height='600px'/>"
		
	if configuration == 'image':
		for row in jsonl:
			image_name = row['image'][len("/tiramisu/.tiramisu/___tiramisu_versions/"):]
			# server_name = "/label-studio/data/local-files/?d=" + image_name
			server_name = "http://localhost:8080/file/" + parse.quote(image_name)

			row['image'] = server_name

	if configuration == 'page_segmentation':
		for row in jsonl:
			image_name = row['image1'][len("/tiramisu/.tiramisu/___tiramisu_versions/"):]
			# server_name = "/label-studio/data/local-files/?d=" + image_name
			server_name = "http://localhost:8080/file/" + parse.quote(image_name)

			row['image1'] = server_name

			if row['image2'] is None:
				row['image2'] = ""
			else:
				image_name = row['image2'][len("/tiramisu/.tiramisu/___tiramisu_versions/"):]
				server_name = "http://localhost:8080/file/" + parse.quote(image_name)

				row['image2'] = server_name

	ls = Client(url=LABEL_STUDIO_URL, api_key=api)
	ls.check_connection()

	project = ls.start_project(
	title=title,
	label_config=config)

	project.import_tasks(
	jsonl
	)

	return {
	"status": "completed"
	}

# Write a Neo4J query to visualize in LabelStudio
# query must return tabular data containing the necessary fields (pdf, image, image1, etc) from Neo4J
@shared_task(name =  "show_me_in_labelstudio")
def show_me_in_labelstudio(query, nodeID, title, api, configuration = "image"):
	from label_studio_sdk import Client


	app = graphApp(URL, 'neo4j', pw)

	query = query.format(nodeID = nodeID)

	title = title.format(nodeID = nodeID)

	result = app.query(query)
	
	if result is None or len(result) == 0:
		return {"status": "completed"}
	else:

		if configuration == 'pdf':
			config = """
			<View>
			<Header value="PDF"/>
			<Rating name="rating" toName="pdf" maxRating="10" icon="star" size="medium" />
			<Choices name="choices" choice="single-radio" toName="pdf" showInline="true">
			<Choice value="Choice A"/>
			<Choice value="Choice B"/>
			</Choices>
			<HyperText name="pdf" value="$pdf" inline="true"/>
		</View>
			"""
		elif configuration == 'image':
			config = """
				<View>
				<Image name="image" value="$image"/>
				<Choices name="choice" toName="image">
					<Choice value="Choice A"/>
				</Choices>
				</View>
			"""
		elif configuration == 'image+text':
			config = """
			<View style="display: flex;">
			<View style="width: 150px; padding-left: 2em; margin-right: 2em; background: #f1f1f1; border-radius: 3px">
				<Labels name="ner" toName="text">
				<Label value="Date" />
				</Labels>
			</View>

			<View>
			<View>
			<Header value="Multi-modal Page Annotation" />
			<Style> .document-border { border: 4px dotted blue;}</Style>
			<Style> .page-border { border: 4px dotted gray; }</Style>
			

			<View style="display: flex;">
				<View style="width: 100%;">
				<View className="document-border">
				<Image name="img-left" value="$image1"/>
				</View>
				</View>

				<View style="width: 100%;">
				<View className="page-border">
				<Text name="text" value="$text1"/>
					</View>
				</View>
			</View>
			
			<View>
				<Header value="What is the class of this document?" />
				<Choices name="comparison" toName="img-left" showInline="true">
				<Choice value="Email"/>
				<Choice value="Letter"/>
				<Choice value="Report"/>
				<Choice value="Else"/>
				</Choices>
			</View>
			</View>
			</View>

			</View>
			"""

		elif configuration == 'page_segmentation':
			config = """
				<View>
				<Header value="Page stream segmentation task" />
				<Style> .document-border { border: 4px dotted blue;}</Style>
				<Style> .page-border { border: 4px dotted gray; }</Style>
				

				<View style="display: flex;">
					<View style="width: 100%;">
					<View className="document-border">
					<Image name="img-left" value="$image1"/>
					</View>
					</View>

					<View style="width: 100%;">
					<View className="page-border">
					<Image name="img-right" value="$image2"/>
						</View>
					</View>
				</View>
				
				<View>
					<Header value="Does the document end here?" />
					<Choices name="comparison" toName="img-left" showInline="true">
					<Choice value="Yes" />
					<Choice value="No" />
					</Choices>
				</View>
				</View>
			"""
		elif configuration == 'custom':
			config = configuration
		else:
			raise ConfigurationNotFoundError
		

		if configuration == 'pdf':
			for row in result:
				file_name = parse.quote(row['file'])
				server_name = "http://localhost:8080/file/" + file_name[len("/tiramisu/.tiramisu/___tiramisu_versions/"):]
				row['pdf'] = f"<embed src='{server_name}' width='100%' height='600px'/>"
		
		if configuration == 'image':
			for row in result:
				image_name = row['file'][len("/tiramisu/.tiramisu/___tiramisu_versions/"):]
				# server_name = "/label-studio/data/local-files/?d=" + image_name
				server_name = "http://localhost:8080/file/" + parse.quote(image_name)

				row['image'] = server_name
		
		# Connect to the Label Studio API and check the connection
		ls = Client(url=LABEL_STUDIO_URL, api_key=api)
		ls.check_connection()

		project = ls.start_project(
		title=title,
		label_config=config)


		project.import_tasks(
		result
		)

		return {
		"status": "completed"
		}
