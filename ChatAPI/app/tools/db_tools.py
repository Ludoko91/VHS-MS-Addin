from pymongo import MongoClient
import os
from datetime import datetime
import requests


class Simple_tools():
    def __init__(self,collection_id):    
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo:27017/')
        client = MongoClient(mongo_uri)
        db = client.vhs
        self.collection = db[collection_id]

    def date_search(self,date):
        """Useful to search for courses via dates, Format for search: DD.MM.YYYY"""


        date_strip_1 = date.replace(".","")
        date_strip = date_strip_1.replace("-","")
        date = datetime.strptime(date_strip, "%d%m%Y").strftime("%d.%m.%Y")
        courses = list(self.collection.find({"date": str(date)}, {"_id": 0}))
        results = []
        for course in courses:
            x = [course["description"],course["date"],course["kursnr"]]
            results.append(x)
        
        if not courses:
            return f"no course found"
        else:
            return f"Course data for date {date}. Data:{results}"
        
    def course_num_search(self,coursenumber):
        """Useful to search for course numbers, only numbers allowed"""


        course = self.collection.find_one({"kursnr": coursenumber.strip()}, {"_id": 0})
        data = [course["description"],course["date"],course["kursnr"]]
        if course:
            return f"This is the course with the coursnumber {coursenumber}:{data}"
        else:
            return f"Course not found"
        
    def course_keyword_search(self,question):
        """Useful to search for a course via keyword"""
        url = "http://flask_app:5000/api/courses/search"
        json ={
            "question": question
        }
        response = requests.post(url, json=json)
        answer = response.json()
        return f"Here are the courses your were looking for: {answer}"