import os
import json
import re
from difflib import SequenceMatcher

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATHS = [
    os.path.join(BASE_DIR, "data", "blogs", "documents.json"),
    os.path.join(BASE_DIR, "data", "wikipedia", "documents.json")
]

# ✅ Load documents
def load_documents():
    documents = []

    for path in DATA_PATHS:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

                if isinstance(data, dict):
                    documents.extend(data.get("documents", []))
                elif isinstance(data, list):
                    documents.extend(data)

    print("✅ Loaded documents:", len(documents))
    return documents


# ✅ Split sentences
def split_sentences(text):
    sentences = re.split(r'[.!?]', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]


# ✅ Similarity
def get_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


# 🔥 Main function
def check_plagiarism(input_text):
    documents = load_documents()
    input_sentences = split_sentences(input_text)

    matches = []
    total_score = 0
    count = 0

    for input_sentence in input_sentences:
        for doc in documents:
            doc_sentences = split_sentences(doc.get("content", ""))

            # ✅ Find BEST match only
            best_match = None
            best_score = 0

            for doc_sentence in doc_sentences:
                score = get_similarity(input_sentence.lower(), doc_sentence.lower())

                if score > best_score:
                    best_score = score
                    best_match = doc_sentence

            # ✅ Apply threshold
            if best_score >= 0.4:
                if best_score >= 0.8:
                    level = "High Plagiarism"
                elif best_score >= 0.6:
                    level = "Moderate Plagiarism"
                else:
                    level = "Low Plagiarism"
                    
                matches.append({
                    "input": input_sentence,
                    "matched": best_match,
                    "score": round(best_score * 100, 2),
                    "similarity_percentage": round(best_score * 100, 2),
                    "plagiarism_level": level,
                    "source": doc.get("source", ""),
                    "title": doc.get("title", "")
                })

                total_score += best_score
                count += 1

    # Structured Output Calculation
    total_input_sentences = len(input_sentences)
    plagiarism_percentage = (count / total_input_sentences) * 100 if total_input_sentences > 0 else 0
    average_similarity = (total_score / count * 100) if count > 0 else 0
    
    # Format sources list
    sources_list = []
    for m in matches:
        sources_list.append({
            "url": m.get("source", "N/A"), # Assuming source field contains the URL in this script
            "matched_text": m["input"],
            "similarity": m["score"]
        })

    return {
        "plagiarism_percentage": round(plagiarism_percentage, 2),
        "average_similarity": round(average_similarity, 2),
        "matched_sentences": count,
        "total_sentences": total_input_sentences,
        "sources": sources_list[:5] # Limit results to top 5 as requested
    }


# 🔥 Test run
if __name__ == "__main__":
    documents = load_documents()

    if documents:
        sample_text = documents[0]["content"][:200]

        print("\n🧪 Testing with dataset content...\n")
        result = check_plagiarism(sample_text)

        print("\n🔍 Plagiarism Score:", result["plagiarism_score"])
        print("\n📄 Matches:\n")

        for m in result["matches"][:5]:  # show only top 5
            print("Input:", m["input"])
            print("Matched:", m["matched"])
            print("Score:", m["score"])
            print("Source:", m["source"])
            print("-" * 50)
    else:
        print("❌ No documents found.")