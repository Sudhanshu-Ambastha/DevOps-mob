# Natural Language Processing (NLP) Technical Specification & Implementation Report

This document outlines the core Natural Language Processing (NLP) algorithms, feature engineering pipelines, and semantic matching architectures implemented across the codebase. Each section details the underlying NLP theory, the specific file, and searchable class/function references for code auditability.

---

### 1. Text Preprocessing & Lexical Normalization

- **File Location:** `ml/nlp/text.py`
- **NLP Theory:** Raw text normalization, case-folding, whitespace collapsing, tokenization, stopword removal, and rule-based morphological stemming.
- **Implementation Details:**
- Converts unstructured strings into uniform lowercase tokens using regex pattern matching.
- Filters out high-frequency, semantically empty syntactic words (stopwords) to isolate domain-specific content words.
- Applies a heuristic suffix-stripping stemmer to collapse plural nouns and inflected variants into canonical root forms.

**Searchable References & Code Snippets:**

- Normalize text and tokenization:

```python
def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())

```

- Keyword extraction and stopword filtering:

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

- **File Location:** `ml/nlp/features.py`
- **NLP Theory:** String distance metrics, set-based lexical overlap (Jaccard similarity), dense vector space modeling, and geometric similarity measures (Cosine similarity).
- **Implementation Details:**
- **Jaccard Similarity:** Measures set overlap ratio (`intersection / union`) for extracted keywords and categorical tags.
- **String Ratio:** Utilizes Python's `SequenceMatcher` to calculate character-level edit distance and title similarity.
- **Cosine Similarity:** Computes the normalized dot product between multi-dimensional dense sentence embeddings to quantify semantic relatedness independent of text length.

**Searchable References & Code Snippets:**

- Jaccard similarity and keyword overlap:

```python
def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)

def keyword_overlap(left: str, right: str) -> float:
    return jaccard(extract_keywords(left), extract_keywords(right))

```

- Vector cosine similarity:

```python
def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator == 0.0:
        return 0.0
    return float(np.dot(left, right) / denominator)

```

---

### 3. Semantic Retrieval & Fallback Matching Engine

- **File Location:** `ml/nlp/matcher.py`
- **NLP Theory:** Dense vector retrieval, candidate pool pre-filtering, and hybrid fallback routing (Semantic embedding matching vs. Lexical keyword matching).
- **Implementation Details:**
- Implements `SemanticMatcher` to manage text comparison workflows.
- Pre-filters a large candidate corpus down to a manageable pool using fast lexical keyword overlap before executing costly dense vector comparisons.
- Features an automated resilience fallback: if external or local embedding services encounter errors, the system gracefully degrades to keyword-based matching.

**Searchable References & Code Snippets:**

- Core matcher class and routing:

```python
class SemanticMatcher:
    async def match(self, submission: Submission, problems: list[dict[str, Any]], use_ai: bool) -> MatchOutcome:
        pool = self._select_pool(submission, problems)
        if not use_ai:
            return self._keyword_match(submission, pool)
        try:
            return await self._embedding_match(submission, allowed)
        except AIProviderError as error:
            outcome = self._keyword_match(submission, pool)
            outcome.ai_error = error
            return outcome

```

---

### 4. Persistent Vector Caching & Version Control

- **File Location:** `ml/nlp/embedding_cache.py`
- **NLP Theory:** Hash-based memoization for high-dimensional vector representations to avoid redundant model inference computations.
- **Implementation Details:**
- Implements `EmbeddingCache` to store computed sentence vectors on disk as atomic JSON payloads.
- Incorporates model identifiers and text preparation version tags (`TEXT_PREP_VERSION`) into cryptographic hashes (`SHA-256`) to automatically invalidate stale caches whenever models or preprocessing rules change.

**Searchable References & Code Snippets:**

- Cache key generation and lookup:

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

- **File Location:** `ml/nlp/srs.py`
- **NLP Theory:** Retrieval-Augmented Generation (RAG), structured prompt templating, and automated output validation against engineering standards.
- **Implementation Details:**
- Uses `SrsGenerator` to encapsulate problem metadata, descriptions, constraints, and crowdsourced community reports into standardized XML-delimited prompt structures (`<problem>`).
- Enforces compliance checks against structured sections (ISO/IEC/IEEE 29148 requirements) to parse, clean, and validate generated technical specifications.

**Searchable References & Code Snippets:**

- Context building and document review:

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

- **File Location:** `ml/nlp/training_data.py`
- **NLP Theory:** Supervised dataset assembly, feature vector serialization, and human-in-the-loop feedback aggregation for semantic classifier calibration.
- **Implementation Details:**
- Maps annotated problem pairs into structured training rows containing multi-dimensional feature dictionaries (cosine similarity, absolute difference summaries, and element-wise products).
- Aggregates runtime user feedback to expand training datasets dynamically.

**Searchable References & Code Snippets:**

- Training row builder:

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
