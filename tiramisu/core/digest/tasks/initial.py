from celery import signature, shared_task

import importlib

from urllib import request, parse
import json 



# the first celery task for any archive
# detects duplicates, corrects file extensions, and saves every file for future subsequent steps

@shared_task(name = 'start_digest')
def digest(blacklist = ['.tiramisu'], hidden = True):

    import tiramisu_digest

    actions_module = importlib.import_module('tiramisu.worker') 
    workspace = actions_module.workspace

    with workspace.createContext() as context:

        (context.config.root / '.tiramisu' / 'neo4j' ).mkdir(exist_ok = True)
        (context.config.root / '.tiramisu' / 'neo4j' / 'import').mkdir(exist_ok = True)
        tiramisu_digest.digest(context.config.root.as_posix(), blacklist, hidden)
        merge_query = (
        "MATCH (n:File) - [:COMBINED_TO] -> (m: File) " 
        "WITH m.fileHash as hash, COLLECT(m) AS ns "
        "WHERE size(ns) > 1 "
        "CALL apoc.refactor.mergeNodes(ns,{properties:{ name:'overwrite',tiramisuPath:'overwrite', originalPath: 'combine', fileExtension:'overwrite', nodeID: 'overwrite', fileHash: 'overwrite', `.*`: 'overwite'},mergeRels:true}) "
        "YIELD node " 
        "return node ")
        
        digest_list = [
        {
            "action": "write_neo4j",
            'kwargs': {'query': "CALL apoc.periodic.iterate( \"LOAD CSV WITH HEADERS FROM 'file:///files.csv' as row with row where linenumber() > 0 return row\", \"with row.NodeType as nodetype, row.Name as name, row.NodeID as nodeID, row.TiramisuPath as tiramisuPath, row.OriginalPath as originalPath, row.FileExtension as fileExtension, row.FileHash as fileHash MERGE (p1: File {name: name, nodeID: nodeID, tiramisuPath: tiramisuPath, originalPath: originalPath, fileExtension: fileExtension, fileHash: fileHash})\",{batchSize:10000, parallel:true})"}
        },

        {
            "action": "write_neo4j",
            'kwargs': {'query': "CALL apoc.periodic.iterate( \"LOAD CSV WITH HEADERS FROM 'file:///folders.csv' as row with row where linenumber() > 0 return row\", \"with row.NodeType as nodetype, row.Name as name, row.NodeID as nodeID, row.TiramisuPath as tiramisuPath, row.OriginalPath as originalPath, row.FileExtension as fileExtension, row.FileHash as fileHash MERGE (p1:Folder {name: name, nodeID: nodeID, tiramisuPath: tiramisuPath, originalPath: originalPath, fileExtension: fileExtension, fileHash: fileHash})\",{batchSize:10000, parallel:true});"}
        },

        {
            "action": "write_neo4j",
            'kwargs': {'query': "CALL apoc.periodic.iterate( \"LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' as row with row where linenumber() > 0 return row\", \"with row.Relationship as relationship, row.Child as child, row.Parent as parent MATCH (p2) WHERE p2.nodeID = parent MATCH (p1) WHERE p1.nodeID = child CALL apoc.create.relationship(p2, relationship, {}, p1) YIELD rel return rel\",{batchSize:10000, parallel:true});"}

        }]

        
        data = json.dumps({ 
                    "action_list": digest_list
                }).encode()
        req = request.Request("http://flask:5000/api/action/chain", data)
        req.add_header("Content-Type", "application/json")
        res = request.urlopen(req)
        result = json.loads(res.read())

    return {
    "status": "completed",
    "result": result['task_id']
    }