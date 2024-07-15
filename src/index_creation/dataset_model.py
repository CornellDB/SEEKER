import uuid

class DatasetModel:
    def __init__(self, dataset_name, dataset, metadata=None):
        #Necessary?
        self.id = uuid.uuid4()
        self.dataset_name = dataset_name
        self.dataset = dataset
        self.metadata = metadata if metadata else {}

    def set_dataset(self, dataset):
        self.dataset = dataset

    def set_metadata(self, metadata):
        self.metadata = metadata
