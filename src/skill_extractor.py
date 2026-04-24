import spacy

nlp = spacy.load("en_core_web_sm")

SKILLS = [
    "python","machine learning","deep learning","nlp",
    "sql","java","c++","html","css","javascript",
    "react","node","django","flask",
    "tensorflow","pytorch","data analysis",
    "power bi","tableau","excel"
]

def extract_skills(text):
    text = text.lower()
    found = set()

    for skill in SKILLS:
        if skill in text:
            found.add(skill)

    return " ".join(found)