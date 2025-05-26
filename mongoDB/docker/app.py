from flask import Flask, request, jsonify
from transformers import AutoModel, AutoTokenizer
import torch

app = Flask(__name__)

# Modell und Tokenizer global laden
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
model.eval()

@app.route('/embed', methods=['POST'])
def embed_text():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    inputs = tokenizer(text, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)

    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()

    return jsonify({"embeddings": embeddings})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4500)
