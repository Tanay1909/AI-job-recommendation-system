from sklearn.feature_extraction.text import TfidfVectorizer

def vectorize(data):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(data)
    return vectorizer, vectors