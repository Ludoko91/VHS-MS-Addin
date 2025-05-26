import requests
from pymongo import MongoClient
import os
from datetime import datetime


mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo:27017/')
client = MongoClient(mongo_uri)
db = client.vhs
collection = db.courses

def date_search_old(date):
    """Useful to search for courses via dates, Format for search: DD.MM.YYYY"""


    date_strip_1 = date.replace(".","")
    date_strip = date_strip_1.replace("-","")
    url = f"http://flask_app:5000/api/courses/date/{date_strip}"

    response = requests.get(url)
    data = response.json()
    if "error" in data:
        return f"no course found"
    else:
        return f"Course data for {date}: {data}"
    
def date_search(date):
    """Useful to search for courses via dates, Format for search: DD.MM.YYYY"""


    date_strip_1 = date.replace(".","")
    date_strip = date_strip_1.replace("-","")
    date = datetime.strptime(date_strip, "%d%m%Y").strftime("%d.%m.%Y")
    courses = list(collection.find({"date": str(date)}, {"_id": 0}))
    results = []
    for course in courses:
        x = [course["description"],course["date"],course["kursnr"]]
        results.append(x)
    
    if not courses:
        return f"no course found"
    else:
        return f"Course data for {date} found: {results}"
    
