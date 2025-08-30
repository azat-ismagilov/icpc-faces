import json
import numpy as np


class DataBase:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.__load_database()

        self.embedding_matrix = self.__get_embedding_matrix()

    def __get_embedding_matrix(self) -> np.ndarray:
        embeddings = []
        for item in self.data:
            if item.get("embeddings") and item.get("bounding_boxes"):
                # Find the embedding with the largest bounding box area
                best_embedding = None
                max_area = 0
                
                for i, bbox_info in enumerate(item["bounding_boxes"]):
                    if i < len(item["embeddings"]):
                        # Handle both dict and string bbox formats
                        if isinstance(bbox_info, dict):
                            bbox = bbox_info.get("bbox", {})
                        else:
                            # If bbox_info is a string, skip it or handle appropriately
                            continue
                            
                        if isinstance(bbox, dict):
                            width = bbox.get("width", 0) / 100.0  # Convert from percentage
                            height = bbox.get("height", 0) / 100.0  # Convert from percentage
                            area = width * height
                            
                            if area > max_area:
                                max_area = area
                                best_embedding = item["embeddings"][i]
                
                # Fallback to first embedding if no valid bbox found
                if best_embedding is None and item["embeddings"]:
                    best_embedding = item["embeddings"][0]
                
                if best_embedding is not None:
                    embeddings.append(best_embedding)
        
        return np.array(embeddings) if embeddings else np.empty((0, 128))

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
            # Find the best embedding (largest face area) for new data
            best_embedding = None
            max_area = 0
            
            for i, bbox_info in enumerate(new_data.get("bounding_boxes", [])):
                if i < len(new_data.get("embeddings", [])):
                    # Handle both dict and string bbox formats
                    if isinstance(bbox_info, dict):
                        bbox = bbox_info.get("bbox", {})
                    else:
                        continue
                        
                    if isinstance(bbox, dict):
                        width = bbox.get("width", 0) / 100.0
                        height = bbox.get("height", 0) / 100.0
                        area = width * height
                        
                        if area > max_area:
                            max_area = area
                            best_embedding = new_data["embeddings"][i]
            
            # Fallback to first embedding if no valid bbox found
            if best_embedding is None and new_data.get("embeddings"):
                best_embedding = new_data["embeddings"][0]
            
            if best_embedding is not None:
                self.embedding_matrix = np.concatenate(
                    (self.embedding_matrix, np.array(best_embedding).reshape(1, -1)),
                    axis=0
                )
        else:
            self.data[idx]["embeddings"].extend(new_data.get("embeddings", []))
            self.data[idx]["bounding_boxes"].extend(new_data.get("bounding_boxes", []))
            # Rebuild embedding matrix to use the largest face for this person
            self.embedding_matrix = self.__get_embedding_matrix()
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
