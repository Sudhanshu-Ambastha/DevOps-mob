import torch
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

class AICoreEngine:
    def __init__(self):
        print("Initializing NLP Engine (Offline Mode Enabled)...")
        self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
        
        self.srs_model_id = "Qwen/Qwen2.5-3B-Instruct"
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.srs_model_id, 
            local_files_only=True
        )
        self.srs_llm = AutoModelForCausalLM.from_pretrained(
            self.srs_model_id,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            local_files_only=True
        )

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        embedding_a = self.similarity_model.encode(text_a, convert_to_tensor=True)
        embedding_b = self.similarity_model.encode(text_b, convert_to_tensor=True)
        score = util.cos_sim(embedding_a, embedding_b)
        return float(score.item())

    def generate_srs(self, raw_description: str) -> str:
        system_prompt = (
            "You are an expert Software Architect. Convert the user's raw problem "
            "description into a structured Software Requirement Specification (SRS) in Markdown format. "
            "Include these exact headings: ### 1. Objective, ### 2. Functional Requirements, and ### 3. Scope."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Problem description: {raw_description}"}
        ]
        
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.srs_llm.device)
        
        generated_ids = self.srs_llm.generate(
            **model_inputs,
            max_new_tokens=400,
            temperature=0.3,
            do_sample=True
        )
        
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        return self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]