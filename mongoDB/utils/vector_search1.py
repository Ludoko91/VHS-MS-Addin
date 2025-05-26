import threading
import numpy as np
import faiss

# Initialisierung des Locks
index_lock = threading.Lock()

# Globale Variablen für Index und Kursnummer-IDs
index_tags_0 = None
kursnr_ids = None

def load_indices():
    global index_tags_0, kursnr_ids

    # Lade den FAISS-Index und die Kursnummern-IDs aus den Dateien
    index_tags_0 = faiss.read_index('data/vector_tags_0.index')
    kursnr_ids = np.load('data/kursnr_ids.npy')

def save_indices():
    global index_tags_0, kursnr_ids

    # Speichere den FAISS-Index und die Kursnummern-IDs in den Dateien
    faiss.write_index(index_tags_0, 'data/vector_tags_0.index')
    np.save('data/kursnr_ids.npy', kursnr_ids)

def add_vectors_to_faiss_indices(vector_list, kursnr):
    global index_tags_0, kursnr_ids

    # Überprüfen, ob die Vektoren die richtige Form haben
    for vector in vector_list:
        if len(vector) != 768:
            return False
    
    with index_lock:
        # Lade die aktuellen Indizes und IDs
        load_indices()

        # Konvertiere die Liste der Vektoren zu einem numpy-Array
        

        # Füge jeden Vektor einzeln in den FAISS-Index ein
        for vector in vector_list:
            vector_list = np.array(vector).astype('float32')
            vector = vector_list.reshape(1, -1)  # Stelle sicher, dass der Vektor 2D ist (1, Dimension)
            index_tags_0.add(vector)
            kursnr_ids = np.append(kursnr_ids, kursnr)

        # Speichere die aktualisierten Indizes und IDs
        save_indices()

    return True


def find_best_matches(query_vector, k=25):
    global index_tags_0, kursnr_ids
    
    # Konvertiere den Query-Vektor zu einem numpy-Array und überprüfe die Dimensionen
    query_vector = np.array(query_vector).astype('float32').reshape(1, -1)

    with index_lock:
        # Lade die Indizes und IDs
        load_indices()

        # Suche nach den k nächsten Nachbarn im Index
        distances, indices = index_tags_0.search(query_vector, k)

    # IDs der gefundenen Nachbarn sammeln, falls gültige Indizes zurückgegeben wurden
    found_ids = [kursnr_ids[i] for i in indices[0] if i != -1]

    # Zähle die Häufigkeit jeder ID (falls einige IDs mehrfach gefunden werden)
    id_counts = {}
    for found_id in found_ids:
        if found_id in id_counts:
            id_counts[found_id] += 1
        else:
            id_counts[found_id] = 1

    # Sortiere die IDs nach Häufigkeit und wähle die top k
    sorted_ids = sorted(id_counts.items(), key=lambda item: item[1], reverse=True)[:k]

    seen = set()
    best_matches = []
    for item in sorted_ids:
        if item[0] not in seen:
            best_matches.append(item[0])
            seen.add(item[0])

    
    return best_matches
