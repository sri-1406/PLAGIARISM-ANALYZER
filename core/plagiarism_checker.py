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
            if best_score > 0.5:
                matches.append({
                    "input": input_sentence,
                    "matched": best_match,
                    "score": round(best_score * 100, 2),
                    "source": doc.get("source", ""),
                    "title": doc.get("title", "")
                })

                total_score += best_score
                count += 1

    overall_score = (len(matches) / len(input_sentences)) * 100 if input_sentences else 0

    return {
        "plagiarism_score": round(overall_score, 2),
        "matches": matches
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