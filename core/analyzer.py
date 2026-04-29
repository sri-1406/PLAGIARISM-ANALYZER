import os
import json
import re
import nltk
import joblib
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

def preprocess_text_to_tokens(text):
    """Tokenize, remove stopwords, and normalize (lowercase)."""
    if not text:
        return []
    text = text.lower()
    # Remove non-alphabetic characters and replace with space
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    tokens = word_tokenize(text)
    # Filter stopwords and short tokens
    try:
        stop_words = set(stopwords.words('english'))
    except:
        stop_words = set()
    return [t for t in tokens if t not in stop_words and len(t) > 1]

class PlagiarismAnalyzer:
    def __init__(self, data_root):
        self.data_root = data_root
        self.dataset = []
        self.doc_vectors = None
        self.sentence_unit_vectors = None
        self.unit_to_doc_map = []
        
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            self.stop_words = set()
            
        # Use a token pattern that works with preprocessed text
        self.vectorizer = TfidfVectorizer(tokenizer=preprocess_text_to_tokens, token_pattern=None)
        
        # Load index if available, otherwise fallback to live dataset loading
        if not self.load_index():
            print("Warning: Precomputed index not found. Falling back to live dataset loading (slower).")
            self._load_all_datasets(data_root)

    def load_index(self):
        """Load precomputed TF-IDF vectorizer and vectors from models directory."""
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        try:
            vectorizer_path = os.path.join(models_dir, 'vectorizer.joblib')
            doc_vec_path = os.path.join(models_dir, 'doc_vectors.joblib')
            sent_vec_path = os.path.join(models_dir, 'sentence_unit_vectors.joblib')
            metadata_path = os.path.join(models_dir, 'metadata.joblib')

            if all(os.path.exists(p) for p in [vectorizer_path, doc_vec_path, sent_vec_path, metadata_path]):
                self.vectorizer = joblib.load(vectorizer_path)
                self.doc_vectors = joblib.load(doc_vec_path)
                self.sentence_unit_vectors = joblib.load(sent_vec_path)
                metadata = joblib.load(metadata_path)
                
                self.dataset = metadata.get("dataset", [])
                self.unit_to_doc_map = metadata.get("unit_to_doc_map", [])
                print(f"Successfully loaded precomputed index with {len(self.dataset)} documents.")
                return True
        except Exception as e:
            print(f"Error loading index: {e}")
        return False

    def _load_all_datasets(self, data_root):
        """Recursively find and load all documents.json files in the data directory."""
        if not os.path.exists(data_root):
            return

        for root, _, files in os.walk(data_root):
            if 'documents.json' in files:
                file_path = os.path.join(root, 'documents.json')
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            self.dataset.extend(data.get("documents", []))
                        elif isinstance(data, list):
                            self.dataset.extend(data)
                        print(f"Loaded documents from {file_path}")
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")


    def _get_sliding_windows(self, sentences, window_size=3):
        """Create overlapping chunks of consecutive sentences."""
        windows = []
        for i in range(len(sentences) - window_size + 1):
            chunk = " ".join(sentences[i:i + window_size])
            windows.append({
                "text": chunk,
                "indices": list(range(i, i + window_size))
            })
        return windows

    def get_document_similarity(self, input_text):
        """Calculate cosine similarity between input and all documents."""
        if not self.dataset:
            return []
            
        try:
            # Use precomputed vectors if available, otherwise fit_transform (legacy)
            if self.doc_vectors is not None:
                input_vector = self.vectorizer.transform([input_text])
                similarities = cosine_similarity(input_vector, self.doc_vectors)[0]
            else:
                doc_contents = [doc['content'] for doc in self.dataset]
                all_docs = doc_contents + [input_text]
                tfidf_matrix = self.vectorizer.fit_transform(all_docs)
                similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
            
            results = []
            for i, score in enumerate(similarities):
                similarity = float(score)
                if similarity >= 0.4:
                    if similarity >= 0.8: level = "High Plagiarism"
                    elif similarity >= 0.6: level = "Moderate Plagiarism"
                    else: level = "Low Plagiarism"
                else:
                    level = "None"
                
                results.append({
                    "id": self.dataset[i]['id'],
                    "title": self.dataset[i]['title'],
                    "source_url": self.dataset[i].get('source_url', self.dataset[i].get('source', 'N/A')),
                    "score": similarity,
                    "similarity_percentage": round(similarity * 100, 2),
                    "plagiarism_level": level
                })
            
            results.sort(key=lambda x: x['score'], reverse=True)
            return results
        except Exception as e:
            print(f"Document similarity error: {e}")
            return []

    def get_sentence_matches(self, input_text, highlight_threshold=0.1, plagiarism_threshold=0.4): 
        """Advanced comparison using precomputed sentence/chunk vectors."""
        raw_sentences = sent_tokenize(input_text)
        input_sentences = [s for s in raw_sentences if len(s.split()) > 5]
        
        if not input_sentences or not self.dataset:
            return {"plagiarized_sentences": [], "total_sentences": len(input_sentences)}

        try:
            # Prepare Input Comparison Units (Sentences + Windows)
            input_windows = self._get_sliding_windows(input_sentences, window_size=2) + \
                           self._get_sliding_windows(input_sentences, window_size=3)
            input_texts = input_sentences + [w["text"] for w in input_windows]

            # Vectorization
            if self.sentence_unit_vectors is not None:
                # FAST PATH: Use precomputed dataset vectors
                input_vectors = self.vectorizer.transform(input_texts)
                dataset_vectors = self.sentence_unit_vectors
                unit_to_doc = self.unit_to_doc_map
            else:
                # SLOW PATH: Legacy fit_transform
                dataset_sentences = []
                unit_to_doc = []
                for doc in self.dataset:
                    doc_sents = sent_tokenize(doc['content'])
                    for s in doc_sents:
                        if len(s.split()) > 5:
                            dataset_sentences.append(s.strip())
                            unit_to_doc.append({"title": doc['title'], "id": doc['id'], "source_url": doc.get('source_url', 'N/A')})
                
                tfidf_matrix = self.vectorizer.fit_transform(dataset_sentences + input_texts)
                dataset_vectors = tfidf_matrix[:len(dataset_sentences)]
                input_vectors = tfidf_matrix[len(dataset_sentences):]
            
            best_matches_per_sentence = {}

            for i in range(len(input_texts)):
                similarities = cosine_similarity(input_vectors[i], dataset_vectors)[0]
                best_idx = similarities.argmax()
                best_score = float(similarities[best_idx])
                
                if best_score >= highlight_threshold:
                    match_info = unit_to_doc[best_idx]
                    if i >= len(input_sentences):
                        window = input_windows[i - len(input_sentences)]
                        for idx in window["indices"]:
                            if idx not in best_matches_per_sentence or best_score > best_matches_per_sentence[idx]["score"]:
                                best_matches_per_sentence[idx] = {"score": best_score, "info": match_info}
                    else:
                        if i not in best_matches_per_sentence or best_score > best_matches_per_sentence[i]["score"]:
                            best_matches_per_sentence[i] = {"score": best_score, "info": match_info}

            # Process into Highlighting vs Scoring (Logic preserved from original)
            highlighted_matches = []
            scoring_matches_count = 0
            scoring_scores = []
            
            sorted_indices = sorted(best_matches_per_sentence.keys())
            for idx in sorted_indices:
                match = best_matches_per_sentence[idx]
                if match["score"] >= 0.1:
                    highlighted_matches.append({
                        "sentence": input_sentences[idx],
                        "match_score": match["score"],
                        "similarity_percentage": round(match["score"] * 100, 2),
                        "source": match["info"]["title"],
                        "source_url": match["info"]["source_url"]
                    })
                if match["score"] >= plagiarism_threshold:
                    scoring_matches_count += 1
                    scoring_scores.append(match["score"])

            # Block merging (Logic preserved)
            plagiarized_blocks = []
            current_block = None
            for idx in sorted_indices:
                match = best_matches_per_sentence[idx]
                if match["score"] >= plagiarism_threshold:
                    if current_block and idx == current_block["end_idx"] + 1 and match["info"]["id"] == current_block["source_id"]:
                        current_block["sentences"].append(input_sentences[idx])
                        current_block["end_idx"] = idx
                        current_block["scores"].append(match["score"])
                    else:
                        if current_block: plagiarized_blocks.append(current_block)
                        current_block = {
                            "sentences": [input_sentences[idx]], "start_idx": idx, "end_idx": idx,
                            "source_id": match["info"]["id"], "info": match["info"], "scores": [match["score"]]
                        }
            if current_block: plagiarized_blocks.append(current_block)

            plag_blocks_formatted = []
            for block in plagiarized_blocks:
                avg_score = sum(block["scores"]) / len(block["scores"])
                level = "High Plagiarism" if avg_score >= 0.8 else "Moderate Plagiarism" if avg_score >= 0.6 else "Low Plagiarism"
                plag_blocks_formatted.append({
                    "sentence": " ".join(block["sentences"]), "match_score": avg_score,
                    "similarity_percentage": round(avg_score * 100, 2), "plagiarism_level": level,
                    "source": block["info"]["title"], "source_url": block["info"]["source_url"]
                })
            
            return {
                "highlighted_matches": highlighted_matches,
                "plagiarized_sentences_blocks": plag_blocks_formatted,
                "total_sentences": len(input_sentences),
                "scoring_count": scoring_matches_count,
                "scoring_scores": scoring_scores
            }
        except Exception as e:
            print(f"Comprehensive analysis error: {e}")
            return {"plagiarized_sentences": [], "total_sentences": 0}

    def analyze(self, input_text):
        """Entry point - logic preserved, just uses refactored helper methods."""
        if not input_text.strip(): return {"error": "Empty input text"}

        doc_matches = self.get_document_similarity(input_text)
        data = self.get_sentence_matches(input_text)
        
        total_sentences = data.get("total_sentences", 0)
        scoring_count = data.get("scoring_count", 0)
        scoring_scores = data.get("scoring_scores", [])
        
        plagiarism_percentage = (scoring_count / total_sentences * 100) if total_sentences > 0 else 0
        total_similarity_sum = sum(scoring_scores)
        average_similarity = (total_similarity_sum / scoring_count * 100) if scoring_count > 0 else 0
        
        plag_blocks = data.get("plagiarized_sentences_blocks", [])
        sources_map = {}
        for s in plag_blocks:
            source_key = f"{s['source']}_{s['source_url']}"
            if source_key not in sources_map or s["match_score"] > sources_map[source_key]["similarity"]:
                sources_map[source_key] = {
                    "url": s["source_url"], "matched_text": s["sentence"][:100] + "...",
                    "similarity": round(s["match_score"] * 100, 2), "level": s["plagiarism_level"]
                }
        
        final_sources = sorted(sources_map.values(), key=lambda x: x["similarity"], reverse=True)[:5]

        return {
            "plagiarism_percentage": round(plagiarism_percentage, 2),
            "average_similarity": round(average_similarity, 2),
            "matched_sentences": scoring_count,
            "total_sentences": total_sentences,
            "sources": final_sources,
            "highlighted_matches": data.get("highlighted_matches", []),
            "overall_percentage": round(plagiarism_percentage, 2),
            "top_matches": doc_matches[:5],
            "plagiarized_sentences": plag_blocks 
        }

    def compare_documents(self, documents):
        """Pairwise comparison of new documents - uses fit_transform locally (correct for temporary pairs)."""
        if len(documents) < 2: return {"error": "Need at least two documents."}
        doc_contents = [doc['content'] for doc in documents]
        doc_names = [doc['name'] for doc in documents]
        
        try:
            # We use a fresh vectorizer for inter-document comparison to avoid bias from the main dataset
            temp_vectorizer = TfidfVectorizer(tokenizer=preprocess_text_to_tokens, token_pattern=None)
            tfidf_matrix = temp_vectorizer.fit_transform(doc_contents)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            pairwise_results = []
            matrix_data = {}
            for i in range(len(documents)):
                matrix_data[doc_names[i]] = {}
                for j in range(len(documents)):
                    score = float(similarity_matrix[i][j])
                    matrix_data[doc_names[i]][doc_names[j]] = round(score * 100, 2)
                    if i < j:
                        sentence_matches = self._get_pairwise_sentence_matches(documents[i]['content'], documents[j]['content'], doc_names[i], doc_names[j])
                        pairwise_results.append({
                            "doc1": doc_names[i], "doc2": doc_names[j],
                            "similarity_percentage": round(score * 100, 2),
                            "matching_sentences_count": len(sentence_matches), "matches": sentence_matches
                        })
            pairwise_results.sort(key=lambda x: x['similarity_percentage'], reverse=True)
            return {"pairwise_results": pairwise_results, "matrix": matrix_data, "document_names": doc_names}
        except Exception as e:
            return {"error": f"Matrix calculation failed: {str(e)}"}

    def _get_pairwise_sentence_matches(self, text1, text2, name1, name2, threshold=0.4):
        sents1 = sent_tokenize(text1)
        sents2 = sent_tokenize(text2)
        if not sents1 or not sents2: return []
        try:
            temp_vectorizer = TfidfVectorizer(tokenizer=preprocess_text_to_tokens, token_pattern=None)
            tfidf = temp_vectorizer.fit_transform(sents1 + sents2)
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
                    level = "High Plagiarism" if best_score >= 0.8 else "Moderate Plagiarism" if best_score >= 0.6 else "Low Plagiarism"
                    matches.append({
                        "sentence1": s1_clean, "sentence2": sents2[best_idx].strip(),
                        "score": round(best_score * 100, 1), "similarity_percentage": round(best_score * 100, 2),
                        "plagiarism_level": level, "source": name2
                    })
            return matches
        except: return []
