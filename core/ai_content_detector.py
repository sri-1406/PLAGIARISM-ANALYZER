import os
import re
import threading
import hashlib
from typing import Dict, Any, List

# Standard model identifier
DEFAULT_MODEL_NAME = "Hello-SimpleAI/chatgpt-detector-roberta"

# Classification threshold constants
MIN_WORDS_FOR_RELIABLE_DETECTION = 30
HIGH_AI_THRESHOLD = 0.70
LOW_AI_THRESHOLD = 0.30

# Maximum chunks analyzed to guarantee sub-second execution on large documents
MAX_CHUNKS_TO_ANALYZE = 10
INFERENCE_BATCH_SIZE = 4

class AIContentDetector:
    """
    High-Performance AI-Generated Content Detector for English text.
    Utilizes a pretrained RoBERTa-base classifier fine-tuned on the HC3 dataset
    to estimate the likelihood that text was produced by an LLM versus written by a human.
    Optimized for sub-second inference with batching, local caching, and CPU vectorization.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = "cpu"
        self._is_loaded = False
        self._load_error = None
        self._init_lock = threading.Lock()
        self._ai_idx = 1
        self._human_idx = 0
        self._cache = {}

    @classmethod
    def get_instance(cls, model_name: str = DEFAULT_MODEL_NAME) -> "AIContentDetector":
        """Thread-safe singleton accessor to prevent repeated model reloads."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(model_name)
        return cls._instance

    def _resolve_label_indices(self):
        """
        Dynamically inspects model configuration id2label to assign AI and Human class indices.
        Guards against reversed labels or alternate model checkpoints.
        """
        if not self.model or not hasattr(self.model, 'config'):
            return

        id2label = getattr(self.model.config, 'id2label', {})
        for idx, label_str in id2label.items():
            l_lower = str(label_str).lower()
            if any(k in l_lower for k in ['chatgpt', 'ai', 'fake', 'machine', 'generated']):
                self._ai_idx = int(idx)
            elif any(k in l_lower for k in ['human', 'real', 'organic']):
                self._human_idx = int(idx)

    def load_model(self) -> bool:
        """
        Loads the pretrained tokenizer and model into memory.
        Uses local_files_only=True first to avoid HuggingFace Hub network checks (0.5s vs 47s).
        Configures optimal CPU execution threads and evaluation state.
        """
        if self._is_loaded:
            return True
        
        with self._init_lock:
            if self._is_loaded:
                return True
            try:
                import torch
                from transformers import AutoTokenizer, AutoModelForSequenceClassification

                # Configure CPU thread parallelism to prevent thread thrashing
                if not torch.cuda.is_available():
                    num_threads = min(4, max(1, os.cpu_count() or 4))
                    try:
                        torch.set_num_threads(num_threads)
                    except Exception:
                        pass

                self.device = "cuda" if torch.cuda.is_available() else "cpu"

                # Try loading from local cache first for sub-second initialization
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        self.model_name,
                        local_files_only=True
                    )
                    self.model = AutoModelForSequenceClassification.from_pretrained(
                        self.model_name,
                        local_files_only=True
                    )
                except Exception:
                    # Fallback to online download if cache not populated
                    self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                    self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)

                self.model.to(self.device)
                self.model.eval()

                self._resolve_label_indices()

                self._is_loaded = True
                self._load_error = None
                return True
            except Exception as e:
                self._load_error = str(e)
                self._is_loaded = False
                return False

    def is_ready(self) -> bool:
        return self._is_loaded

    def get_status(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "loaded": self._is_loaded,
            "device": self.device,
            "error": self._load_error,
            "ai_label_index": self._ai_idx,
            "human_label_index": self._human_idx
        }

    def _normalize_text(self, text: str) -> str:
        """
        Fast text normalizer:
        - Replaces corrupted unicode replacement chars
        - Unwraps hard mid-sentence line breaks into spaces
        - Preserves paragraph boundaries
        """
        if not text:
            return ""
        
        cleaned = re.sub(r'(\w)\ufffd(\w)', r"\1'\2", text)
        cleaned = cleaned.replace('\ufffd', ' ')

        paragraphs = re.split(r'\r?\n\s*\r?\n+', cleaned.strip())
        normalized_paragraphs = []
        for para in paragraphs:
            tokens = para.split()
            if tokens:
                normalized_paragraphs.append(' '.join(tokens))

        return '\n\n'.join(normalized_paragraphs)

    def _chunk_text(self, text: str, max_chunk_words: int = 260) -> List[Dict[str, Any]]:
        """
        Lightning-fast word-based chunking (~260 words ~= 340-380 RoBERTa tokens).
        Fits comfortably within the 512 token model limit without repeated tokenizer calls.
        """
        paragraphs = text.split("\n\n")
        chunks = []
        current_paragraphs = []
        current_words = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            para_word_count = len(para.split())

            # If a single paragraph exceeds max words, break it by sentences
            if para_word_count > max_chunk_words:
                if current_paragraphs:
                    chunks.append({
                        "text": "\n\n".join(current_paragraphs),
                        "word_count": current_words
                    })
                    current_paragraphs = []
                    current_words = 0

                sentences = re.split(r'(?<=[.!?])\s+', para)
                curr_sent_chunk = []
                curr_sent_words = 0
                for sent in sentences:
                    s_words = len(sent.split())
                    if curr_sent_words + s_words > max_chunk_words and curr_sent_chunk:
                        chunks.append({
                            "text": " ".join(curr_sent_chunk),
                            "word_count": curr_sent_words
                        })
                        curr_sent_chunk = [sent]
                        curr_sent_words = s_words
                    else:
                        curr_sent_chunk.append(sent)
                        curr_sent_words += s_words

                if curr_sent_chunk:
                    chunks.append({
                        "text": " ".join(curr_sent_chunk),
                        "word_count": curr_sent_words
                    })
                continue

            if current_words + para_word_count > max_chunk_words:
                chunks.append({
                    "text": "\n\n".join(current_paragraphs),
                    "word_count": current_words
                })
                current_paragraphs = [para]
                current_words = para_word_count
            else:
                current_paragraphs.append(para)
                current_words += para_word_count

        if current_paragraphs:
            chunks.append({
                "text": "\n\n".join(current_paragraphs),
                "word_count": current_words
            })

        return chunks

    def detect(self, text: str) -> Dict[str, Any]:
        """
        Analyzes English text and returns AI vs Human probability distribution,
        categorical classification, confidence score, and contextual disclaimer.
        Optimized with caching, batched tensor inference, and smart sampling.
        """
        # 1. Input sanitization
        if not text or not text.strip():
            return {
                "error": "No text provided for analysis.",
                "valid": False
            }

        cleaned_text = self._normalize_text(text)
        words = cleaned_text.split()
        word_count = len(words)
        char_count = len(cleaned_text)

        if word_count == 0:
            return {
                "error": "No readable text provided for analysis.",
                "valid": False
            }

        # 2. Check LRU / Hash Cache
        text_hash = hashlib.sha256(cleaned_text.encode('utf-8')).hexdigest()
        if text_hash in self._cache:
            return self._cache[text_hash]

        # 3. Ensure model is loaded
        if not self.load_model():
            return {
                "error": f"Failed to initialize AI detection model: {self._load_error or 'Unknown error'}",
                "valid": False,
                "model_status": self.get_status()
            }

        import torch

        is_short_text = word_count < MIN_WORDS_FOR_RELIABLE_DETECTION

        # 4. Chunk text into ~260-word segments
        chunks = self._chunk_text(cleaned_text, max_chunk_words=260)
        if not chunks:
            chunks = [{"text": cleaned_text, "word_count": word_count}]

        # 5. Smart sampling for large documents: cap at MAX_CHUNKS_TO_ANALYZE
        total_chunks_detected = len(chunks)
        if total_chunks_detected > MAX_CHUNKS_TO_ANALYZE:
            # Select head, evenly spaced middle, and tail chunks
            head = chunks[:3]
            tail = chunks[-3:]
            mid_slice = chunks[3:-3]
            step = max(1, len(mid_slice) // 4)
            middle = [mid_slice[i] for i in range(0, len(mid_slice), step)][:4]
            selected_chunks = head + middle + tail
        else:
            selected_chunks = chunks

        chunk_results = []
        weighted_ai_prob_sum = 0.0
        total_weight = 0

        # 6. Batched Model Inference with torch.inference_mode()
        try:
            with torch.inference_mode():
                for b_start in range(0, len(selected_chunks), INFERENCE_BATCH_SIZE):
                    batch = selected_chunks[b_start:b_start + INFERENCE_BATCH_SIZE]
                    batch_texts = [c["text"] for c in batch]

                    inputs = self.tokenizer(
                        batch_texts,
                        padding=True,
                        truncation=True,
                        max_length=512,
                        return_tensors="pt"
                    ).to(self.device)

                    outputs = self.model(**inputs)
                    batch_probs = torch.softmax(outputs.logits, dim=-1).cpu().tolist()

                    for idx, probs in enumerate(batch_probs):
                        ai_p = probs[self._ai_idx] if len(probs) > self._ai_idx else 0.5
                        human_p = probs[self._human_idx] if len(probs) > self._human_idx else 0.5
                        
                        weight = max(1, batch[idx]["word_count"])
                        weighted_ai_prob_sum += ai_p * weight
                        total_weight += weight

                        chunk_results.append({
                            "chunk_index": b_start + idx + 1,
                            "token_count": weight,
                            "ai_probability": round(ai_p * 100, 1),
                            "human_probability": round(human_p * 100, 1)
                        })

            final_ai_prob = weighted_ai_prob_sum / total_weight if total_weight > 0 else 0.5
            final_human_prob = 1.0 - final_ai_prob

        except Exception as e:
            return {
                "error": f"Inference execution failed: {str(e)}",
                "valid": False
            }

        # 7. Classification determination
        if is_short_text:
            classification = "Inconclusive (Text too short)"
            confidence = "Low"
            assessment_detail = (
                f"The provided text contains only {word_count} word{'s' if word_count != 1 else ''}. "
                f"Statistical AI content detectors require at least {MIN_WORDS_FOR_RELIABLE_DETECTION} words "
                "for meaningful pattern analysis."
            )
        elif final_ai_prob >= HIGH_AI_THRESHOLD:
            classification = "Likely AI-generated"
            confidence = "High" if final_ai_prob >= 0.85 else "Moderate"
            assessment_detail = (
                "The sequence patterns, token distributions, and structural style "
                "strongly match patterns identified by the neural classifier as machine-generated text."
            )
        elif final_ai_prob <= LOW_AI_THRESHOLD:
            classification = "Likely human-written"
            confidence = "High" if final_ai_prob <= 0.15 else "Moderate"
            assessment_detail = (
                "The sequence patterns, structural style, and syntactic variance "
                "strongly align with patterns identified by the neural classifier as organic human writing."
            )
        else:
            classification = "Inconclusive / Mixed"
            confidence = "Low"
            assessment_detail = (
                "The document exhibits mixed stylistic signals, showing traits common to both human writing and AI-assisted generation."
            )

        result_payload = {
            "valid": True,
            "word_count": word_count,
            "char_count": char_count,
            "chunks_analyzed": len(selected_chunks),
            "total_chunks": total_chunks_detected,
            "ai_probability": round(final_ai_prob * 100, 1),
            "human_probability": round(final_human_prob * 100, 1),
            "classification": classification,
            "confidence": confidence,
            "assessment_detail": assessment_detail,
            "is_short_text": is_short_text,
            "model_info": {
                "name": self.model_name,
                "architecture": "RoBERTa-base (HC3 fine-tuned)",
                "device": self.device
            },
            "disclaimer": (
                "AI content detection is probabilistic and heuristic. Reported scores are raw softmax likelihoods "
                "from the fine-tuned RoBERTa classifier. They should be used as an informative indicator rather than "
                "definitive proof of authorship."
            ),
            "chunk_details": chunk_results if len(chunk_results) > 1 else None
        }

        # Cache result (keep cache size bounded to last 100 items)
        if len(self._cache) > 100:
            self._cache.pop(next(iter(self._cache)))
        self._cache[text_hash] = result_payload

        return result_payload
