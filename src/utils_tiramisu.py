
import json
from urllib import request, parse
import requests
import time
import pandas as pd



def check_status(url):
	r = requests.get(url)
	status = r.json()['task_status']

	return status == 'SUCCESS'
	

def submit_to_tiramisu(task, kwargs):
	digest_list = [
	{

		"action": task,
		 'kwargs': kwargs
	}]
	data = json.dumps({ 
			"action_list": digest_list 
		}).encode()
	req = request.Request("http://localhost:8080/api/action/concurrent", data)
	req.add_header("Content-Type", "application/json")
	res = request.urlopen(req)
	out_data = res.read()
	result = json.loads(out_data)


def return_from_neo4j(query):
	digest_list = [
	{

		"action": "query_neo4j",
		 'kwargs': {'query': query}
	}]
	
	data = json.dumps({ 
			"action_list": digest_list 
		}).encode()
	
	req = request.Request("http://localhost:8080/api/action/concurrent", data)
	req.add_header("Content-Type", "application/json")
	res = request.urlopen(req)
	out_data = res.read()
	result = json.loads(out_data)
	
	time.sleep(1)
	
	response = request.urlopen("http://localhost:8080/api/status/" + result['task_id'][0])

	finished = False
	while not finished:
		time.sleep(1)

		finished = check_status("http://localhost:8080/api/status/" + result['task_id'][0])
	response = request.urlopen("http://localhost:8080/api/status/" + result['task_id'][0])
	data = json.loads(response.read())
	
	return pd.DataFrame(data['task_result'])