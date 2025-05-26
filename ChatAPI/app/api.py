from flask import Flask, request, jsonify,render_template
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import requests

import main as main 
from tools import date_search

app = Flask(__name__)

# Aktiviere CORS für alle Routen
CORS(app, resources={r"/*": {"origins": "*"}}, expose_headers=["Content-Type"], supports_credentials=True)


m = main
d = date_search

# MongoDB-Verbindung
client = MongoClient("mongodb://mongo:27017")  # Passe den URI an deine Umgebung an
db = client["vhs"]  # Name der Datenbank
user_collection = db["users"]  # Name der Collection


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/square', methods=['POST'])
def calculate_square():
    try:
        data = request.get_json()
        number = data.get('number')
        if not isinstance(number, (int, float)):
            return jsonify({'error': 'Invalid input, expected a number'}), 400

        result = number ** 2
        return jsonify({'number': number, 'square': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/chat', methods=['POST'])
def chat():
    if request.method == 'OPTIONS':
        # CORS-Header für Preflight-Anfragen
        response = jsonify({'message': 'Preflight OK'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200
    try:
        data = request.get_json()
        query = data['chat_message']
        chat_history_messages = data['chat_history']
        user_database = data["user_database"]

        if not isinstance(query, (str)):
            return jsonify({'error': 'Invalid chat_message, expected a string'}), 400
        if not isinstance(chat_history_messages, (list)):
            return jsonify({'error': 'Invalid chat_history, expected a list'}), 400

        if len(chat_history_messages) == 0:
            chat_history = m.message_conveter(chat_history_messages)
            print(f"chat history: {chat_history}")
            answer = m.chatting_func(query,user_database,chat_history)
            return jsonify({'message' : query, 'answer': str(answer)}), 200
        else:
            answer = m.chatting_func(query,user_database)
            return jsonify({'message' : str(chat_history_messages), 'answer': str(answer)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/process-email', methods=['POST'])
def process_email():
    if request.method == 'OPTIONS':
        # Preflight-Anfrage
        return '', 200
    try:
        data = request.get_json()
        email_text_raw = data["emailText"]
        user_database = data["user_database"]

        email_text = f"Schreibe eine Antworte als KI-Assistent der VHS im Format einer E-Mail ohne Betreff auf folgenden Text mithilfe von relvanten Informationen, die du von deinen Tools bekommst. Formatiere deine Antwort als E-Mail mit <br> für Zeilenumbrüche. Text:{email_text_raw}"

        if not isinstance(email_text, (str)):
            return jsonify({'error': 'Invalid chat_message, expected a string'}), 401

        response_text = m.email_func(email_text,user_database)
        return jsonify({"responseText": str(response_text)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/process-email-test', methods=['POST'])
def process_email_test():
    if request.method == 'OPTIONS':
        # Preflight-Anfrage
        return '', 200
    try:
        data = request.get_json()
        email_text = data["emailText"]
        user_database = data["user_database"]

        if not isinstance(email_text, (str)):
            return jsonify({'error': 'Invalid chat_message, expected a string'}), 401

        response_text = m.email_func(email_text,user_database)
        return jsonify({"responseText": str(response_text)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route("/api/user-database", methods=["GET"])
def get_user_database():
    """
    Abrufen der Datenbankzuordnung eines Benutzers basierend auf der E-Mail-Adresse.
    Query-Parameter: email
    """
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Email-Parameter fehlt"}), 400

    user = user_collection.find_one({"email": email})
    if user:
        return jsonify({"email": user["email"], "database": user["database"]})
    else:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404


@app.route("/api/user-database", methods=["POST"])
def set_user_database():
    """
    Speichern oder Aktualisieren der Datenbankzuordnung eines Benutzers.
    Erwartet JSON-Body:
    {
        "email": "user@example.com",
        "database": "database1"
    }
    """
    data = request.get_json()
    email = data.get("email")
    database = data.get("database")

    if not email or not database:
        return jsonify({"error": "Email und Database sind erforderlich"}), 400

    # Benutzer erstellen oder aktualisieren
    result = user_collection.update_one(
        {"email": email},
        {"$set": {"database": database}},
        upsert=True
    )

    if result.upserted_id or result.modified_count > 0:
        return jsonify({"message": "Datenbankzuordnung erfolgreich gespeichert"}), 200
    else:
        return jsonify({"error": "Datenbankzuordnung konnte nicht gespeichert werden"}), 500

@app.route('/api/chat', methods=['POST'])
def proxy_chat():
    try:
        data = request.get_json()
        chat_message = data.get('chat_message')
        chat_history = data.get('chat_history', [])
        user_database = data.get('user_database', 'default')

        # Forward the request to the chat API
        response = requests.post(
            'http://chatapi:2000/api/chat',
            json={
                'chat_message': chat_message,
                'chat_history': chat_history,
                'user_database': user_database
            }
        )
        
        return response.json(), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=2000)