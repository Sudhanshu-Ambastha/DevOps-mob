import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
NLP_ROOT = CURRENT_DIR.parent
sys.path.append(str(NLP_ROOT))

import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from text import normalize_text, tokenize, extract_keywords, build_embedding_text
from features import keyword_overlap, cosine_similarity, compute_pair_features

def run_pipeline_test():
    raw_text = "I need a Dark Mode Toggle for the Dashboard!"
    norm = normalize_text(raw_text)
    tokens = tokenize(raw_text)
    keywords = extract_keywords(raw_text)
    
    print("[1] Text Preprocessing, Tokenization & Stemming:")
    print(f"Raw Input:  '{raw_text}'")
    print(f"Normalized: '{norm}'")
    print(f"Tokens:     {tokens}")
    print(f"Keywords:   {keywords}\n")
    
    text_a = "Add a dark mode toggle in settings"
    text_b = "I need a dark theme option for the dashboard"
    overlap = keyword_overlap(text_a, text_b)
    
    print("[2] Lexical Keyword Overlap (Jaccard Set Metric):")
    print(f"Comparing: '{text_a}'")
    print(f"And:       '{text_b}'")
    print(f"Jaccard Overlap Score: {overlap:.4f}\n")
    
    env_path = CURRENT_DIR / ".env"
    load_dotenv(dotenv_path=env_path)
    
    model_path = os.getenv("MODEL_PATH") or r"H:\My Drive\Dev_Bridge\models\paraphrase-MiniLM-L6-v2"
    print(f"[3] Loading Local Deep Learning Model...")
    print(f"Model Path: {model_path}")
    
    if not Path(model_path).exists():
        print(f"ERROR: Model path does not exist on disk! Check your MODEL_PATH.")
        return
        
    model = SentenceTransformer(model_path)
    print("Transformer Model loaded successfully into memory!\n")
    
    sentences = [
        text_a,
        text_b,
        "Send me an email notification when a developer accepts a prompt."
    ]
    
    print("[4] Generating Dense Embeddings & Computing Cosine Similarity:")
    embeddings = model.encode(sentences, convert_to_numpy=True)
    
    sim_0_1 = cosine_similarity(embeddings[0], embeddings[1])
    sim_0_2 = cosine_similarity(embeddings[0], embeddings[2])
    
    print(f"Sentence 1 vs 2 (Semantic Match):  {sim_0_1:.4f} 🔥")
    print(f"Sentence 1 vs 3 (Unrelated Match): {sim_0_2:.4f} ❄️\n")
    
    print("🗺️ [5] Computing Full Pairwise Feature Engineering Map:")
    features = compute_pair_features(
        left_title="Dark Mode Feature",
        left_text=text_a,
        left_tags=["ui", "dashboard"],
        right_title="Night Theme Option",
        right_text=text_b,
        right_tags=["ui", "settings"],
        left_vector=embeddings[0],
        right_vector=embeddings[1]
    )
    
    for key, val in features.items():
        print(f"{key}: {val}")

if __name__ == "__main__":
    run_pipeline_test()