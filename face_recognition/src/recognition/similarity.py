import numpy as np


def get_k_similar_faces(request_embedding: np.ndarray, faces_embeddings: np.ndarray, k: int = 5) -> list:
    """
    Get the indices of the k most similar faces to the request embedding.
    :param request_embedding: The embedding of the request face.
    :param faces_embeddings: The embeddings of the faces in the database.
    :param k: The number of most similar faces to return.
    :return: A list of indices of the k most similar faces.
    """

    if len(faces_embeddings) == 0:
        return np.array([]), []
    k = min(k, len(faces_embeddings))

    similarities = 1 - np.dot(faces_embeddings, request_embedding).flatten() \
        / np.linalg.norm(faces_embeddings, axis=-1) / np.linalg.norm(request_embedding)
    
    # Get the indices of the k most similar faces
    k_indices = similarities.argsort()[:k]
    return k_indices, similarities[k_indices].tolist()

def get_group(request_embedding: np.ndarray, faces_embeddings: np.ndarray) -> list:
    """
    Get the group of the most similar faces to the request embedding.
    :param request_embedding: The embedding of the request face.
    :param faces_embeddings: The embeddings of the faces in the database.
    :return: A list of indices of the most similar faces.
    """

    distances = 1 - np.dot(faces_embeddings, request_embedding).flatten() \
        / np.linalg.norm(faces_embeddings, axis=-1) / np.linalg.norm(request_embedding)

    return np.arange(len(faces_embeddings))[distances < 0.4].tolist()
