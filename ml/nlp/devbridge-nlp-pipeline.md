# Natural Language Processing (NLP) Technical Specification & Implementation Report

This document outlines the core Natural Language Processing (NLP) algorithms, feature engineering pipelines, semantic matching architectures, and supervised machine learning classifiers implemented across the codebase. Each section details the underlying theory, file locations, and searchable references for code auditability.

---

### 1. Text Preprocessing & Lexical Normalization

* **File Location:** `ml/nlp/text.py`
* **NLP Theory:** Raw text normalization, case-folding, whitespace collapsing, tokenization, stopword removal, and rule-based morphological stemming.
* **Implementation Details:**
* Converts unstructured strings into uniform lowercase tokens using regex pattern matching.
* Filters out high-frequency, semantically empty syntactic words (stopwords) to isolate domain-specific content words.
* Applies heuristic suffix-stripping to collapse plural nouns and inflected variants into canonical root forms.

**Searchable References & Code Snippets:**

* Normalize text and tokenization:

```python
def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())

```

* Keyword extraction and stopword filtering:

```python
def extract_keywords(text: str) -> set[str]:
    keywords = set()
    for token in tokenize(text):
        if len(token) > 2 and token not in STOPWORDS:
            keywords.add(_light_stem(token))
    return keywords

```

---

### 2. Lexical Metrics & Vector Similarity Engineering

* **File Location:** `ml/nlp/features.py`
* **NLP Theory:** String distance metrics, set-based lexical overlap (Jaccard similarity), dense vector space modeling, and geometric similarity measures (Cosine similarity).
* **Implementation Details:**
* **Jaccard Similarity:** Measures set overlap ratio (`intersection / union`) for extracted keywords and categorical tags.
* **String Ratio:** Utilizes Python's `SequenceMatcher` to calculate character-level edit distance and title similarity.
* **Cosine Similarity:** Computes the normalized dot product between multi-dimensional dense sentence embeddings to quantify semantic relatedness independent of text length.

**Searchable References & Code Snippets:**

* Jaccard similarity and keyword overlap:

```python
def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)

def keyword_overlap(left: str, right: str) -> float:
    return jaccard(extract_keywords(left), extract_keywords(right))

```

* Vector cosine similarity:

```python
def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator == 0.0:
        return 0.0
    return float(np.dot(left, right) / denominator)

```

---

### 3. Semantic Retrieval & Fallback Matching Engine

* **File Location:** `ml/nlp/matcher.py`
* **NLP Theory:** Dense vector retrieval, candidate pool pre-filtering, and hybrid fallback routing (Semantic embedding matching vs. Lexical keyword matching).
* **Implementation Details:**
* Implements `SemanticMatcher` to manage text comparison workflows.
* Pre-filters a large candidate corpus down to a manageable pool using fast lexical keyword overlap before executing costly dense vector comparisons.
* Features automated resilience fallback: if external or local embedding services encounter errors, the system gracefully degrades to keyword-based matching.

**Searchable References & Code Snippets:**

* Core matcher class and routing:

```python
class SemanticMatcher:
    async def match(self, submission: Submission, problems: list[dict[str, Any]], use_ai: bool) -> MatchOutcome:
        pool = self._select_pool(submission, problems)
        if not use_ai:
            return self._keyword_match(submission, pool)
        try:
            return await self._embedding_match(submission, pool)
        except AIProviderError as error:
            outcome = self._keyword_match(submission, pool)
            outcome.ai_error = error
            return outcome

```

---

### 4. Persistent Vector Caching & Version Control

* **File Location:** `ml/nlp/embedding_cache.py`
* **NLP Theory:** Hash-based memoization for high-dimensional vector representations to avoid redundant model inference computations.
* **Implementation Details:**
* Implements `EmbeddingCache` to store computed sentence vectors on disk as atomic JSON payloads.
* Incorporates model identifiers and text preparation version tags (`TEXT_PREP_VERSION`) into cryptographic hashes (`SHA-256`) to automatically invalidate stale caches whenever models or preprocessing rules change.

**Searchable References & Code Snippets:**

* Cache key generation and lookup:

