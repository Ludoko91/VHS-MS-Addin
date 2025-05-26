import requests

def course_num_search(coursenumber):
    """Useful to search for course numbers, only numbers allowed"""

    url = f"http:// flask_app:5000/api/courses/{coursenumber}"

    response = requests.get(url)
    data = response.json()
    x = data
    print(x,data)
    if "error" in x:
        return f"no course found"
    else:
        return f"This are the course data you were looking for: {x}"
    


#print(course_num_search("2423700")) 