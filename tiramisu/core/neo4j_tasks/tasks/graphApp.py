import logging
import sys

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

# this class interfaces flask server with the neo4j database
# class functions can be added to include more scenario-specific cypher queries
# each cypher query requires a static class method and a parent function under self.driver.session() context 
class graphApp:

	def __init__(self, uri, user, password):
		self.driver = GraphDatabase.driver(uri, auth=(user, password))

		self.database_name = 'neo4j'

	def close(self):
		# Don't forget to close the driver connection when you are finished with it
		self.driver.close()

	@staticmethod
	def enable_log(level, output_stream):
		handler = logging.StreamHandler(output_stream)
		handler.setLevel(level)
		logging.getLogger("neo4j").addHandler(handler)
		logging.getLogger("neo4j").setLevel(level)

	# adds a generic node relationship to the neo4j database
	# this class method is a subset of query_write, but with more structured attributes and fields
	def generic_action(self, nodeID, label, parentID, relationship, attributes, database = None):


		if database is None:

			with self.driver.session() as session:
				result = session.write_transaction(
					self._generic_action,  nodeID, label, parentID, relationship, attributes)

				return result
		else:
			with self.driver.session(database = database) as session:
				result = session.write_transaction(
					self._generic_action,  nodeID, label, parentID, relationship, attributes)

				return result

	def update_metadata(self, nodeID, attributes, database = None):


		if database is None:
			with self.driver.session() as session:
				result = session.write_transaction(
					self._update_metadata,  nodeID, attributes)

				return result
		else:
			with self.driver.session(database= database) as session:
				result = session.write_transaction(
					self._update_metadata,  nodeID, attributes)

				return result
	# writes any cypher transaction for the neo4j database
	def query_write(self, query, database = None):
		if database is None:

			with self.driver.session() as session:
				result = session.run(query)
				record = result.single()
				print(record)
				return record
		else:
			with self.driver.session(database = database) as session:
				result = session.run(query)
				record = result.single()
				return record
	# asks the neo4j database to return any query
	def query(self, query, database = None):
		if database is None:
			with self.driver.session() as session:
				result = session.read_transaction(self._query, query)
		else:
			with self.driver.session(database = database) as session:
				result = session.read_transaction(self._query, query)
		return result
	
	
	def load_csv(self, query, database_name):
		with self.driver.session(database = database_name) as session:
			result = session.read_transaction(self._load_csv, query)
		
		return result

		
	@staticmethod
	def _generic_action(tx, nodeID, label, parentID, relationship, attributes):
		relationship = relationship.upper()
		query = (
			"MERGE (p1 {nodeID: $nodeID}) "
			)

		if not attributes is None:
			query += (
				f"SET p1:{label} "
				"SET p1 += $attributes "
				)

		query += (
			"WITH p1 "
			"MATCH (p2) " 
			"WHERE p2.nodeID = $parentID "
			"CALL apoc.create.relationship(p2, $relationship, NULL, p1) YIELD rel "
			"RETURN p2, p1"
			)
		print(query)
		result = tx.run(query, nodeID = nodeID, parentID = parentID, relationship = relationship, attributes = attributes)
		try:
			return [row for row in result]
		# Capture any errors along with the query and data for traceability
		except ServiceUnavailable as exception:
			logging.error("{query} raised an error: \n {exception}".format(
				query=query, exception=exception))
			raise

	@staticmethod
	def _update_metadata(tx, nodeID, attributes):
		query = (
			"MATCH (p1 {nodeID: $nodeID}) "
			)

		query += (
			"SET p1 += $attributes "
			)

		query += (
			"RETURN p1"
			)
		result = tx.run(query, nodeID = nodeID, attributes = attributes)
		try:
			return [row for row in result]
		# Capture any errors along with the query and data for traceability
		except ServiceUnavailable as exception:
			logging.error("{query} raised an error: \n {exception}".format(
				query=query, exception=exception))
			raise

	@staticmethod
	def _query_write(tx, query):
		try:
			result = tx.run(query)
		except ServiceUnavailable as exception:
			logging.error("{query} raised an error: \n {exception}".format(
				query=query, exception=exception))
			raise

	@staticmethod
	def _query(tx, query):
		try:
			results = []
			result = tx.run(query)
			for i in result:
				results.append(i.data())

			return results
		except ServiceUnavailable as exception:
			logging.error("{query} raised an error: \n {exception}".format(
				query=query, exception=exception))
			raise

	@staticmethod
	def _load_csv(tx, query):
		try:
			results = []
			result = tx.run(query)
			for i in result:
				results.append(i.data())

			return results
		except ServiceUnavailable as exception:
			logging.error("{query} raised an error: \n {exception}".format(
				query=query, exception=exception))
			raise