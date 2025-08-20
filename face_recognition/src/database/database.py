import json
import numpy as np


class DataBase:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.__load_database()

        self.embedding_matrix = self.__get_embedding_matrix()

    def __get_embedding_matrix(self) -> np.ndarray:
        embedding_matrix = np.array([item["embeddings"][0] for item in self.data])
        return embedding_matrix if embedding_matrix.size > 0 else np.empty((0, 128))

    def __load_database(self):
        try:
            with open(self.database_path, 'r') as file:
                self.data = json.load(file)
        except FileNotFoundError:
            self.data = {}
        except json.JSONDecodeError:
            self.data = {}

    def update(self, new_data: dict, idx: int = -1):
        """
        Update the database with new data.
        :param new_data: A dictionary containing new data to be added or updated in the database.
        :param idx: The index at which to update the data. If -1, it appends the new data.
        :return: None
        """
        if idx == -1:
            self.data.append(new_data)
            self.embedding_matrix = np.concatenate(
                (self.embedding_matrix, np.array(new_data["embeddings"][0]).reshape(1, -1)),
                axis=0
            )
        else:
            self.data[idx]["embeddings"].extend(new_data.get("embeddings", []))
            self.data[idx]["bounding_boxes"].extend(new_data.get("bounding_boxes", []))
        self.save()

    def get(self, idx: int) -> dict:
        """
        Get the data from the database.
        :param idx: The index of the data to retrieve.
        :return: The data at the specified index.
        """
        return self.data[idx]
    
    def get_embeddings(self) -> np.ndarray:
        """
        Get the embeddings from the database.
        :return: A numpy array of embeddings.
        """
        return self.embedding_matrix

    def save(self):
        with open(self.database_path, 'w') as file:
            json.dump(self.data, file, indent=4)

    def __len__(self):
        """
        Get the number of items in the database.
        :return: The number of items in the database.
        """
        return len(self.data)
