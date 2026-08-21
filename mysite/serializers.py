import pickle


class PickleSerializer:
    """Re-implements Django's removed PickleSerializer for session data that contains model objects."""

    def __init__(self, protocol=None):
        self.protocol = pickle.HIGHEST_PROTOCOL if protocol is None else protocol

    def dumps(self, obj):
        return pickle.dumps(obj, self.protocol)

    def loads(self, data):
        return pickle.loads(data)
