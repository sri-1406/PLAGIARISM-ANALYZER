import json
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ensure NLTK resources are available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class PlagiarismAnalyzer:
    def __init__(self, dataset_path):
        try:
            with open(dataset_path, 'r') as f:
                self.dataset = json.load(f)
        except Exception as e:
            print(f"Error loading dataset: {e}")
            self.dataset = []
        
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            self.stop_words = set()
            
        # Use a token pattern that works with preprocessed text
        self.vectorizer = TfidfVectorizer(tokenizer=self.preprocess_text_to_tokens, token_pattern=None)

    def preprocess_text_to_tokens(self, text):
        """Tokenize, remove stopwords, and normalize (lowercase)."""
        if not text:
            return []
        text = text.lower()
        # Remove non-alphabetic characters and replace with space
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        tokens = word_tokenize(text)
        # Filter stopwords and short tokens
        return [t for t in tokens if t not in self.stop_words and len(t) > 1]

    def get_document_similarity(self, input_text):
        """Calculate cosine similarity between input and all documents."""
        if not self.dataset:
            return []
            
        doc_contents = [doc['content'] for doc in self.dataset]
        all_docs = doc_contents + [input_text]
        
        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_docs)
            similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
            
            results = []
            for i, score in enumerate(similarities):
                results.append({
                    "id": self.dataset[i]['id'],
                    "title": self.dataset[i]['title'],
                    "score": float(score)
                })
            
            results.sort(key=lambda x: x['score'], reverse=True)
            return results
        except ValueError:
            return []

    def get_sentence_matches(self, input_text, threshold=0.7): 
        """Compare sentences of input with each document and identify strong matches (>= threshold)."""
        input_sentences = sent_tokenize(input_text)
        plagiarized_sentences = []
        
        if not input_sentences or not self.dataset:
            return {"plagiarized_sentences": []}

        for input_sent in input_sentences:
            input_sent_clean = input_sent.strip()
            if not input_sent_clean:
                continue
            
            best_match = None
            
            for doc in self.dataset:
                doc_sentences = sent_tokenize(doc['content'])
                
                for doc_sent in doc_sentences:
                    try:
                        s1_tokens = set(self.preprocess_text_to_tokens(input_sent_clean))
                        s2_tokens = set(self.preprocess_text_to_tokens(doc_sent))
                        
                        if not s1_tokens or not s2_tokens:
                            continue
                            
                        # Jaccard Similarity
                        intersection = s1_tokens.intersection(s2_tokens)
                        union = s1_tokens.union(s2_tokens)
                        score = float(len(intersection) / len(union))
                        
                        if score >= threshold:
                            if best_match is None or score > best_match["score"]:
                                best_match = {
                                    "score": score,
                                    "doc_title": doc['title'],
                                    "original_sent": doc_sent
                                }
                    except Exception as e:
                        print(f"Error comparing sentences: {e}")
                        continue
            
            if best_match:
                plagiarized_sentences.append({
                    "sentence": input_sent_clean,
                    "match_score": best_match["score"],
                    "source": best_match["doc_title"]
                })
        
        return {
            "plagiarized_sentences": plagiarized_sentences
        }

    def analyze(self, input_text):
        """Main analysis entry point."""
        if not input_text.strip():
            return {"error": "Empty input text"}

        doc_matches = self.get_document_similarity(input_text)
        # Strictly enforce 0.7 threshold for highlighting
        sentence_data = self.get_sentence_matches(input_text, threshold=0.7)
        
        # Calculate overall plagiarism as the highest document similarity score (cosine)
        overall = (doc_matches[0]['score'] * 100) if doc_matches else 0
        
        return {
            "overall_percentage": round(overall, 2),
            "top_matches": [m for m in doc_matches if m['score'] > 0.1][:3],
            "plagiarized_sentences": sentence_data["plagiarized_sentences"]
        }



