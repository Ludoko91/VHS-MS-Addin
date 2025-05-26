import requests

def course_keyword_search(question):
    """Useful to search for a course via keyword"""
    url = "http://flask_app:5000/api/courses/search"
    json ={
        "question": question
    }
    response = requests.post(url, json=json)
    answer = response.json()
    return f"Here are the courses your were looking for: {answer}"