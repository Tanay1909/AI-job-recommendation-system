from sklearn.metrics.pairwise import cosine_similarity

def recommend_jobs(resume, jobs, vectorizer, job_vectors):
    resume_vec = vectorizer.transform([resume])
    scores = cosine_similarity(resume_vec, job_vectors)[0]

    jobs["match (%)"] = (scores * 100).round(2)

    return jobs.sort_values(by="match (%)", ascending=False).head(5)