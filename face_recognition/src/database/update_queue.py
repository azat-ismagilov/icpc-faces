import json
import numpy as np

from src.recognition import get_k_similar_faces, get_group
from src.database import DataBase

class UpdateQueue:
    def __init__(self, database: DataBase, new_data_path: str, num_faces_show: int = 5, log_path: str = 'update_log.jsonl'):
        """
        Initialize the UpdateQueue with a database and a new data file.
        :param database: An instance of DataBase to interact with the database.
        :param new_data_path: Path to the new data file to be processed.
        :param num_faces_show: Number of similar faces to show.
        :param log_path: Path to the log file where updates will be recorded.
        """
        self.database = database
        self.num_faces_show = num_faces_show
        self.new_data_path = new_data_path
        self.log_path = log_path
        self.queue = []
        self.queue_embeddings = None

        self.__load_new_data()

    
    def __load_new_data(self):
        """
        Load new data from the specified file and populate the queue.
        :return: None
        """
        with open(self.new_data_path, 'r') as file:
            new_data = json.load(file)
        
        for item in new_data:
            self.queue.append(item)
        
        self.queue_embeddings = np.array([item['embeddings'][0] for item in new_data])

    def get(self):
        """
        Get the next item from the queue.
        :return: A tuple containing the new state, a list of similar faces, indices and similarity score.
        """

        if not self.queue:
            return [], [], [], []

        new_embedding = self.queue_embeddings[0,:]
        embeddings_matrix = self.database.get_embeddings()

        similar_faces, similarities = get_k_similar_faces(
            request_embedding=new_embedding,
            faces_embeddings=embeddings_matrix,
            k=self.num_faces_show
        )

        group_idx = get_group(new_embedding, self.queue_embeddings)
        batch_states = [self.queue[i] for i in group_idx]

        self.queue = [self.queue[i] for i in range(len(self.queue)) if i not in group_idx]
        self.queue_embeddings = np.delete(self.queue_embeddings, group_idx, axis=0)

        return batch_states, [self.database.get(idx) for idx in similar_faces], similar_faces.tolist(), similarities
    
    def update(self, data: dict, name: str = None, idx: int = None):
        """
        Update the database with the new data.
        :param data: The data to be updated in the database.
        :param name: Optional name for the data.
        :param idx: Optional index for the data.
        :return: None
        """
        assert name is not None or idx is not None, "Name or index should be provided for update."

        if idx is not None:
            data['name'] = self.database.get(idx)['name'] if name is None else name
            self.database.update(data, idx=idx)
        elif name is not None:
            data['name'] = name
            self.database.update(data)

        self.log(data)

    def undo(self, data: dict):
        """
        Undo the last operation by putting the data back into the queue.
        :param data: The data to be put back into the queue.
        :return: None
        """
        self.queue.append(data)
        self.queue_embeddings = np.vstack((self.queue_embeddings, np.array(data['embeddings'][0])))

    def log(self, data: dict):
        """
        Log the data to a file.
        :param data: The data to be logged.
        :return: None
        """
        with open(self.log_path, 'a') as log_file:
            log_file.write(json.dumps(data) + '\n')

    @staticmethod
    def combine_group(group: list, name: str = None):
        """
        Combine a group of faces into a single entry in the database.
        :param group: List of indices of faces to be combined.
        :param name: Optional name for the combined entry.
        :return: None
        """

        result = group[0]

        for object in group[1:]:
            result['embeddings'].extend(object['embeddings'])
            result['bounding_boxes'].extend(object['bounding_boxes'])

        if name is not None:
            result['name'] = name

        return result
    
    def compute_similar(self, data: dict):
        """
        Compute similar faces for the given data.
        :param data: The data for which similar faces are to be computed.
        :return: A tuple containing the new state, a list of similar faces and indices.
        """
        embeddings_matrix = self.database.get_embeddings()

        similar_faces, similarities = get_k_similar_faces(
            request_embedding=np.array(data['embeddings'][0]),
            faces_embeddings=embeddings_matrix,
            k=self.num_faces_show
        )

        return [self.database.get(idx) for idx in similar_faces], similar_faces.tolist(), similarities
