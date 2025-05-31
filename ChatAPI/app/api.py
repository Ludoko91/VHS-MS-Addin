from flask import Flask, request, jsonify,render_template, Response, stream_with_context
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import requests
from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
import json
from fastapi.responses import StreamingResponse

from tools.db_tools import Simple_tools
from tools.relevant_llm import MQ

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

model_id = "qwen2.5:14b"
Settings.llm = Ollama(base_url="http://ollama:11434", api_key="token-abc123", model=model_id, request_timeout="60", temperature=0.1, is_function_calling_model=True)




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
    
@app.route('/api/chat', methods=['GET'])
def chat():
    try:
        data = request.get_json()
        query = data.get('message')
        chat_history_messages = json.loads(data.get('chat_history', '[]'))
        user_database = data.get('user_database', 'default')

        course_num_search_tool = FunctionTool.from_defaults(fn=st.course_num_search)
        date_search_tool = FunctionTool.from_defaults(fn=st.date_search)
        match_query_with_courses_tool = FunctionTool.from_defaults(fn=mq.match_query_with_courses)

        agent = ReActAgent.from_tools(
                tools=[date_search_tool, course_num_search_tool, match_query_with_courses_tool],
                chat_history=chat_history_messages,
                verbose=True
        )
        st = Simple_tools(user_database)
        mq = MQ(user_database)
        async def generate():
                print("Generating")
                try:
                    if query != "":
                        response = agent.stream_chat(message=query, chat_history=chat_history_messages)
                        for token in response.response_gen:
                            yield f"data: {token}\n\n"
                    else:
                        response = agent.chat(message=query, chat_history=chat_history_messages)
                        yield f"data: {response}\n\n"
                except Exception as e:
                    print(f"Error in stream: {str(e)}")
                    yield f"data: Error: {str(e)}\n\n"
                    yield "data: [DONE]\n\n"
            
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )        
    except Exception as e:
        print(f"An unexpected error occurred during chat_stream: {e}")
        return {"success": False, "error": str(e)}
    
    
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=2000)