from cog.torque import Graph
import os

class KnowledgeGraph:
    def __init__(self, workspace_id):
        self.db_path = f"cogdb_{workspace_id}"
        if not os.path.exists(self.db_path):
            CogDB.create(self.db_path)
        self.client = CogDBClient(self.db_path)

    def add_relation(self, source, relation, target):
        self.client.insert(source, relation, target)

    def get_relations(self, source, relation):
        return list(self.client.search(source, relation))

    def get_all_relations(self):
        return list(self.client.search("*", "*", "*"))