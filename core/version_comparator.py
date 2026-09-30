import os
import re
import json
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ensure NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    ENGLISH_STOPWORDS = set(stopwords.words('english'))
except:
    ENGLISH_STOPWORDS = set()

def clean_tokens(text):
    """Normalize text into alphabetic tokens without stopwords."""
    if not text:
        return []
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    tokens = word_tokenize(text)
    return [t for t in tokens if t not in ENGLISH_STOPWORDS and len(t) > 1]

def calculate_jaccard(tokens1, tokens2):
    """Jaccard similarity between two token sets."""
    set1, set2 = set(tokens1), set(tokens2)
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

class VersionComparator:
    """
    Dedicated Version Comparison engine.
    Computes:
      1. Version Similarity % (Macro-level semantic & structural closeness)
      2. Content Match / Plagiarism % (Micro-level verbatim/paraphrased copy ratio)
      3. Content Change Classification: UNCHANGED, MODIFIED, ADDED, REMOVED
    """

    def compare_versions(self, text_v1, text_v2, v1_name="Version 1", v2_name="Version 2"):
        text_v1 = text_v1 or ""
        text_v2 = text_v2 or ""

        sents_v1 = [s.strip() for s in sent_tokenize(text_v1) if s.strip()]
        sents_v2 = [s.strip() for s in sent_tokenize(text_v2) if s.strip()]

        # Edge cases
        if not sents_v1 and not sents_v2:
            return self._build_empty_result(v1_name, v2_name)
        if not sents_v1:
            return self._build_all_added_result(sents_v2, v1_name, v2_name)
        if not sents_v2:
            return self._build_all_removed_result(sents_v1, v1_name, v2_name)

        # 1. Macro-Level Document TF-IDF Cosine Similarity
        try:
            doc_vectorizer = TfidfVectorizer(tokenizer=clean_tokens, token_pattern=None)
            doc_tfidf = doc_vectorizer.fit_transform([text_v1, text_v2])
            doc_cosine = float(cosine_similarity(doc_tfidf[0], doc_tfidf[1])[0][0])
        except Exception:
            doc_cosine = calculate_jaccard(clean_tokens(text_v1), clean_tokens(text_v2))

        # 2. Sentence-Level Pairwise Similarity Matrix
        all_sents = sents_v1 + sents_v2
        sent_vectorizer = TfidfVectorizer(tokenizer=clean_tokens, token_pattern=None)
        sent_tfidf = sent_vectorizer.fit_transform(all_sents)

        v1_vecs = sent_tfidf[:len(sents_v1)]
        v2_vecs = sent_tfidf[len(sents_v1):]
        pair_matrix = cosine_similarity(v2_vecs, v1_vecs) # shape: (len(v2), len(v1))

        # Track alignments
        detailed_items = []
        matched_v1_indices = set()
        
        unchanged_count = 0
        modified_count = 0
        added_count = 0

        weighted_match_sum = 0.0

        for i, s2 in enumerate(sents_v2):
            best_j = int(pair_matrix[i].argmax())
            best_score = float(pair_matrix[i][best_j])
            
            # Supplementary Jaccard verification for short sentences
            toks1 = clean_tokens(sents_v1[best_j])
            toks2 = clean_tokens(s2)
            jaccard = calculate_jaccard(toks1, toks2)
            combined_sim = max(best_score, jaccard)

            # Classify
            if combined_sim >= 0.88 or s2.lower() == sents_v1[best_j].lower():
                status = "UNCHANGED"
                unchanged_count += 1
                matched_v1_indices.add(best_j)
                weighted_match_sum += 1.0
                score_pct = round(max(combined_sim * 100, 95.0 if s2.lower() == sents_v1[best_j].lower() else 88.0), 1)
                detailed_items.append({
                    "id": len(detailed_items) + 1,
                    "status": status,
                    "similarity": score_pct,
                    "v1_text": sents_v1[best_j],
                    "v2_text": s2,
                    "base_sentence": sents_v1[best_j],
                    "rev_sentence": s2
                })
            elif combined_sim >= 0.40:
                status = "MODIFIED"
                modified_count += 1
                matched_v1_indices.add(best_j)
                weighted_match_sum += combined_sim
                score_pct = round(combined_sim * 100, 1)
                detailed_items.append({
                    "id": len(detailed_items) + 1,
                    "status": status,
                    "similarity": score_pct,
                    "v1_text": sents_v1[best_j],
                    "v2_text": s2,
                    "base_sentence": sents_v1[best_j],
                    "rev_sentence": s2
                })
            else:
                status = "ADDED"
                added_count += 1
                detailed_items.append({
                    "id": len(detailed_items) + 1,
                    "status": status,
                    "similarity": 0.0,
                    "v1_text": "-",
                    "v2_text": s2,
                    "base_sentence": "",
                    "rev_sentence": s2
                })

        # Find REMOVED sentences (existed in V1, absent in V2)
        removed_count = 0
        for j, s1 in enumerate(sents_v1):
            if j not in matched_v1_indices:
                # Double-check max similarity against any V2 sentence
                max_sim_in_v2 = float(pair_matrix[:, j].max()) if pair_matrix.shape[0] > 0 else 0.0
                if max_sim_in_v2 < 0.40:
                    removed_count += 1
                    detailed_items.append({
                        "id": len(detailed_items) + 1,
                        "status": "REMOVED",
                        "similarity": 0.0,
                        "v1_text": s1,
                        "v2_text": "-",
                        "base_sentence": s1,
                        "rev_sentence": ""
                    })

        # Calculate Final Metrics
        total_v2 = max(len(sents_v2), 1)
        total_v1 = max(len(sents_v1), 1)

        # Content Match / Plagiarism % (Verbatim + substantial overlap ratio against V1)
        matching_percentage = round(min(100.0, (weighted_match_sum / total_v2) * 100.0), 1)

        # Version Similarity % (Macro-level similarity blending doc-level vector & sentence overlap)
        macro_sentence_sim = (weighted_match_sum / max(total_v1, total_v2))
        version_similarity = round(min(100.0, (0.50 * doc_cosine + 0.50 * macro_sentence_sim) * 100.0), 1)

        # Percentage break-downs for content change
        total_eval_units = max(len(detailed_items), 1)
        statistics = {
            "v1_sentences": len(sents_v1),
            "v2_sentences": len(sents_v2),
            "unchanged": unchanged_count,
            "unchanged_count": unchanged_count,
            "unchanged_pct": round((unchanged_count / total_v2) * 100.0, 1),
            "modified": modified_count,
            "modified_count": modified_count,
            "modified_pct": round((modified_count / total_v2) * 100.0, 1),
            "added": added_count,
            "added_count": added_count,
            "added_pct": round((added_count / total_v2) * 100.0, 1),
            "removed": removed_count,
            "removed_count": removed_count,
            "removed_pct": round((removed_count / total_v1) * 100.0, 1)
        }

        return {
            "version_similarity": version_similarity,
            "matching_percentage": matching_percentage,
            "statistics": statistics,
            "detailed_comparison": detailed_items,
            "v1_name": v1_name,
            "v2_name": v2_name
        }

    def _build_empty_result(self, v1_name, v2_name):
        return {
            "version_similarity": 100.0,
            "matching_percentage": 0.0,
            "statistics": {
                "v1_sentences": 0, "v2_sentences": 0,
                "unchanged_count": 0, "unchanged_pct": 0.0,
                "modified_count": 0, "modified_pct": 0.0,
                "added_count": 0, "added_pct": 0.0,
                "removed_count": 0, "removed_pct": 0.0
            },
            "detailed_comparison": [],
            "v1_name": v1_name,
            "v2_name": v2_name
        }

    def _build_all_added_result(self, sents_v2, v1_name, v2_name):
        items = [{"id": i+1, "status": "ADDED", "similarity": 0.0, "v1_text": "-", "v2_text": s} for i, s in enumerate(sents_v2)]
        return {
            "version_similarity": 0.0,
            "matching_percentage": 0.0,
            "statistics": {
                "v1_sentences": 0, "v2_sentences": len(sents_v2),
                "unchanged_count": 0, "unchanged_pct": 0.0,
                "modified_count": 0, "modified_pct": 0.0,
                "added_count": len(sents_v2), "added_pct": 100.0,
                "removed_count": 0, "removed_pct": 0.0
            },
            "detailed_comparison": items,
            "v1_name": v1_name,
            "v2_name": v2_name
        }

    def _build_all_removed_result(self, sents_v1, v1_name, v2_name):
        items = [{"id": j+1, "status": "REMOVED", "similarity": 0.0, "v1_text": s, "v2_text": "-"} for j, s in enumerate(sents_v1)]
        return {
            "version_similarity": 0.0,
            "matching_percentage": 0.0,
            "statistics": {
                "v1_sentences": len(sents_v1), "v2_sentences": 0,
                "unchanged_count": 0, "unchanged_pct": 0.0,
                "modified_count": 0, "modified_pct": 0.0,
                "added_count": 0, "added_pct": 0.0,
                "removed_count": len(sents_v1), "removed_pct": 100.0
            },
            "detailed_comparison": items,
            "v1_name": v1_name,
            "v2_name": v2_name
        }