```python
class EmbeddingCache:
    def key_for(self, text: str) -> str:
        raw = f"{self.model_id}\0{TEXT_PREP_VERSION}\0{text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, text: str) -> list[float] | None:
        with self._lock:
            return self._entries.get(self.key_for(text))

```

---

### 5. Prompt Engineering & Contextual Generation (RAG)

* **File Location:** `ml/nlp/srs.py`
* **NLP Theory:** Retrieval-Augmented Generation (RAG), structured prompt templating, and automated output validation against engineering standards.
* **Implementation Details:**
* Uses `SrsGenerator` to encapsulate problem metadata, descriptions, constraints, and crowdsourced community reports into standardized XML-delimited prompt structures (`<problem>`).
* Enforces compliance checks against structured sections (ISO/IEC/IEEE 29148 requirements) to parse, clean, and validate generated technical specifications.

**Searchable References & Code Snippets:**

* Context building and document review:

```python
def build_user_prompt(context: SrsContext) -> str:
    lines = [
        "<problem>",
        f"Title: {context.title}",
        f"Description: {context.description}",
        f"Desired outcome: {context.outcome or 'TBD'}"
    ]
    lines.append("</problem>")
    return "\n".join(lines)

class SrsGenerator:
    async def generate(self, context: SrsContext) -> SrsDraft:
        result = await self.provider.generate(SYSTEM_PROMPT, build_user_prompt(context))
        markdown = clean_model_output(result.text)
        return SrsDraft(markdown=markdown, model=result.model, ...)

```

---

### 6. Pairwise Similarity Dataset Construction & Feature Maps

* **File Location:** `ml/nlp/training_data.py`
* **NLP Theory:** Supervised dataset assembly, feature vector serialization, and human-in-the-loop feedback aggregation for semantic classifier calibration.
* **Implementation Details:**
* Maps annotated problem pairs into structured training rows containing multi-dimensional feature dictionaries.
* Aggregates runtime user feedback to expand training datasets dynamically.

**Searchable References & Code Snippets:**

* Training row builder:

```python
def build_training_rows(dataset: dict[str, Any], feedback: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [row_from_labelled_pair(pair) for pair in dataset.get("labelled_pairs", [])]
    for record in feedback:
        row = row_from_feedback(record)
        if row is not None:
            rows.append(row)
    return {
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "row_count": len(rows),
        "rows": rows
    }

```

---

### 7. Supervised Multi-Layer Perceptron (MLP) Classifier & Evaluation

* **File Locations:** `ml/nlp/classifier/classifier.py`, `ml/nlp/classifier/train_model.py`
* **ML Theory:** Feed-forward artificial neural network trained via backpropagation with an Adam optimizer and ReLU activation, classifying candidate pairs into binary duplicate states (`1` for same underlying issue, `0` for unrelated/different).
* **Implementation Details:**
* **Input Layer:** Accepts a strict 4-feature vector: `[cosine_similarity, title_similarity, keyword_overlap, tag_overlap]`.
* **Hidden Layer:** 8 neurons with ReLU activation.
* **Output Layer:** 1 neuron with Sigmoid activation.
* **Evaluation Metrics:** Evaluated on stratified test splits yielding **83.33% Accuracy**, **100% Precision**, **66.67% Recall**, and an **80.00% F1-Score**.
* **Model Persistence:** Serializes trained parameters, scalers, and feature schemas into atomic binary weights (`artifact_mlp_model.pkl`).

**Searchable References & Code Snippets:**

* MLP Architecture and Feature Extraction:

```python
class DuplicateMLPClassifier:
    def __init__(self, model_path: str = None):
        self.scaler = StandardScaler()
        self.mlp = MLPClassifier(
            hidden_layer_sizes=(8,),
            activation='relu',
            solver='adam',
            max_iter=1000,
            random_state=42
        )

    def _extract_feature_vector(self, features: Dict[str, Any]) -> list:
        return [
            float(features.get("cosine_similarity") or 0.0),
            float(features.get("title_similarity") or 0.0),
            float(features.get("keyword_overlap") or 0.0),
            float(features.get("tag_overlap") or 0.0)
        ]

```