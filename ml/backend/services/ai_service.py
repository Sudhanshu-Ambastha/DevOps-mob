import httpx

NLP_SERVICE_URL = "http://127.0.0.1:8001"  # Your NLP worker running on port 8001

async def analyze_problem_text(existing_desc: str, new_desc: str) -> float:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NLP_SERVICE_URL}/api/nlp/similarity",
                json={"text_a": existing_desc, "text_b": new_desc},
                timeout=10.0
            )
            return response.json().get("similarity_score", 0.0)
        except Exception:
            return 0.0

async def create_srs_spec(description: str) -> str:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NLP_SERVICE_URL}/api/nlp/generate-srs",
                json={"raw_description": description},
                timeout=30.0
            )
            return response.json().get("srs_specification", "SRS Generation Failed")
        except Exception:
            return "Error connecting to local NLP worker."