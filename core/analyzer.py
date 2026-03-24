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
        """Compare sentences of input with each sentence in the dataset using TF-IDF and Cosine Similarity."""
        input_sentences = sent_tokenize(input_text)
        if not input_sentences or not self.dataset:
            return {"plagiarized_sentences": []}

        # Collect all sentences from the dataset across all documents
        dataset_sentences = []
        sentence_to_doc = [] # Map index to document details
        
        for doc in self.dataset:
            doc_sents = sent_tokenize(doc['content'])
            for s in doc_sents:
                s_clean = s.strip()
                if s_clean:
                    dataset_sentences.append(s_clean)
                    sentence_to_doc.append({"title": doc['title'], "id": doc['id']})
        
        if not dataset_sentences:
            return {"plagiarized_sentences": []}

        try:
            # We fit on all sentences (dataset + current input) to correctly calculate IDF
            all_sents = dataset_sentences + input_sentences
            tfidf_matrix = self.vectorizer.fit_transform(all_sents)
            
            # Vectors for dataset: 0 to len(dataset_sentences)-1
            # Vectors for input: len(dataset_sentences) to end
            dataset_vectors = tfidf_matrix[:len(dataset_sentences)]
            input_vectors = tfidf_matrix[len(dataset_sentences):]
            
            plagiarized_sentences = []
            
            for i, input_sent in enumerate(input_sentences):
                input_sent_clean = input_sent.strip()
                if not input_sent_clean:
                    continue
                
                # Calculate cosine similarity between current input sentence and all dataset sentences
                similarities = cosine_similarity(input_vectors[i], dataset_vectors)[0]
                
                best_idx = similarities.argmax()
                best_score = float(similarities[best_idx])
                
                if best_score >= threshold:
                    plagiarized_sentences.append({
                        "sentence": input_sent_clean,
                        "match_score": best_score,
                        "source": sentence_to_doc[best_idx]["title"]
                    })
            
            return {"plagiarized_sentences": plagiarized_sentences}
        except Exception as e:
            print(f"Error in sentence-level analysis: {e}")
            return {"plagiarized_sentences": []}

    def analyze(self, input_text):
        """Main analysis entry point against the static dataset."""
        if not input_text.strip():
            return {"error": "Empty input text"}

        doc_matches = self.get_document_similarity(input_text)
        sentence_data = self.get_sentence_matches(input_text, threshold=0.7)
        
        overall = (doc_matches[0]['score'] * 100) if doc_matches else 0
        
        return {
            "overall_percentage": round(overall, 2),
            "top_matches": [m for m in doc_matches if m['score'] > 0.1][:3],
            "plagiarized_sentences": sentence_data["plagiarized_sentences"]
        }

    def compare_documents(self, documents):
        """
        Compare a list of documents with each other (Inter-Document Comparison).
        documents: List of dicts [{"name": "doc1.txt", "content": "..."}]
        """
        if len(documents) < 2:
            return {"error": "Need at least two documents for comparison."}

        doc_contents = [doc['content'] for doc in documents]
        doc_names = [doc['name'] for doc in documents]
        
        # Calculate pairwise document similarity
        try:
            tfidf_matrix = self.vectorizer.fit_transform(doc_contents)
            similarity_matrix = cosine_similarity(tfidf_matrix)
        except Exception as e:
            return {"error": f"Matrix calculation failed: {str(e)}"}

        pairwise_results = []
        matrix_data = {} # For the UI matrix representation

        for i in range(len(documents)):
            matrix_data[doc_names[i]] = {}
            for j in range(len(documents)):
                score = float(similarity_matrix[i][j])
                matrix_data[doc_names[i]][doc_names[j]] = round(score * 100, 2)
                
                if i < j: # Only store unique pairs for the list
                    # Sentence-level comparison for this specific pair
                    sentence_matches = self._get_pairwise_sentence_matches(
                        documents[i]['content'], 
                        documents[j]['content'],
                        doc_names[i],
                        doc_names[j]
                    )
                    
                    pairwise_results.append({
                        "doc1": doc_names[i],
                        "doc2": doc_names[j],
                        "similarity_percentage": round(score * 100, 2),
                        "matching_sentences_count": len(sentence_matches),
                        "matches": sentence_matches
                    })

        # Sort results by similarity descending
        pairwise_results.sort(key=lambda x: x['similarity_percentage'], reverse=True)

        return {
            "pairwise_results": pairwise_results,
            "matrix": matrix_data,
            "document_names": doc_names
        }

    def _get_pairwise_sentence_matches(self, text1, text2, name1, name2, threshold=0.7):
        """Helper to find matching sentences between two specific documents."""
        sents1 = sent_tokenize(text1)
        sents2 = sent_tokenize(text2)
        
        if not sents1 or not sents2:
            return []

        try:
            all_sents = sents1 + sents2
            tfidf = self.vectorizer.fit_transform(all_sents)
            
            vecs1 = tfidf[:len(sents1)]
            vecs2 = tfidf[len(sents1):]
            
            matches = []
            for i, s1 in enumerate(sents1):
                s1_clean = s1.strip()
                if not s1_clean: continue
                
                sims = cosine_similarity(vecs1[i], vecs2)[0]
                best_idx = sims.argmax()
                best_score = float(sims[best_idx])
                
                if best_score >= threshold:
                    matches.append({
                        "sentence1": s1_clean,
                        "sentence2": sents2[best_idx].strip(),
                        "score": round(best_score * 100, 1),
                        "source": name2
                    })
            return matches
        except:
            return []



