import time
from llama_index.llms.openai_like import OpenAILike
import re
import requests
from pymongo import MongoClient
import os

 
#questions = ["Ich habe Rückenschmerzen! Können Sie mir einen Kurs empfehlen?", "Ich habe eine Kopfverkrampfung! Können Sie mir einen Kurs empfehlen?", "Ich habe eine Kopfverkrampfung! Können Sie mir einen Kurs empfehlen?", "Ich habe eine Kopfverkrampfung! Können Sie mir einen Kurs empfehlen?"]
 
# unsloth/tinyllama-bnb-4bit is a pre-quantized checkpoint.
model_id = "meta-llama/Llama-3.2-3B-Instruct"
llm = OpenAILike(api_base="http://vllm:8000/v1", api_key="token-abc123", model= model_id, request_timeout="30",temperature=0.1, trust_remote_code=True, max_model_len=1024, enable_prefix_caching=True, max_num_seqs=200)
#llm = OpenAILike(api_base="http://192.168.178.57:8000/v1", api_key="token-abc123", model= model_id, request_timeout="30",temperature=0.1, trust_remote_code=True, max_model_len=1024, enable_prefix_caching=True, max_num_seqs=200)

class MQ():
    def __init__(self,collection_id):  
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo:27017/')
        client = MongoClient(mongo_uri)
        db = client.vhs
        self.collection = db[collection_id]


    def match_query_with_courses(self,question):

        """Useful to find relevant Inforamtion with a question"""

        courses = list(self.collection.find({}, {"_id": 0}))  # hide the _id-Feld

        i = []
        for course in courses:
            x = course["description"]
            i.append(x)


        prompts = []
        for text in i:
                prompt = f"""
                    You are an expert at scoring the relevance of a course description to a query. You are only allowed to respond with a single integer.
                    Given a query and a passage, you must provide a score on an integer scale of 0 to 3 with the follwing meaning:
                    0 = represent that the passage has nothing to do with the query,
                    1 = represents that the passage seems related to the query but does not contain any part of an answer to it,
                    2 = represents that the passage contains a partial or complete answer for the query, but the answer may be a bit unclear, or hidden
                    amongst extraneous information and
                    3 = represents that the passage is dedicated to the query and contains a partial or complete answer to it.

                    Split the given problem into steps:
                    Consider the underlying intent of the search. Measure how well the content matches a likely intent of the query.
                    Consider the aspects above and the relative importance of each and decide on a final score for the following problem:
                    Passage: {text}
                    Query: {question}

                    Only respond with a single integer which is the final score for the problem. Do not provide anything else!

                """
                #prompts.append(tokenizer.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False))
                prompts.append(prompt)
        print(f"courses checked: {len(prompts)}")

        start_time = time.time()  # Start timing
        responses = llm.complete(
            prompt=prompts,
        )

        end_time = time.time()  # End timing
        elapsed_time = end_time - start_time  # Calculate elapsed time
        try:
            liste =[]
            for response in responses:
                liste.append(response)

            comp_list = []
            for i in liste[2][1]:
                comp_list.append(i)

            obj_list = []
            for a in comp_list[1]:
                obj_list.append(a)

            answerlist = []
            for p in obj_list[1]:
                answerlist.append(p.text)

            scores = []
            if not answerlist: 
                return f"Error" 
            else:
                for a in answerlist:
                    try:
                        scores.append(re.search('[0-9]+', a).group())
                    except:
                        print(a)
                        scores.append("0")

            final_list = []
            for c,s in zip(course,scores):
                if s == "3":
                    final_list.append(c)

        except IndexError as e:
            print(f"Error with conversion: {e}")
            final_list = ["no courses found"]

        print(f"FINISHED in {elapsed_time:.2f} seconds")
        if not final_list:
            return f"Keine Informationen gefunden"
        else:
            return f"Hier sind die gesuchten Informationen: {final_list}"

    #print(match_query_with_courses(questions[0]))
