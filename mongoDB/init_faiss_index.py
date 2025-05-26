import numpy as np
import faiss
from pymongo import MongoClient

# Funktion zum Überprüfen der Form des numpy-Arrays und Erstellen des FAISS-Indexes
def create_and_save_index(vectors, kursnr_ids):
    if vectors.shape[1] != 768:  # Überprüfe, ob die zweite Dimension 768 ist
        print("Error: Vectors should have 768 dimensions")
    else:
        index = faiss.IndexFlatL2(768)  # L2-Abstand für 768-dimensionale Vektoren
        index.add(vectors)
        faiss.write_index(index, 'data/vector_tags_0.index')
        np.save('data/kursnr_ids.npy', np.array(kursnr_ids))

# Verbindung zur MongoDB
mongo_uri = 'mongodb://mongo_container:27017'
client = MongoClient(mongo_uri)
db = client.vhs  # Verbindung zur Datenbank
collection = db.courses_new   # Ausgewählte Sammlung

# Initialisierung der Listen
kursnr = []
vector_tags_0 = []

# Vektoren und IDs aus der MongoDB abrufen
for document in collection.find():
    
    
    # Nur vector_tags_0 abrufen und in die Liste speichern
    vectorlist = document.get('metatags_vector')
    if vectorlist:
        for vector in vectorlist:
            if isinstance(vector, list) and len(vector) == 768:
                vector_tags_0.append(vector)  # Füge den Vektor der Liste hinzu
                kursnr.append(document['kursnr'])
            else:
                print(f"Skipping document with kursnr {document['kursnr']} due to invalid vector format")

# Konvertiere die Liste der Vektoren in ein numpy-Array
vector_tags_0 = np.array(vector_tags_0).astype('float32')

# Erstellen und Speichern des FAISS-Indexes und der Kursnummern
create_and_save_index(vector_tags_0, kursnr)

print("Index and Kursnr IDs saved successfully.")
