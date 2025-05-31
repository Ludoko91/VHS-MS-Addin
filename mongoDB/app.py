from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import os
import numpy as np
import faiss
import threading
from datetime import datetime

from utils.embbeder import embedder
from utils.vector_search1 import add_vectors_to_faiss_indices,find_best_matches

app = Flask(__name__)

# Conncected to MongoDB 
mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo:27017/')
client = MongoClient(mongo_uri)
db = client.vhs
collection = db.Molfsee

emb = embedder()


# Serve the index.html file
@app.route('/api')
def index():
    return render_template('index.html')

# API-Endpunkt:get all courses
@app.route('/api/courses', methods=['GET'])
def get_courses():
    courses = list(collection.find({}, {"_id": 0}))  # hide the _id-Feld

    i = []
    for course in courses:
        x = course["description"]
        i.append(x)
    return jsonify(i)

# API-Endpunkt: Find specific Course with kursnr
@app.route('/api/courses/<kursnr>', methods=['GET'])
def get_course(kursnr):
    course = collection.find_one({"kursnr": kursnr.strip()}, {"_id": 0})
    if course:
        return jsonify(course["description"])
    else:
        return jsonify({"error": "Course not found"}), 404
    
# API-Endpunkt: get all courses from that date
@app.route('/api/courses/date/<date>', methods=['GET'])
def get_courses_by_vhs(date):
    date = datetime.strptime(date, "%d%m%Y").strftime("%d.%m.%Y")

    courses = list(collection.find({"date": str(date)}, {"_id": 0}))
    results = []
    for course in courses:
        x = [course["description"],course["date"]]
        results.append(x)
    if courses:
        return jsonify(results)
    else:
        return jsonify({"error": "No courses found for the specified VHS"}), 404

# API-Endpunkt: search for Course Number
@app.route('/api/courses/<kursnr>', methods=['PUT'])
def update_course(kursnr):
    update_data = request.json
    result = collection.update_one({"kursnr": kursnr.strip()}, {"$set": update_data})
    if result.matched_count > 0:
        return jsonify({"message": "Course updated successfully"}), 200
    else:
        return jsonify({"error": "Course not found"}), 404

# API-Endpunkt: keyword Vectorsearch via question vector
@app.route('/api/courses/search', methods=['POST'])
def search():
    input_question = request.json.get('question')
    input_vector = emb.text_embedding(input_question)
    best_matches = find_best_matches(input_vector)
    results = []

    for kursnr in best_matches:
        course = collection.find_one({"kursnr": kursnr.strip()}, {"_id": 0})
        if course:
            descritpion = course["description"]
            results.append(descritpion)
        else:
            return jsonify({"error": "Course not found"}), 404

    return jsonify(results[:2])

# API-Endpunkt: Add course to Database
@app.route('/api/courses', methods=['POST'])
def add_course():
    course_data = request.json
    if 'kursnr' not in course_data:
        return jsonify({"error": "Course number is required"}), 400

    # Check if course exists
    existing_course = collection.find_one({"kursnr": course_data["kursnr"].strip()})
    if existing_course:
        return jsonify({"error": "Course already exists"}), 409
    try:
    # Add Vectors to FAISS-Index
        vectors = course_data.get('metatags_vector')
    #if vectors is None or not all(isinstance(v, list) and len(v) == 768 for v in vectors):
        #return jsonify({"error": "A valid metatags_vector with vectors of 768 dimensions is required"}), 400
    
        # Versuche, die Vektoren dem FAISS-Index hinzuzufügen
        success = add_vectors_to_faiss_indices(vectors, course_data["kursnr"].strip())
        
        if not success:
            return jsonify({"error": "Failed to add vectors to FAISS index"}), 500
    except Exception as e:
        collection.insert_one(course_data)
        return jsonify({"Add course, but error with FAISS-Index": str(e)}), 500
    # Add course to Database
    collection.insert_one(course_data)
    
    return jsonify({"message": "Course added successfully"}), 201

# API-Endpunkt: Delete course
@app.route('/api/courses/<kursnr>', methods=['DELETE'])
def delete_course(kursnr):
    result = collection.delete_one({"kursnr": kursnr.strip()})
    if result.deleted_count > 0:
        return jsonify({"message": "Course deleted successfully"})
    else:
        return jsonify({"error": "Course not found"}), 404



# API-Endpunkt: Vectorsearch via new vector
@app.route('/api/courses/search1', methods=['POST'])
def search1():
    input_vector = request.json.get('vector')
    if input_vector is None or len(input_vector) != 768:
        return jsonify({"error": "A valid vector with 768 dimensions is required"}), 400

    best_matches = find_best_matches(input_vector)
    results = []

    for kursnr in best_matches:
        course = collection.find_one({"kursnr": kursnr.strip()}, {"_id": 0})
        if course:
            descritpion = course["description"]
            results.append(descritpion)
        else:
            return jsonify({"error": "Course not found"}), 404

    return jsonify(results[:4])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=2000)
