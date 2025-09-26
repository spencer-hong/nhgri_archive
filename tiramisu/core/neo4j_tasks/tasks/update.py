from celery import signature, shared_task

from neo4j_tasks.tasks.graphApp import graphApp
from urllib import request, parse
import json 
import os

URL = "bolt://neo4j:7687"
# password can be changed in docker (see core/docker-compose.yaml line 20)
pw = os.environ['NEO4J_PASSWORD']




@shared_task(name =  "add_node_neo4j")
def add_node_neo4j(nodeID, label, parentID, relationship, attributes = None):

	app = graphApp(URL, 'neo4j', pw)

	result = app.generic_action(nodeID = nodeID, label = label, parentID = parentID, \
	relationship = relationship, attributes = attributes )


	return {
	"status": "completed"
	}


# prone to sql injection
# avoid using
# included just for debugging purposes
@shared_task(name = "write_neo4j")
def write_neo4j(query, database = None):
	app = graphApp(URL, "neo4j", pw)

	if database is None:
		result = app.query_write(query)
	else:
		result = app.query_write(query, database)

	return {
		"status": "completed"
	}

@shared_task(name = "update_metadata_neo4j")
def update_metadata_neo4j(nodeID, attributes, database = None):
	app = graphApp(URL, "neo4j", pw)

	if database is None:
		result = app.update_metadata(nodeID = nodeID, attributes = attributes)
	else:
		result = app.update_metadata(nodeID = nodeID, attributes = attributes, database = database)

	return {
		"status": "completed"
	}


# only gets read permission 
@shared_task(name = "query_neo4j")
def query_neo4j(query, database = 'neo4j'):
	app = graphApp(URL, "neo4j", pw)

	if database is None:  
		result = app.query(query)
	else:
		result = app.query(query, database)
	
	return result

@shared_task(name = "load_csv_neo4j")
def load_csv_neo4j(node_csv, relationship_csv, attribute_name):
	app = graphApp(URL, "neo4j", pw)

	query = (f"CALL apoc.periodic.iterate( \"LOAD CSV WITH HEADERS FROM 'file:///{node_csv}.csv'")
	
	query += (" as row with row where linenumber() > 0 return row\",\"with ")

	for i in attribute_name:
		renamed = i.capitalize()
		query += (f"row.{renamed} as {i}, ")
	
	query += ("MERGE (p1: File {")
	
	for i in attribute_name:
		query += (f"{i}: {i}, ")

	query += ("})\",{batchSize:10000, parallel:true})")

	relationship_query = (f"CALL apoc.periodic.iterate( \"LOAD CSV WITH HEADERS FROM 'file:///{relationship_csv}.csv'" )
	
	relationship_query += ("as row with row where linenumber() > 0 return row\", \"with row.Relationship as relationship, row.Child as child, row.Parent as parent MATCH (p2) WHERE p2.nodeID = parent MATCH (p1) WHERE p1.nodeID = child CALL apoc.create.relationship(p2, relationship, {}, p1) YIELD rel return rel\",{batchSize:10000, parallel:true});")

	data = json.dumps({ 
				"action_list": [
					{"action": "write",
				"kwargs": {"query": query}
				},
				{ 
					"action": "write",
					"kwargs": {"query": relationship_query}
				}] 
			}).encode()
	req = request.Request("http://flask:5000/api/action/chain", data)
	req.add_header("Content-Type", "application/json")
	res = request.urlopen(req)
	result = json.loads(res.read())

	return {
		"status": "completed",
		"result": result["task_id"]
	}
