# Deep Learning (DL) Technical Specification & Implementation Report

This document outlines the core Deep Learning (DL), neural embedding, and transformer-based architectures implemented across the project. It details the neural model loading, high-dimensional vector space operations, neural language model (LLM) inference, and inference guardrails, complete with searchable class and function references for code auditability.

---

### 1. Transformer Encoder Architecture & Dense Embeddings

- **File Location:** `ml/nlp/providers/local.py`
- **Deep Learning Theory:** Transformer-based encoder architectures (specifically Siamese/Triplet BERT-style sentence transformers) designed to map variable-length natural language text into dense, continuous vector spaces.
- **Implementation Details:**
- Loads pre-trained transformer model weights (`paraphrase-MiniLM-L6-v2`) directly from disk using the `SentenceTransformer` library.
- Executes asynchronous forward-pass inference (`model.encode`) via thread pools (`asyncio.to_thread`) to convert raw text tokens into 384-dimensional dense floating-point embeddings.

**Searchable References & Code Snippets:**

- Local Transformer model loading and encoding:

```python
class LocalEmbeddingProvider:
    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_path)
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        embeddings = await asyncio.to_thread(
            lambda: model.encode(texts, convert_to_numpy=True).tolist()
        )
        return embeddings

```

---

### 2. High-Dimensional Vector Space Math & L2 Norms

- **File Location:** `ml/nlp/features.py`
- **Deep Learning Theory:** Linear algebra operations on high-dimensional tensor representations, including vector magnitude (L2 norm) calculation and dot-product similarity.
- **Implementation Details:**
- Computes the geometric properties of dense vector spaces using optimized NumPy linear algebra routines (`np.linalg.norm`, `np.dot`).
- Generates element-wise absolute difference summaries and Hadamard products (element-wise products) between embedding vectors to capture multi-dimensional tensor interactions.

**Searchable References & Code Snippets:**

- L2 norm and vector dot product for cosine similarity:

```python
def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator == 0.0:
        return 0.0
    return float(np.dot(left, right) / denominator)

```

- Embedding tensor difference summary:

```python
def embedding_difference_summary(left: np.ndarray, right: np.ndarray) -> dict[str, float]:
    difference = np.abs(left - right)
    return {
        "mean": float(difference.mean()),
        "std": float(difference.std()),
        "max": float(difference.max()),
        "l2": float(np.linalg.norm(difference))
    }
```

---

### 3. Neural Language Model (LLM) Generative Inference

- **File Location:** `ml/nlp/providers/openrouter.py` & `ml/nlp/srs.py`
- **Deep Learning Theory:** Autoregressive transformer decoders, system/user prompt conditioning, temperature sampling, and structured output parsing.
- **Implementation Details:**
- Interfaces with neural generative models via OpenRouter chat completion APIs.
- Configures inference parameters such as temperature control (`srs_temperature`) for deterministic generation and token bounds (`srs_max_output_tokens`).
- Cleans and filters model outputs (stripping chain-of-thought `<think>` tokens and Markdown code fences) to ensure structured technical document generation.

**Searchable References & Code Snippets:**

- Generative payload construction and LLM client call:

```python
async def _post_completion(self, client: httpx.AsyncClient, system_prompt: str, user_prompt: str) -> httpx.Response:
    body = {
        "model": self.model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": self.temperature,
        "max_tokens": self.max_output_tokens,
        "usage": {"include": True}
    }
    return await client.post(f"{API_BASE}/chat/completions", json=body)
```

---

### 4. Vector Memoization & Embedding Cache Persistence

- **File Location:** `ml/nlp/embedding_cache.py`
- **Deep Learning Theory:** Neural inference memoization, cryptographic hashing for state validation, and quantization precision rounding.
- **Implementation Details:**
- Implements `EmbeddingCache` to store computed neural embeddings on disk, avoiding expensive redundant model forward passes.
- Rounds vector floating-point values to fixed precision (`VECTOR_DECIMALS = 7`) to optimize storage while preserving spatial representation accuracy.

**Searchable References & Code Snippets:**

- Vector rounding and caching:

```python
class EmbeddingCache:
    def put_many(self, items: dict[str, list[float]]) -> None:
        with self._lock:
            for text, vector in items.items():
                self._entries[self.key_for(text)] = [round(value, VECTOR_DECIMALS) for value in vector]
            self._save()
```

---

### 5. Neural Inference Guardrails & Token Budgeting

- **File Location:** `ml/nlp/usage_guard.py` & `ml/nlp/providers/cloudflare.py`
- **Deep Learning Theory:** Token-to-neuron estimation heuristics, inference rate-limiting, and quota management for deep learning cloud APIs.
- **Implementation Details:**
- Calculates estimated token counts and neural execution costs (`estimate_neurons`) based on input character length before dispatching network requests.
- Enforces daily usage budgets and cool-down states to prevent API quota exhaustion.

**Searchable References & Code Snippets:**

- Neuron estimation heuristic:

```python
ESTIMATED_CHARS_PER_TOKEN = 3
NEURONS_PER_TOKEN = 1075 / 1_000_000

def estimate_neurons(texts: list[str]) -> float:
    characters = sum(len(text) for text in texts)
    return (characters / ESTIMATED_CHARS_PER_TOKEN) * NEURONS_PER_TOKEN
```
