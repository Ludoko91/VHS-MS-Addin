import requests


class embedder():

    def __init__(self) -> None:
        self.url = "http://embedding_model_api_container:4500/embed"

    def text_embedding(self,text):
        try:
            data = {"text": text}

            response = requests.post(self.url, json=data, timeout=10)

            if response.status_code == 200:
                return response.json().get("embeddings")
            else:
                print("Error with eEmbbedding response:", response.status_code, response.json())
        except:
            print(f"Error with embedding")


