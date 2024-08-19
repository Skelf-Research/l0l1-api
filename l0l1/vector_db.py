import numpy as np
from usearch.index import Index

class VectorDB:
    def __init__(self, ndim, metric='cos', dtype='f32'):
        self.index = Index(ndim=ndim, metric=metric, dtype=dtype)

    def add(self, key, vector):
        self.index.add(key, vector)

    def search(self, vector, k=10):
        return self.index.search(vector, k)

    def save(self, filepath):
        self.index.save(filepath)

    def load(self, filepath):
        self.index.load(filepath)
